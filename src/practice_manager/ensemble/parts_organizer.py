"""
Practice Manager - Parts organizer (adapted from OTPD Music Manager FileOrganizer)

Moves downloaded part files from downloads_dir to set_folder/Parts/.
Uses library structure (no database) to map filename prefix to target folder.
"""

import logging
import re
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Instruments for suffix stripping (from config)
INSTRUMENTS = ["bagpipes", "seconds", "bass", "snare", "tenor"]
PART_LABELS = ["phrase", "line", "part"]


def _build_folder_map(library_root: Path) -> Dict[str, Tuple[str, str]]:
    """
    Build prefix -> (section_name, folder_name) from library structure.

    Keys are folder names (and optionally shorter prefixes for flexible matching).
    """
    mapping: Dict[str, Tuple[str, str]] = {}
    for item in library_root.iterdir():
        if not item.is_dir() or item.name.startswith("#") or item.name.startswith("."):
            continue
        if not re.match(r"Section\s+\d+\s+-", item.name, re.IGNORECASE):
            continue
        section_name = item.name
        for set_item in item.iterdir():
            if not set_item.is_dir() or set_item.name.startswith("."):
                continue
            folder_name = set_item.name
            mapping[folder_name] = (section_name, folder_name)
            prefix_short = folder_name.split(" - ")[0].strip()
            if prefix_short and prefix_short not in mapping:
                mapping[prefix_short] = (section_name, folder_name)
    return mapping


def _extract_prefix(filename: str) -> str:
    """
    Extract folder-matching prefix from part filename.

    e.g. "Competition 08 - Prince Charles Welcome to Lochaber part 1 bass.pdf"
    -> "Competition 08 - Prince Charles Welcome to Lochaber"
    For WAV (complete score): "Competition 08 - Prince Charles.wav" -> "Competition 08 - Prince Charles"
    """
    stem = Path(filename).stem
    lower = stem.lower()
    for label in PART_LABELS:
        idx = lower.find(f" {label} ")
        if idx >= 0:
            stem = stem[:idx].strip()
            break
    for inst in INSTRUMENTS:
        for suffix in (f"_{inst}", f" {inst}"):
            if stem.lower().endswith(suffix):
                stem = stem[: -len(suffix)].strip()
                break
    return stem.strip()


def _find_target_folder(prefix: str, folder_map: Dict[str, Tuple[str, str]]) -> Optional[Tuple[str, str]]:
    """Find (section_name, folder_name) for a given prefix."""
    if prefix in folder_map:
        return folder_map[prefix]
    for key, val in folder_map.items():
        if prefix.startswith(key) or key.startswith(prefix):
            return val
    return None


class PartsOrganizer:
    """Organize downloaded part files into set_folder/Parts/."""

    def __init__(self, downloads_dir: Path, scores_dir: Path, library_root: Optional[Path] = None):
        self.downloads_dir = Path(downloads_dir)
        self.scores_dir = Path(scores_dir)
        self.library_root = library_root or scores_dir
        self._folder_map = _build_folder_map(self.library_root)
        self.stats = {"organized": 0, "errors": 0}

    def organize_downloads(
        self, dry_run: bool = False, only_files: Optional[List[Path]] = None
    ) -> Dict:
        """
        Move part files from downloads_dir to set_folder/Parts/.

        If only_files is provided, only organize those paths.
        Otherwise organize all part-like PDF/WAV in downloads_dir.
        """
        if not self.downloads_dir.exists():
            return self.stats
        to_process = only_files if only_files else list(self.downloads_dir.iterdir())
        for file_path in to_process:
            file_path = Path(file_path)
            if not file_path.is_file() or file_path.name.startswith("."):
                continue
            if file_path.suffix.lower() not in (".pdf", ".wav"):
                continue
            prefix = _extract_prefix(file_path.name)
            if not prefix:
                continue
            try:
                self._organize_file(file_path, dry_run)
            except Exception as e:
                logger.error("Error organizing %s: %s", file_path.name, e)
                self.stats["errors"] += 1
        return self.stats

    def _organize_file(self, file_path: Path, dry_run: bool) -> bool:
        """Move a single file to the correct set_folder/Parts/."""
        prefix = _extract_prefix(file_path.name)
        target = _find_target_folder(prefix, self._folder_map)
        if not target:
            logger.warning("No matching folder for prefix '%s' (from %s)", prefix[:50], file_path.name)
            return False
        section_name, folder_name = target
        parts_dir = self.scores_dir / section_name / folder_name / "Parts"
        target_path = parts_dir / file_path.name
        if dry_run:
            logger.info("Would move %s -> %s/Parts/", file_path.name, folder_name)
            return True
        parts_dir.mkdir(parents=True, exist_ok=True)
        if target_path.exists():
            target_path.unlink()
        shutil.move(str(file_path), str(target_path))
        logger.info("Moved %s -> %s/Parts/", file_path.name, folder_name)
        self.stats["organized"] += 1
        return True
