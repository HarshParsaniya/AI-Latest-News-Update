from __future__ import annotations

import argparse
import json
import logging
import os
import sys

from dotenv import load_dotenv

load_dotenv()

from app.graph import build_graph
from app.llm import get_langfuse_handler
from app.settings import get_settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch latest AI news and send a digest.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Fetch, summarize, and print bodies without sending email or WhatsApp.",
    )
    return parser.parse_args(argv)


def run(dry_run: bool = False) -> dict:
    get_settings.cache_clear()
    settings = get_settings()
    if dry_run:
        os.environ["DRY_RUN"] = "true"
        get_settings.cache_clear()
        settings = get_settings()

    graph = build_graph()
    callbacks = []
    handler = get_langfuse_handler(settings)
    if handler is not None:
        callbacks.append(handler)

    config = {"callbacks": callbacks} if callbacks else {}
    result = graph.invoke({"dry_run": dry_run or settings.dry_run, "errors": []}, config=config)

    if handler is not None:
        try:
            from langfuse import Langfuse

            Langfuse().flush()
        except Exception:  # noqa: BLE001
            pass

    return result


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    args = parse_args(argv)
    result = run(dry_run=args.dry_run)
    status = result.get("delivery_status") or {}
    summary = {
        "item_count": len(result.get("summaries") or []),
        "email": status.get("email"),
        "whatsapp": status.get("whatsapp"),
        "ok": result.get("ok"),
        "errors": result.get("errors") or [],
    }
    print(json.dumps(summary, indent=2))
    if args.dry_run or get_settings().dry_run:
        print("\n--- EMAIL SUBJECT ---\n", result.get("email_subject") or "")
        print("\n--- EMAIL TEXT ---\n", result.get("email_text") or "")
        print("\n--- WHATSAPP ---\n", result.get("whatsapp_text") or "")
    return 0 if result.get("ok", True) else 1


if __name__ == "__main__":
    sys.exit(main())
