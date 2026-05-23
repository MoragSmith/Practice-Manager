"""Tests for data model: JSON read/write, backup creation."""

import json
from pathlib import Path

import pytest

from src.practice_manager.core.data_model import (
    create_empty_state,
    create_item,
    get_item,
    load,
    reconcile_missing_items,
    save,
    set_item,
)


def test_create_empty_state() -> None:
    state = create_empty_state()
    assert "schema_version" in state
    assert "items" in state
    assert state["focus_set_ids"] == []
    assert state["focus_instrument"] == "bass"
    assert state["set_instruments"] == {}


def test_create_item() -> None:
    item = create_item("tune", streak=5, score=50.0)
    assert item["type"] == "tune"
    assert item["streak"] == 5
    assert item["score"] == 50.0


def test_load_missing_file_returns_empty(tmp_path: Path) -> None:
    data = load(tmp_path)
    assert "items" in data
    assert data["items"] == {}


def test_save_creates_file(tmp_path: Path) -> None:
    data = create_empty_state()
    save(data, tmp_path)
    json_path = tmp_path / "practice_status.json"
    assert json_path.exists()
    loaded = json.loads(json_path.read_text())
    assert loaded["schema_version"] == 1


def test_save_creates_backup(tmp_path: Path) -> None:
    data = create_empty_state()
    save(data, tmp_path)
    # Second save should create backup
    save(data, tmp_path)
    backup_dir = tmp_path / "backups"
    assert backup_dir.exists()
    backups = list(backup_dir.glob("practice_status_*.json"))
    assert len(backups) >= 1


def test_load_then_save_preserves_data(tmp_path: Path) -> None:
    data = create_empty_state()
    set_item(data, "set1", "set", 3, 30.0)
    save(data, tmp_path)
    loaded = load(tmp_path)
    assert get_item(loaded, "set1")["streak"] == 3
    assert get_item(loaded, "set1")["score"] == 30.0


def test_set_item_creates_new() -> None:
    data = create_empty_state()
    set_item(data, "tune1", "tune", 2, 20.0)
    assert "tune1" in data["items"]
    assert data["items"]["tune1"]["streak"] == 2


def test_reconcile_missing_items_marks_removed_tunes_and_restores_reappeared() -> None:
    data = create_empty_state()
    present_id = "Section 1|Set 01|Tune A"
    removed_id = "Section 1|Set 01|Tune B"
    set_item(data, present_id, "tune", 4, 40.0)
    set_item(data, removed_id, "tune", 7, 70.0)

    changed = reconcile_missing_items(
        data,
        [{"set_id": "Section 1|Set 01", "tunes": [{"tune_id": present_id}], "parts": []}],
    )

    assert changed is True
    assert data["items"][present_id]["missing"] is False
    assert data["items"][removed_id]["missing"] is True
    assert data["items"][removed_id]["streak"] == 7
    assert data["items"][removed_id]["score"] == 70.0

    changed = reconcile_missing_items(
        data,
        [{"set_id": "Section 1|Set 01", "tunes": [{"tune_id": removed_id}], "parts": []}],
    )

    assert changed is True
    assert data["items"][present_id]["missing"] is True
    assert data["items"][removed_id]["missing"] is False


def test_reconcile_missing_items_ignores_organizational_sets() -> None:
    data = create_empty_state()
    set_item(data, "Section 1|Set 01", "set", 0, 0.0)

    changed = reconcile_missing_items(data, [])

    assert changed is False
    assert data["items"]["Section 1|Set 01"]["missing"] is False
