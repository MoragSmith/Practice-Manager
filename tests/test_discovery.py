"""Tests for discovery: part grouping, sorting."""

from pathlib import Path

import pytest

from src.practice_manager.discovery import (
    _discover_parts,
    _get_part_label,
    _infer_tunes_from_set_folder,
    discover,
)


def test_get_part_label_phrase() -> None:
    assert _get_part_label("Set01a_phrase1.pdf") == "phrase"
    assert _get_part_label("PHRASE_01.wav") == "phrase"


def test_get_part_label_line() -> None:
    assert _get_part_label("line_02.pdf") == "line"


def test_get_part_label_part() -> None:
    assert _get_part_label("bass_part_A.wav") == "part"


def test_get_part_label_none() -> None:
    assert _get_part_label("random_file.pdf") is None


def test_infer_tunes_skips_instrument_parts(tmp_path: Path) -> None:
    (tmp_path / "Set 01a - Tune.pdf").write_text("")
    (tmp_path / "Set 01a - Tune.wav").write_text("")
    (tmp_path / "Set 01a - Tune_bass.pdf").write_text("")
    tunes = _infer_tunes_from_set_folder(tmp_path)
    assert "Set 01a - Tune" in tunes
    assert len(tunes) == 1


def test_discover_parts_groups_and_sorts(tmp_path: Path) -> None:
    parts_dir = tmp_path / "Parts"
    parts_dir.mkdir()
    (parts_dir / "phrase_01.pdf").write_text("")
    (parts_dir / "phrase_01.wav").write_text("")
    (parts_dir / "line_01.pdf").write_text("")
    (parts_dir / "line_01.wav").write_text("")
    (parts_dir / "part_01.pdf").write_text("")
    (parts_dir / "part_01.wav").write_text("")
    
    items = {}
    result = _discover_parts(parts_dir, "Section1|Set01", items)
    
    labels = [r["label"] for r in result]
    assert labels == ["phrase", "line", "part"]


def test_discover_parts_sorts_by_streak(tmp_path: Path) -> None:
    parts_dir = tmp_path / "Parts"
    parts_dir.mkdir()
    (parts_dir / "phrase_a.pdf").write_text("")
    (parts_dir / "phrase_a.wav").write_text("")
    (parts_dir / "phrase_b.pdf").write_text("")
    (parts_dir / "phrase_b.wav").write_text("")
    
    set_id = "Section1|Set01"
    items = {
        f"{set_id}|Parts|phrase_b": {"streak": 5},
        f"{set_id}|Parts|phrase_a": {"streak": 0},
    }
    result = _discover_parts(parts_dir, set_id, items)
    
    phrase_results = [r for r in result if r["label"] == "phrase"]
    assert len(phrase_results) == 2
    # Lower streak first
    assert phrase_results[0]["part_id"] == "phrase_a"
    assert phrase_results[1]["part_id"] == "phrase_b"


def test_discover_skips_files_without_label(tmp_path: Path) -> None:
    library = tmp_path / "lib"
    library.mkdir()
    (library / "Section 1 - Test").mkdir()
    set_dir = library / "Section 1 - Test" / "Set 01 - Foo"
    set_dir.mkdir()
    (set_dir / "Set 01a - Tune.pdf").write_text("")
    (set_dir / "Set 01a - Tune.wav").write_text("")
    
    parts_dir = set_dir / "Parts"
    parts_dir.mkdir()
    (parts_dir / "phrase_01.pdf").write_text("")
    (parts_dir / "phrase_01.wav").write_text("")
    (parts_dir / "other.pdf").write_text("")  # no phrase/line/part
    (parts_dir / "other.wav").write_text("")
    
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    items = {}
    result = discover(library, data_dir, items)
    
    assert len(result) == 1
    parts = result[0]["parts"]
    assert len(parts) == 1
    assert parts[0]["part_id"] == "phrase_01"
