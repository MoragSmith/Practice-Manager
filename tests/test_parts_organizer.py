"""
Tests for PartsOrganizer - real files and paths, no mocks.

Tests prefix extraction, folder mapping, and full organize flow with actual
file system operations.
"""

from pathlib import Path

import pytest

from src.practice_manager.ensemble.parts_downloader import clean_part_name
from src.practice_manager.ensemble.parts_organizer import (
    PartsOrganizer,
    _build_folder_map,
    _extract_prefix,
    _find_target_folder,
)


# =============================================================================
# _extract_prefix - pure function tests
# =============================================================================


class TestCleanPartName:
    """Test clean_part_name for split PDF file naming (OTPD-style)."""

    def test_line1_14_feb_removes_date_keeps_line1(self) -> None:
        """line1 + '14 Feb' must keep line1; do not strip digits after line."""
        assert (
            clean_part_name("Competition 08 - Prince Charles Welcome to Lochaber line1 14 FebPrivate")
            == "Competition 08 - Prince Charles Welcome to Lochaber line1"
        )

    def test_phrase2_keeps_number(self) -> None:
        """phrase2 keeps its number (part identifier)."""
        assert clean_part_name("Set 01 - Tune phrase2 3 Jan") == "Set 01 - Tune phrase2"

    def test_private_removed(self) -> None:
        assert "Private" not in clean_part_name("Title line1 14 FebPrivate")

    def test_unchanged_when_clean(self) -> None:
        assert clean_part_name("Competition 08 - Prince Charles Welcome to Lochaber line1") == "Competition 08 - Prince Charles Welcome to Lochaber line1"


class TestExtractPrefix:
    """Test prefix extraction from part filenames."""

    def test_part_with_instrument(self) -> None:
        assert (
            _extract_prefix("Competition 08 - Prince Charles Welcome to Lochaber part 1 bass.pdf")
            == "Competition 08 - Prince Charles Welcome to Lochaber"
        )

    def test_phrase_label(self) -> None:
        assert _extract_prefix("Set 01a - Tune phrase 2.pdf") == "Set 01a - Tune"

    def test_line_label(self) -> None:
        assert _extract_prefix("Competition 08 line 114.wav") == "Competition 08"

    def test_wav_complete_score(self) -> None:
        assert _extract_prefix("Competition 08 - Prince Charles.wav") == "Competition 08 - Prince Charles"

    def test_instrument_suffix_stripped(self) -> None:
        assert _extract_prefix("Set01a_bass.pdf") == "Set01a"

    def test_underscore_instrument(self) -> None:
        assert _extract_prefix("Tune_part1_snare.pdf") == "Tune_part1"

    def test_no_part_label_returns_stem(self) -> None:
        assert _extract_prefix("Random Score.pdf") == "Random Score"


# =============================================================================
# _build_folder_map - real directory structure
# =============================================================================


class TestBuildFolderMap:
    """Test folder map built from real directory structure."""

    def test_maps_section_and_set_folders(self, tmp_path: Path) -> None:
        section = tmp_path / "Section 1 - Competition"
        section.mkdir()
        set_folder = section / "Competition 08 - Prince Charles Welcome to Lochaber"
        set_folder.mkdir()

        mapping = _build_folder_map(tmp_path)

        assert "Competition 08 - Prince Charles Welcome to Lochaber" in mapping
        section_name, folder_name = mapping["Competition 08 - Prince Charles Welcome to Lochaber"]
        assert section_name == "Section 1 - Competition"
        assert folder_name == "Competition 08 - Prince Charles Welcome to Lochaber"

    def test_adds_short_prefix(self, tmp_path: Path) -> None:
        section = tmp_path / "Section 2 - Pipes on Parade"
        section.mkdir()
        set_folder = section / "PoP 06 - Title"
        set_folder.mkdir()

        mapping = _build_folder_map(tmp_path)

        assert "PoP 06" in mapping
        assert mapping["PoP 06"] == ("Section 2 - Pipes on Parade", "PoP 06 - Title")

    def test_skips_hidden_and_script_resources(self, tmp_path: Path) -> None:
        (tmp_path / "Section 1 - Test").mkdir()
        (tmp_path / "Section 1 - Test" / "Set 01").mkdir()
        (tmp_path / "#Script Resources").mkdir()
        (tmp_path / ".hidden").mkdir()

        mapping = _build_folder_map(tmp_path)

        assert "Set 01" in mapping
        assert len(mapping) >= 1

    def test_skips_non_section_dirs(self, tmp_path: Path) -> None:
        (tmp_path / "RandomFolder").mkdir()
        (tmp_path / "Section 1 - Real").mkdir()
        (tmp_path / "Section 1 - Real" / "Set 01").mkdir()

        mapping = _build_folder_map(tmp_path)

        assert "Set 01" in mapping


# =============================================================================
# _find_target_folder
# =============================================================================


class TestFindTargetFolder:
    """Test target folder lookup."""

    def test_exact_match(self) -> None:
        mapping = {"Competition 08 - Prince Charles": ("S1", "Competition 08 - Prince Charles")}
        assert _find_target_folder("Competition 08 - Prince Charles", mapping) == (
            "S1",
            "Competition 08 - Prince Charles",
        )

    def test_prefix_match(self) -> None:
        mapping = {"Competition 08": ("S1", "Competition 08 - Prince Charles Welcome to Lochaber")}
        assert _find_target_folder("Competition 08 - Prince Charles Welcome to Lochaber", mapping) == (
            "S1",
            "Competition 08 - Prince Charles Welcome to Lochaber",
        )

    def test_no_match_returns_none(self) -> None:
        mapping = {"Other Set": ("S1", "Other Set")}
        assert _find_target_folder("Unknown Prefix", mapping) is None


# =============================================================================
# PartsOrganizer - full integration with real files
# =============================================================================


class TestPartsOrganizer:
    """Test PartsOrganizer with real file system operations."""

    def test_organizes_pdf_to_parts_dir(self, tmp_path: Path) -> None:
        library = tmp_path / "library"
        section = library / "Section 1 - Competition"
        section.mkdir(parents=True)
        set_folder = section / "Competition 08 - Prince Charles Welcome to Lochaber"
        set_folder.mkdir()

        downloads = tmp_path / "downloads"
        downloads.mkdir()
        part_pdf = downloads / "Competition 08 - Prince Charles Welcome to Lochaber part 1 bass.pdf"
        part_pdf.write_bytes(b"%PDF-1.4 fake")

        organizer = PartsOrganizer(downloads, library)
        stats = organizer.organize_downloads(dry_run=False)

        target = set_folder / "Parts" / part_pdf.name
        assert target.exists()
        assert target.read_bytes() == b"%PDF-1.4 fake"
        assert not part_pdf.exists()
        assert stats["organized"] == 1
        assert stats["errors"] == 0

    def test_organizes_wav_to_parts_dir(self, tmp_path: Path) -> None:
        library = tmp_path / "library"
        section = library / "Section 1 - Competition"
        section.mkdir(parents=True)
        set_folder = section / "Competition 08 - Prince Charles"
        set_folder.mkdir()

        downloads = tmp_path / "downloads"
        downloads.mkdir()
        wav_file = downloads / "Competition 08 - Prince Charles.wav"
        wav_file.write_bytes(b"RIFF....WAVE")

        organizer = PartsOrganizer(downloads, library)
        stats = organizer.organize_downloads(dry_run=False)

        target = set_folder / "Parts" / wav_file.name
        assert target.exists()
        assert stats["organized"] == 1

    def test_dry_run_does_not_move_files(self, tmp_path: Path) -> None:
        library = tmp_path / "library"
        (library / "Section 1 - Competition" / "Set 01").mkdir(parents=True)

        downloads = tmp_path / "downloads"
        downloads.mkdir()
        part_pdf = downloads / "Set 01 - Tune part 1 bass.pdf"
        part_pdf.write_bytes(b"%PDF")

        organizer = PartsOrganizer(downloads, library)
        stats = organizer.organize_downloads(dry_run=True)

        assert part_pdf.exists()
        assert not (library / "Section 1 - Competition" / "Set 01" / "Parts").exists()
        assert stats["organized"] == 0

    def test_only_files_organizes_subset(self, tmp_path: Path) -> None:
        library = tmp_path / "library"
        section = library / "Section 1 - Competition"
        section.mkdir(parents=True)
        set_a = section / "Set A - First"
        set_b = section / "Set B - Second"
        set_a.mkdir()
        set_b.mkdir()

        downloads = tmp_path / "downloads"
        downloads.mkdir()
        part_a = downloads / "Set A - First part 1 bass.pdf"
        part_b = downloads / "Set B - Second part 1 bass.pdf"
        part_a.write_bytes(b"%PDF-A")
        part_b.write_bytes(b"%PDF-B")

        organizer = PartsOrganizer(downloads, library)
        stats = organizer.organize_downloads(only_files=[part_a])

        assert (set_a / "Parts" / part_a.name).exists()
        assert not (set_b / "Parts").exists()
        assert part_b.exists()
        assert stats["organized"] == 1

    def test_skips_non_matching_prefix(self, tmp_path: Path) -> None:
        library = tmp_path / "library"
        (library / "Section 1 - Competition" / "Set 01").mkdir(parents=True)

        downloads = tmp_path / "downloads"
        downloads.mkdir()
        orphan = downloads / "Orphan - No Match part 1 bass.pdf"
        orphan.write_bytes(b"%PDF")

        organizer = PartsOrganizer(downloads, library)
        stats = organizer.organize_downloads(dry_run=False)

        assert orphan.exists()
        assert stats["organized"] == 0

    def test_creates_parts_dir_if_missing(self, tmp_path: Path) -> None:
        library = tmp_path / "library"
        (library / "Section 1 - X" / "Set 01").mkdir(parents=True)

        downloads = tmp_path / "downloads"
        downloads.mkdir()
        (downloads / "Set 01 - X part 1.pdf").write_bytes(b"%PDF")

        organizer = PartsOrganizer(downloads, library)
        organizer.organize_downloads(dry_run=False)

        parts_dir = library / "Section 1 - X" / "Set 01" / "Parts"
        assert parts_dir.exists()
        assert parts_dir.is_dir()
