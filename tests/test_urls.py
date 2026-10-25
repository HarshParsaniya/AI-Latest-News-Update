from app.urls import canonicalize_url, unwrap_google_news


def test_unwrap_google_news_url_param():
    raw = "https://news.google.com/rss/articles/abc?url=https://example.com/ai-story&hl=en"
    assert unwrap_google_news(raw) == "https://example.com/ai-story"


def test_canonicalize_strips_utm_and_www():
    url = "https://www.Example.com/path/article/?utm_source=x&id=1"
    assert canonicalize_url(url) == "https://example.com/path/article?id=1"
