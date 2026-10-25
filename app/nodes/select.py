from __future__ import annotations

import logging
from datetime import datetime
from difflib import SequenceMatcher

from app.settings import get_settings
from app.state import DigestState, NewsItem
from app.store import sent_urls

logger = logging.getLogger(__name__)

SIMILARITY_THRESHOLD = 0.85


def _parse_dt(value: str) -> datetime:
    if not value:
        return datetime.min
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        return datetime.min


def _near_duplicate(title: str, seen_titles: list[str]) -> bool:
    lowered = title.casefold()
    for other in seen_titles:
        if SequenceMatcher(None, lowered, other.casefold()).ratio() >= SIMILARITY_THRESHOLD:
            return True
    return False


def normalize_and_dedup(state: DigestState) -> DigestState:
    already = sent_urls()
    errors = list(state.get("errors") or [])
    unique: dict[str, NewsItem] = {}
    for item in state.get("raw_items") or []:
        url = item.get("url") or ""
        title = (item.get("title") or "").strip()
        if not url or not title:
            continue
        if url in already:
            continue
        previous = unique.get(url)
        if previous is None or _parse_dt(item.get("published") or "") > _parse_dt(
            previous.get("published") or ""
        ):
            unique[url] = item
    candidates = list(unique.values())
    logger.info("Normalized to %s candidates (%s already sent skipped)", len(candidates), len(already))
    return {"candidates": candidates, "errors": errors}


def select_latest(state: DigestState) -> DigestState:
    settings = get_settings()
    ranked = sorted(
        state.get("candidates") or [],
        key=lambda item: _parse_dt(item.get("published") or ""),
        reverse=True,
    )
    selected: list[NewsItem] = []
    seen_titles: list[str] = []
    for item in ranked:
        title = item.get("title") or ""
        if _near_duplicate(title, seen_titles):
            continue
        selected.append(item)
        seen_titles.append(title)
        if len(selected) >= settings.target_item_count:
            break
    logger.info("Selected %s items", len(selected))
    return {"selected": selected}
