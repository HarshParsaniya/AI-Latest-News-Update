from __future__ import annotations

import hashlib
import logging
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from email.utils import parsedate_to_datetime
from html import unescape

import feedparser
import httpx

from app.settings import get_settings
from app.sources import SOURCES
from app.state import DigestState, NewsItem
from app.urls import canonicalize_url

logger = logging.getLogger(__name__)

USER_AGENT = "AINewsDigest/0.1 (+https://github.com/local/ai-news-digest)"
MAX_ENTRIES_PER_FEED = 40
TAG_RE = re.compile(r"<[^>]+>")


def strip_html(text: str) -> str:
    cleaned = unescape(TAG_RE.sub(" ", text or ""))
    return " ".join(cleaned.split())


def _item_id(url: str, title: str) -> str:
    return hashlib.sha256(f"{url}|{title}".encode()).hexdigest()[:16]


def _published_iso(entry) -> str:
    for key in ("published", "updated"):
        raw = entry.get(key)
        if not raw:
            continue
        try:
            return parsedate_to_datetime(raw).isoformat()
        except (TypeError, ValueError, OverflowError):
            return str(raw)
    if entry.get("published_parsed"):
        try:
            from datetime import datetime, timezone
            from time import mktime

            return datetime.fromtimestamp(
                mktime(entry.published_parsed), tz=timezone.utc
            ).isoformat()
        except (OverflowError, ValueError, OSError):
            pass
    return ""


def _snippet(entry) -> str:
    summary = entry.get("summary") or entry.get("description") or ""
    return strip_html(str(summary))[:1200]


def _extract_text(url: str) -> str:
    try:
        import trafilatura

        downloaded = trafilatura.fetch_url(url)
        if not downloaded:
            return ""
        return (trafilatura.extract(downloaded) or "")[:4000]
    except Exception as exc:  # noqa: BLE001
        logger.debug("Article extract failed for %s: %s", url, exc)
        return ""


def _parse_feed(source_name: str, xml: str, extract: bool) -> list[NewsItem]:
    parsed = feedparser.parse(xml)
    items: list[NewsItem] = []
    for entry in parsed.entries[:MAX_ENTRIES_PER_FEED]:
        title = strip_html(entry.get("title") or "").strip()
        link = (entry.get("link") or "").strip()
        if not title or not link:
            continue
        url = canonicalize_url(link)
        snippet = _snippet(entry)
        if extract and url:
            body = _extract_text(url)
            if body:
                snippet = body
        items.append(
            NewsItem(
                id=_item_id(url, title),
                title=title,
                url=url,
                source=source_name,
                published=_published_iso(entry),
                snippet=snippet,
            )
        )
    return items


def _fetch_one(source: dict, extract: bool) -> tuple[str, list[NewsItem], str | None]:
    try:
        with httpx.Client(timeout=20.0, follow_redirects=True, headers={"User-Agent": USER_AGENT}) as client:
            response = client.get(source["url"])
            response.raise_for_status()
        return source["name"], _parse_feed(source["name"], response.text, extract), None
    except Exception as exc:  # noqa: BLE001
        return source["name"], [], str(exc)


def fetch_sources(state: DigestState) -> DigestState:
    settings = get_settings()
    errors = list(state.get("errors") or [])
    raw: list[NewsItem] = []
    with ThreadPoolExecutor(max_workers=6) as pool:
        futures = [
            pool.submit(_fetch_one, source, settings.extract_article_text)
            for source in SOURCES
        ]
        for future in as_completed(futures):
            name, items, error = future.result()
            if error:
                logger.warning("Source %s failed: %s", name, error)
                errors.append(f"fetch:{name}: {error}")
            else:
                logger.info("Fetched %s items from %s", len(items), name)
                raw.extend(items)
    return {"raw_items": raw, "errors": errors}
