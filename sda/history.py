"""Opt-in SQLite storage for aggregate iteration scorecards only."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path


class SQLiteHistoryStore:
    def __init__(self, path) -> None:
        self.path = Path(path).expanduser()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self):
        return sqlite3.connect(self.path)

    def _initialize(self) -> None:
        with self._connect() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS iteration_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pilot_id TEXT NOT NULL,
                recorded_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                decision TEXT NOT NULL,
                scorecard_json TEXT NOT NULL
            )""")

    def save(self, iteration: dict) -> None:
        pilot_id = str(iteration["pilot"]["pilot_id"])
        decision = str(iteration["decision"]["code"])
        payload = json.dumps(iteration, sort_keys=True, default=str)
        with self._connect() as db:
            db.execute("INSERT INTO iteration_history (pilot_id, decision, scorecard_json) "
                       "VALUES (?, ?, ?)", (pilot_id, decision, payload))

    def list(self) -> list[dict]:
        with self._connect() as db:
            rows = db.execute("SELECT pilot_id, recorded_at, decision FROM iteration_history "
                              "ORDER BY recorded_at DESC").fetchall()
        return [{"pilot_id": r[0], "recorded_at": r[1], "decision": r[2]} for r in rows]

    def get(self, pilot_id: str) -> list[dict]:
        with self._connect() as db:
            rows = db.execute("SELECT scorecard_json FROM iteration_history WHERE pilot_id = ? "
                              "ORDER BY recorded_at DESC", (pilot_id,)).fetchall()
        return [json.loads(r[0]) for r in rows]

    def delete_all(self) -> None:
        with self._connect() as db:
            db.execute("DELETE FROM iteration_history")
