"""Tests for data model: JSON read/write, backup creation."""

import json
from pathlib import Path

import pytest

from src.practice_manager.data_model import (
    create_empty_state,
    create_item,
    get_item,
    load,
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
