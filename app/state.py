from typing import Any, TypedDict


class NewsItem(TypedDict, total=False):
    id: str
    title: str
    url: str
    source: str
    published: str
    snippet: str
    summary: str
    blurb: str


class DigestState(TypedDict, total=False):
    raw_items: list[NewsItem]
    candidates: list[NewsItem]
    selected: list[NewsItem]
    summaries: list[NewsItem]
    email_subject: str
    email_html: str
    email_text: str
    whatsapp_text: str
    delivery_status: dict[str, Any]
    errors: list[str]
    dry_run: bool
    ok: bool
