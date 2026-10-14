from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB_PATH = PROJECT_ROOT / "data" / "shopscribe_history.sqlite3"


def _connect(db_path: str | Path = DEFAULT_DB_PATH) -> sqlite3.Connection:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS content_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            product_name TEXT NOT NULL,
            language TEXT NOT NULL,
            model TEXT NOT NULL,
            content_json TEXT NOT NULL
        )
        """
    )
    connection.commit()
    return connection


def save_history(
    product_name: str,
    language: str,
    model: str,
    content_json: str,
    db_path: str | Path = DEFAULT_DB_PATH,
) -> int:
    timestamp = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    with _connect(db_path) as connection:
        cursor = connection.execute(
            "INSERT INTO content_history (created_at, product_name, language, model, content_json) VALUES (?, ?, ?, ?, ?)",
            (timestamp, product_name, language, model, content_json),
        )
        return int(cursor.lastrowid)


def get_recent_history(limit: int = 10, db_path: str | Path = DEFAULT_DB_PATH) -> list[dict[str, str | int]]:
    if limit < 1:
        raise ValueError("limit must be at least 1")
    with _connect(db_path) as connection:
        rows = connection.execute(
            "SELECT id, created_at, product_name, language, model, content_json FROM content_history ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]
