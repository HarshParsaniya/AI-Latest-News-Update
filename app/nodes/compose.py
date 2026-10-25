from __future__ import annotations

from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.settings import get_settings
from app.state import DigestState, NewsItem

TEMPLATE_DIR = Path(__file__).resolve().parents[2] / "templates"


def _now_label() -> str:
    settings = get_settings()
    try:
        tz = ZoneInfo(settings.digest_tz)
    except Exception:  # noqa: BLE001
        tz = ZoneInfo("UTC")
    return datetime.now(tz).strftime("%Y-%m-%d")


def _plain_email(items: list[NewsItem], date_label: str) -> str:
    lines = [f"AI Daily Digest — {date_label} ({len(items)} updates)", ""]
    for index, item in enumerate(items, start=1):
        lines.extend(
            [
                f"{index}. {item.get('title', '')}",
                f"{item.get('source', '')} · {item.get('published', '')}",
                item.get("summary") or "",
                item.get("url") or "",
                "",
            ]
        )
    return "\n".join(lines).strip() + "\n"


def _whatsapp(items: list[NewsItem], date_label: str, max_chars: int) -> str:
    footer = "\nFull digest is in email."
    included: list[NewsItem] = []
    for item in items:
        trial = included + [item]
        body = _whatsapp_body(trial, date_label) + footer
        if len(body) > max_chars and included:
            break
        included.append(item)
        if len(body) > max_chars:
            break
    if not included and items:
        included = items[:1]
    return _whatsapp_body(included, date_label) + footer


def _whatsapp_body(items: list[NewsItem], date_label: str) -> str:
    lines = [f"AI Daily Digest — {date_label} ({len(items)} updates)", ""]
    for index, item in enumerate(items, start=1):
        title = item.get("title") or ""
        blurb = item.get("blurb") or ""
        url = item.get("url") or ""
        lines.append(f"{index}. {title} — {blurb}")
        lines.append(url)
        lines.append("")
    return "\n".join(lines).rstrip()


def render_email_html(items: list[NewsItem], date_label: str) -> str:
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        autoescape=select_autoescape(["html"]),
    )
    template = env.get_template("digest.html")
    return template.render(items=items, date_label=date_label, count=len(items))


def compose_digest(state: DigestState) -> DigestState:
    settings = get_settings()
    items = list(state.get("summaries") or [])
    date_label = _now_label()
    subject = f"AI Daily Digest — {date_label} ({len(items)} updates)"
    return {
        "email_subject": subject,
        "email_html": render_email_html(items, date_label),
        "email_text": _plain_email(items, date_label),
        "whatsapp_text": _whatsapp(items, date_label, settings.callmebot_max_chars),
    }
