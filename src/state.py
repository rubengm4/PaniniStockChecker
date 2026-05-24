from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from src.models import StockStatus


class StateStore:
    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(db_path)
        self._conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS watch_state (
                watch_id TEXT PRIMARY KEY,
                status TEXT NOT NULL,
                reason TEXT,
                checked_at TEXT NOT NULL
            )
            """
        )
        self._conn.commit()

    def get(self, watch_id: str) -> StockStatus | None:
        row = self._conn.execute(
            "SELECT status FROM watch_state WHERE watch_id = ?",
            (watch_id,),
        ).fetchone()
        if row is None:
            return None
        return StockStatus(row["status"])

    def get_detail(self, watch_id: str) -> dict | None:
        row = self._conn.execute(
            "SELECT status, reason, checked_at FROM watch_state WHERE watch_id = ?",
            (watch_id,),
        ).fetchone()
        if row is None:
            return None
        return {
            "status": row["status"],
            "reason": row["reason"],
            "checked_at": row["checked_at"],
        }

    def set(self, watch_id: str, status: StockStatus, reason: str) -> None:
        now = datetime.now(timezone.utc).isoformat()
        self._conn.execute(
            """
            INSERT INTO watch_state (watch_id, status, reason, checked_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(watch_id) DO UPDATE SET
                status = excluded.status,
                reason = excluded.reason,
                checked_at = excluded.checked_at
            """,
            (watch_id, status.value, reason, now),
        )
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()
