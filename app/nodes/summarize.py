from __future__ import annotations

import json
import logging
import re

from langchain_core.messages import HumanMessage, SystemMessage

from app.llm import get_chat_model
from app.state import DigestState, NewsItem

logger = logging.getLogger(__name__)

SYSTEM = (
    "You summarize AI news for a daily digest. "
    "Return ONLY valid JSON: an array of objects with keys id, summary, blurb. "
    "summary is 3-5 sentences. blurb is one short WhatsApp line under 140 characters. "
    "Do not invent facts. Do not include URLs in summary or blurb."
)


def _fallback(item: NewsItem) -> NewsItem:
    snippet = (item.get("snippet") or item.get("title") or "").strip()
    summary = snippet[:600] or item.get("title", "")
    blurb = snippet[:137] + "..." if len(snippet) > 140 else snippet
    return {**item, "summary": summary, "blurb": blurb or item.get("title", "")}


def _parse_json(text: str) -> list[dict]:
    text = text.strip()
    match = re.search(r"\[.*\]", text, re.DOTALL)
    if match:
        text = match.group(0)
    data = json.loads(text)
    if not isinstance(data, list):
        raise ValueError("LLM did not return a JSON array")
    return data


def summarize_items(state: DigestState) -> DigestState:
    selected = list(state.get("selected") or [])
    errors = list(state.get("errors") or [])
    if not selected:
        return {"summaries": [], "errors": errors}

    model = get_chat_model()
    if model is None:
        return {"summaries": [_fallback(item) for item in selected], "errors": errors}

    payload = [
        {
            "id": item["id"],
            "title": item.get("title"),
            "source": item.get("source"),
            "snippet": (item.get("snippet") or "")[:1500],
        }
        for item in selected
    ]
    try:
        response = model.invoke(
            [
                SystemMessage(content=SYSTEM),
                HumanMessage(content=json.dumps(payload, ensure_ascii=False)),
            ]
        )
        content = response.content
        if isinstance(content, list):
            content = "".join(
                part.get("text", "") if isinstance(part, dict) else str(part) for part in content
            )
        parsed = {row["id"]: row for row in _parse_json(str(content)) if "id" in row}
        summaries: list[NewsItem] = []
        for item in selected:
            row = parsed.get(item["id"])
            if not row:
                summaries.append(_fallback(item))
                continue
            summaries.append(
                {
                    **item,
                    "summary": str(row.get("summary") or item.get("snippet") or item.get("title")),
                    "blurb": str(row.get("blurb") or item.get("title")),
                }
            )
        return {"summaries": summaries, "errors": errors}
    except Exception as exc:  # noqa: BLE001
        logger.warning("Summarization failed, using snippets: %s", exc)
        errors.append(f"summarize: {exc}")
        return {"summaries": [_fallback(item) for item in selected], "errors": errors}
