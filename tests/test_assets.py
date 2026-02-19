"""Tests for asset resolution (instrument-specific PDFs)."""

from pathlib import Path

import pytest

from src.practice_manager.assets import get_part_assets, get_tune_assets


def test_get_part_assets_prefers_instrument_pdf(tmp_path: Path) -> None:
    """When bass PDF exists, returns it over the stored (bagpipes) PDF."""
    base = "Competition 08 - Prince Charles Welcome to Lochaber line 1"
    (tmp_path / f"{base}_bagpipes.pdf").write_text("")
    (tmp_path / f"{base}_bass.pdf").write_text("")
    (tmp_path / f"{base}.wav").write_text("")

    part_record = {
        "part_id": base,
        "pdf_path": tmp_path / f"{base}_bagpipes.pdf",
        "wav_path": tmp_path / f"{base}.wav",
    }
    pdf_path, wav_path = get_part_assets(part_record, "bass")
    assert pdf_path == tmp_path / f"{base}_bass.pdf"
    assert wav_path == tmp_path / f"{base}.wav"


def test_get_tune_assets_set_folder(tmp_path: Path) -> None:
    """Complete tune WAV/PDF in set folder (e.g. Competition 08)."""
    set_folder = tmp_path / "Competition 08 - Prince Charles Welcome to Lochaber"
    set_folder.mkdir()
    (set_folder / "Competition 08 - Prince Charles Welcome to Lochaber.wav").write_text("")
    (set_folder / "Competition 08 - Prince Charles Welcome to Lochaber_bass.pdf").write_text("")
    pdf_path, wav_path = get_tune_assets(set_folder, "Competition 08 - Prince Charles Welcome to Lochaber", "bass")
    assert wav_path == set_folder / "Competition 08 - Prince Charles Welcome to Lochaber.wav"
    assert pdf_path == set_folder / "Competition 08 - Prince Charles Welcome to Lochaber_bass.pdf"


def test_get_tune_assets_fallback_to_set_folder_name(tmp_path: Path) -> None:
    """When tune_name differs from folder, try set_folder_name."""
    set_folder = tmp_path / "Competition 08 - Prince Charles Welcome to Lochaber"
    set_folder.mkdir()
    (set_folder / "Competition 08 - Prince Charles Welcome to Lochaber.wav").write_text("")
    (set_folder / "Competition 08 - Prince Charles Welcome to Lochaber_bass.pdf").write_text("")
    # tune_name from structure might differ slightly
    pdf_path, wav_path = get_tune_assets(set_folder, "Competition 08a - Prince Charles Welcome to Lochaber", "bass")
    assert wav_path is not None
    assert pdf_path is not None


def test_get_part_assets_fallback_when_no_instrument_pdf(tmp_path: Path) -> None:
    """When no instrument-specific PDF exists, uses stored PDF."""
    base = "phrase 1"
    (tmp_path / f"{base}_bagpipes.pdf").write_text("")
    (tmp_path / f"{base}.wav").write_text("")

    part_record = {
        "part_id": base,
        "pdf_path": tmp_path / f"{base}_bagpipes.pdf",
        "wav_path": tmp_path / f"{base}.wav",
    }
    pdf_path, wav_path = get_part_assets(part_record, "bass")
    assert pdf_path == tmp_path / f"{base}_bagpipes.pdf"
    assert wav_path == tmp_path / f"{base}.wav"
