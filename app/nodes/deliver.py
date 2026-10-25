from __future__ import annotations

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from urllib.parse import quote

import httpx

from app.settings import get_settings
from app.state import DigestState

logger = logging.getLogger(__name__)

CALLMEBOT_URL = "https://api.callmebot.com/whatsapp.php"


def send_email_message(subject: str, html_body: str, text_body: str) -> str:
    settings = get_settings()
    if not settings.smtp_ready:
        raise RuntimeError("SMTP is not configured (need SMTP_USER, SMTP_APP_PASSWORD, DIGEST_TO_EMAIL)")

    sender = settings.from_address
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = ", ".join(settings.email_recipients)
    msg.attach(MIMEText(text_body, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=30) as server:
        server.starttls()
        server.login(settings.smtp_user, settings.smtp_app_password)
        server.sendmail(sender, settings.email_recipients, msg.as_string())
    return "sent"


def send_whatsapp_message(text: str) -> str:
    settings = get_settings()
    if not settings.whatsapp_ready:
        return "skipped_disabled"
    url = (
        f"{CALLMEBOT_URL}?phone={quote(settings.callmebot_phone)}"
        f"&apikey={quote(settings.callmebot_apikey)}"
        f"&text={quote(text)}"
    )
    try:
        with httpx.Client(timeout=30.0, follow_redirects=True) as client:
            response = client.get(url)
        if response.status_code >= 400:
            logger.warning("WhatsApp skipped: HTTP %s %s", response.status_code, response.text[:200])
            return f"skipped_http_{response.status_code}"
        return "sent"
    except Exception as exc:  # noqa: BLE001
        logger.warning("WhatsApp skipped: %s", exc)
        return f"skipped_error:{exc}"


def send_email(state: DigestState) -> DigestState:
    status = dict(state.get("delivery_status") or {})
    errors = list(state.get("errors") or [])
    settings = get_settings()
    items = state.get("summaries") or []
    if settings.dry_run or state.get("dry_run"):
        status["email"] = "dry_run"
        return {"delivery_status": status, "errors": errors}
    if not items:
        status["email"] = "skipped_empty"
        return {"delivery_status": status, "errors": errors}
    try:
        status["email"] = send_email_message(
            state.get("email_subject") or "AI Daily Digest",
            state.get("email_html") or "",
            state.get("email_text") or "",
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("Email send failed")
        status["email"] = "failed"
        errors.append(f"email: {exc}")
    return {"delivery_status": status, "errors": errors}


def send_whatsapp(state: DigestState) -> DigestState:
    status = dict(state.get("delivery_status") or {})
    errors = list(state.get("errors") or [])
    settings = get_settings()
    if settings.dry_run or state.get("dry_run"):
        status["whatsapp"] = "dry_run"
        return {"delivery_status": status, "errors": errors}
    if not (state.get("summaries") or []):
        status["whatsapp"] = "skipped_empty"
        return {"delivery_status": status, "errors": errors}
    result = send_whatsapp_message(state.get("whatsapp_text") or "")
    status["whatsapp"] = result
    if result.startswith("skipped_http") or result.startswith("skipped_error"):
        errors.append(f"whatsapp: {result}")
    return {"delivery_status": status, "errors": errors}
