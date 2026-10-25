from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from app.settings import get_settings


SCHEMA = """
CREATE TABLE IF NOT EXISTS sent_items (
    url TEXT PRIMARY KEY,
    title TEXT,
    sent_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at TEXT NOT NULL,
    item_count INTEGER,
    email_status TEXT,
    whatsapp_status TEXT
);
"""


def _connect(path: Path | None = None) -> sqlite3.Connection:
    db_path = path or get_settings().sqlite_path
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.executescript(SCHEMA)
    return conn


def sent_urls(path: Path | None = None) -> set[str]:
    with _connect(path) as conn:
        rows = conn.execute("SELECT url FROM sent_items").fetchall()
    return {row[0] for row in rows}


def record_sent(items: list[dict], path: Path | None = None) -> None:
    now = datetime.now(timezone.utc).isoformat()
    with _connect(path) as conn:
        conn.executemany(
            "INSERT OR IGNORE INTO sent_items (url, title, sent_at) VALUES (?, ?, ?)",
            [(item["url"], item.get("title", ""), now) for item in items if item.get("url")],
        )
        conn.commit()


def record_run(
    item_count: int,
    email_status: str,
    whatsapp_status: str,
    path: Path | None = None,
) -> None:
    now = datetime.now(timezone.utc).isoformat()
    with _connect(path) as conn:
        conn.execute(
            "INSERT INTO runs (started_at, item_count, email_status, whatsapp_status) "
            "VALUES (?, ?, ?, ?)",
            (now, item_count, email_status, whatsapp_status),
        )
        conn.commit()
