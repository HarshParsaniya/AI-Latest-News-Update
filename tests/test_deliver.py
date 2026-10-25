from app.nodes.deliver import send_email, send_whatsapp, send_whatsapp_message
from app.settings import get_settings


def test_whatsapp_http_error_is_skipped(monkeypatch):
    class FakeResponse:
        status_code = 500
        text = "unavailable"

    class FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def get(self, url):
            return FakeResponse()

    monkeypatch.setenv("WHATSAPP_ENABLED", "true")
    monkeypatch.setenv("CALLMEBOT_PHONE", "+15555550100")
    monkeypatch.setenv("CALLMEBOT_APIKEY", "test-key")
    get_settings.cache_clear()
    monkeypatch.setattr("app.nodes.deliver.httpx.Client", FakeClient)

    status = send_whatsapp_message("hello")
    assert status.startswith("skipped_http_500")
    get_settings.cache_clear()


def test_whatsapp_node_does_not_fail_job(monkeypatch):
    monkeypatch.setenv("DRY_RUN", "false")
    get_settings.cache_clear()
    monkeypatch.setattr(
        "app.nodes.deliver.send_whatsapp_message",
        lambda text: "skipped_http_429",
    )
    result = send_whatsapp(
        {
            "summaries": [{"url": "https://example.com/a", "title": "A"}],
            "whatsapp_text": "digest",
            "delivery_status": {"email": "sent"},
            "errors": [],
        }
    )
    assert result["delivery_status"]["email"] == "sent"
    assert result["delivery_status"]["whatsapp"].startswith("skipped_http")
    get_settings.cache_clear()


def test_email_dry_run_skips_smtp(monkeypatch):
    monkeypatch.setenv("DRY_RUN", "true")
    get_settings.cache_clear()
    result = send_email(
        {
            "summaries": [{"url": "https://example.com/a"}],
            "email_subject": "s",
            "email_html": "<p>x</p>",
            "email_text": "x",
            "delivery_status": {},
            "errors": [],
        }
    )
    assert result["delivery_status"]["email"] == "dry_run"
    get_settings.cache_clear()
