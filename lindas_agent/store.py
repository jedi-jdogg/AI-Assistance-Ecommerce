"""SQLite state: daily snapshots, alert de-duplication, price-change log."""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Iterable

SCHEMA = """
CREATE TABLE IF NOT EXISTS snapshots (
  day TEXT NOT NULL,
  kind TEXT NOT NULL,
  payload TEXT NOT NULL,
  PRIMARY KEY (day, kind)
);
CREATE TABLE IF NOT EXISTS alerts_sent (
  key TEXT PRIMARY KEY,
  sent_at TEXT NOT NULL,
  severity TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS price_changes (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  changed_at TEXT NOT NULL,
  variant_id TEXT NOT NULL,
  old_price REAL, new_price REAL,
  reason TEXT, applied INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS variant_daily (
  day TEXT NOT NULL,
  variant_id TEXT NOT NULL,
  inventory_quantity INTEGER,
  units_30d INTEGER,
  net_sales_90d REAL,
  rank INTEGER,
  PRIMARY KEY (day, variant_id)
);
"""


class StateStore:
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(path))
        self.conn.executescript(SCHEMA)

    # --- snapshots -------------------------------------------------------------
    def save_snapshot(self, day: str, kind: str, payload: Any) -> None:
        self.conn.execute(
            "INSERT OR REPLACE INTO snapshots(day, kind, payload) VALUES (?,?,?)",
            (day, kind, json.dumps(payload, default=str)),
        )
        self.conn.commit()

    def load_snapshot(self, day: str, kind: str) -> Any | None:
        row = self.conn.execute("SELECT payload FROM snapshots WHERE day=? AND kind=?", (day, kind)).fetchone()
        return json.loads(row[0]) if row else None

    # --- alert de-dup ----------------------------------------------------------
    def should_send(self, key: str, dedupe_hours: int) -> bool:
        row = self.conn.execute("SELECT sent_at FROM alerts_sent WHERE key=?", (key,)).fetchone()
        if not row:
            return True
        last = datetime.fromisoformat(row[0])
        return datetime.utcnow() - last > timedelta(hours=dedupe_hours)

    def mark_sent(self, key: str, severity: str) -> None:
        self.conn.execute(
            "INSERT OR REPLACE INTO alerts_sent(key, sent_at, severity) VALUES (?,?,?)",
            (key, datetime.utcnow().isoformat(), severity),
        )
        self.conn.commit()

    # --- price log -------------------------------------------------------------
    def log_price_change(self, variant_id: str, old: float, new: float, reason: str, applied: bool) -> None:
        self.conn.execute(
            "INSERT INTO price_changes(changed_at, variant_id, old_price, new_price, reason, applied) VALUES (?,?,?,?,?,?)",
            (datetime.utcnow().isoformat(), variant_id, old, new, reason, int(applied)),
        )
        self.conn.commit()

    def last_price_change(self, variant_id: str) -> datetime | None:
        row = self.conn.execute(
            "SELECT changed_at FROM price_changes WHERE variant_id=? AND applied=1 ORDER BY id DESC LIMIT 1",
            (variant_id,),
        ).fetchone()
        return datetime.fromisoformat(row[0]) if row else None

    # --- variant history -------------------------------------------------------
    def save_variant_daily(self, day: str, rows: Iterable[tuple]) -> None:
        self.conn.executemany(
            "INSERT OR REPLACE INTO variant_daily(day, variant_id, inventory_quantity, units_30d, net_sales_90d, rank)"
            " VALUES (?,?,?,?,?,?)",
            rows,
        )
        self.conn.commit()
