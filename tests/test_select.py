from app.nodes.select import normalize_and_dedup, select_latest
from app.settings import get_settings


def test_normalize_skips_sent_and_duplicate_urls(monkeypatch):
    monkeypatch.setattr(
        "app.nodes.select.sent_urls",
        lambda: {"https://example.com/old"},
    )
    state = {
        "raw_items": [
            {
                "id": "1",
                "title": "Old story",
                "url": "https://example.com/old",
                "published": "2026-10-25T08:00:00+00:00",
            },
            {
                "id": "2",
                "title": "Newer copy",
                "url": "https://example.com/new",
                "published": "2026-10-25T10:00:00+00:00",
            },
            {
                "id": "3",
                "title": "Older copy",
                "url": "https://example.com/new",
                "published": "2026-10-25T09:00:00+00:00",
            },
        ],
        "errors": [],
    }
    result = normalize_and_dedup(state)
    urls = [item["url"] for item in result["candidates"]]
    assert urls == ["https://example.com/new"]
    assert result["candidates"][0]["title"] == "Newer copy"


def test_select_latest_ranks_and_drops_near_duplicates(monkeypatch):
    get_settings.cache_clear()
    monkeypatch.setenv("TARGET_ITEM_COUNT", "10")
    get_settings.cache_clear()
    state = {
        "candidates": [
            {
                "id": "a",
                "title": "OpenAI releases a new model",
                "url": "https://a.example/1",
                "published": "2026-10-24T10:00:00+00:00",
            },
            {
                "id": "b",
                "title": "OpenAI releases a new model!",
                "url": "https://b.example/1",
                "published": "2026-10-25T12:00:00+00:00",
            },
            {
                "id": "c",
                "title": "DeepMind publishes robotics paper",
                "url": "https://c.example/1",
                "published": "2026-10-25T11:00:00+00:00",
            },
        ]
    }
    selected = select_latest(state)["selected"]
    titles = [item["title"] for item in selected]
    assert titles[0].startswith("OpenAI releases")
    assert "DeepMind publishes robotics paper" in titles
    assert len(selected) == 2
