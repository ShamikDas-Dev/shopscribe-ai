import json

from storage.history import get_recent_history, save_history


def test_history_round_trip_uses_local_database(tmp_path):
    db_path = tmp_path / "history.sqlite3"
    payload = json.dumps({"product_title": "Example"})

    row_id = save_history("Example product", "English", "qwen3:4b", payload, db_path=db_path)
    rows = get_recent_history(limit=5, db_path=db_path)

    assert row_id == 1
    assert len(rows) == 1
    assert rows[0]["product_name"] == "Example product"
    assert rows[0]["content_json"] == payload
