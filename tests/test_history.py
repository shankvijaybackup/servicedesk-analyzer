from __future__ import annotations

from sda.history import SQLiteHistoryStore


def test_opt_in_history_round_trip_and_delete(tmp_path):
    store = SQLiteHistoryStore(tmp_path / "history.db")
    iteration = {
        "pilot": {"pilot_id": "p-1", "name": "Pilot"},
        "decision": {"code": "widen"},
        "baseline": {"cohort_size": 20},
        "follow_up": {"cohort_size": 20},
    }
    store.save(iteration)
    assert store.list()[0]["decision"] == "widen"
    assert store.get("p-1")[0]["baseline"]["cohort_size"] == 20
    store.delete_all()
    assert store.list() == []
