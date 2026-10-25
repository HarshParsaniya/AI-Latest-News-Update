from __future__ import annotations

import logging

from app.settings import get_settings
from app.state import DigestState
from app.store import record_run, record_sent

logger = logging.getLogger(__name__)


def persist_sent(state: DigestState) -> DigestState:
    settings = get_settings()
    status = dict(state.get("delivery_status") or {})
    items = list(state.get("summaries") or [])
    email_status = status.get("email", "unknown")
    whatsapp_status = status.get("whatsapp", "unknown")
    dry = settings.dry_run or state.get("dry_run")

    if dry:
        record_run(len(items), email_status, whatsapp_status)
        return {"ok": True, "delivery_status": status}

    if email_status == "sent":
        record_sent(items)
        logger.info("Recorded %s sent URLs", len(items))
    else:
        logger.warning("Not recording sent URLs because email status is %s", email_status)

    record_run(len(items), email_status, whatsapp_status)
    ok = email_status in {"sent", "skipped_empty"}
    return {"ok": ok, "delivery_status": status}
