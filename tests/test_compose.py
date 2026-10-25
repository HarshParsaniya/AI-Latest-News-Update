from app.nodes.compose import compose_digest, render_email_html
from app.settings import get_settings


def _items():
    return [
        {
            "id": "1",
            "title": "Gemini update",
            "source": "TechCrunch AI",
            "published": "2026-10-25T08:00:00+00:00",
            "summary": "Google shipped a Gemini update for developers.",
            "blurb": "Gemini update lands for developers.",
            "url": "https://example.com/gemini",
        },
        {
            "id": "2",
            "title": "Open model drop",
            "source": "Hugging Face Blog",
            "published": "2026-10-25T07:00:00+00:00",
            "summary": "A new open-weight model is on Hugging Face.",
            "blurb": "New open-weight model released.",
            "url": "https://example.com/open-model",
        },
    ]


def test_email_puts_link_after_summary():
    html = render_email_html(_items(), "2026-10-25")
    summary_at = html.find("Google shipped a Gemini update")
    link_at = html.find("https://example.com/gemini")
    assert summary_at != -1 and link_at != -1
    assert summary_at < link_at


def test_compose_whatsapp_link_after_blurb(monkeypatch):
    monkeypatch.setenv("CALLMEBOT_MAX_CHARS", "1500")
    get_settings.cache_clear()
    result = compose_digest({"summaries": _items()})
    text = result["whatsapp_text"]
    blob = text.split("1. Gemini update")[1]
    blurb_at = blob.find("Gemini update lands for developers.")
    url_at = blob.find("https://example.com/gemini")
    assert blurb_at != -1 and url_at != -1
    assert blurb_at < url_at
    assert "Full digest is in email." in text
    assert result["email_subject"].startswith("AI Daily Digest —")
    get_settings.cache_clear()


def test_whatsapp_keeps_links_when_truncating(monkeypatch):
    monkeypatch.setenv("CALLMEBOT_MAX_CHARS", "280")
    get_settings.cache_clear()
    long_items = []
    for i in range(8):
        long_items.append(
            {
                "id": str(i),
                "title": f"Very long artificial intelligence headline number {i} for the digest",
                "blurb": "This blurb is intentionally lengthy so the WhatsApp payload overflows.",
                "summary": "Summary text.",
                "url": f"https://example.com/story-{i}",
                "source": "Test",
                "published": "2026-10-25T08:00:00+00:00",
            }
        )
    result = compose_digest({"summaries": long_items})
    text = result["whatsapp_text"]
    assert "https://example.com/story-0" in text
    assert text.count("https://example.com/story-") >= 1
    lines = [line for line in text.splitlines() if line.strip()]
    for index, line in enumerate(lines):
        if line[:2].rstrip(".").isdigit() or (len(line) > 2 and line[0].isdigit() and line[1] == "."):
            assert lines[index + 1].startswith("https://")
    get_settings.cache_clear()
