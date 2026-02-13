"""
Practice Manager - Discovery

Discovers sets, tunes, and parts from the OTPD library.
Uses otpd_music_book_structure.json when present; else infers from filesystem.
"""

import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .config import INSTRUMENTS, PART_LABELS

logger = logging.getLogger(__name__)

# Exclude dirs: #*, Tune Resources, hidden
def _should_exclude_dir(name: str) -> bool:
    return name.startswith("#") or name == "Tune Resources" or name.startswith(".")


def _load_structure_map(data_dir: Path) -> Optional[List[Dict]]:
    """Load otpd_music_book_structure.json if present."""
    path = data_dir / "otpd_music_book_structure.json"
    if not path.exists():
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.warning("Could not load structure map: %s", e)
        return None


def _infer_tunes_from_set_folder(set_path: Path) -> List[str]:
    """
    Infer tune names from PDF/WAV in set folder.
    Look for complete files (no instrument suffix): Set NNa - Title.pdf/.wav
    """
    tune_names: set[str] = set()
    for f in set_path.iterdir():
        if f.is_file() and f.suffix.lower() in (".pdf", ".wav"):
            base = f.stem
            # Skip instrument parts (_bass, _snare, etc.)
            if any(base.lower().endswith(f"_{inst}") for inst in INSTRUMENTS):
                continue
            # Match Set NNa - Title (letter optional)
            if re.match(r"Set\s+\d+[a-z]?\s+-\s+.+", base, re.IGNORECASE):
                tune_names.add(base)
    return sorted(tune_names)


def _get_part_label(filename: str) -> Optional[str]:
    """Return which label (phrase/line/part) is in filename, or None. Case-insensitive."""
    lower = filename.lower()
    for label in PART_LABELS:
        if label in lower:
            return label
    return None


def _discover_parts(
    parts_path: Path,
    set_id: str,
    items: Dict[str, Dict],
) -> List[Dict[str, Any]]:
    """
    Discover parts in Parts/ folder.
    Group by label (phrase, line, part). Within each group, sort by streak ascending.
    Pair PDF+WAV by shared stem; log warnings on ambiguity.
    """
    discovered: List[Dict[str, Any]] = []
    pdfs: Dict[str, Path] = {}
    wavs: Dict[str, Path] = {}
    
    for f in parts_path.iterdir():
        if not f.is_file():
            continue
        name_lower = f.name.lower()
        if _get_part_label(f.name) is None:
            continue  # Ignore files without phrase/line/part
        stem = f.stem
        if name_lower.endswith(".pdf"):
            if stem in pdfs:
                logger.warning("Ambiguous PDF pairing for stem %s: %s vs %s", stem, pdfs[stem], f)
            pdfs[stem] = f
        elif name_lower.endswith(".wav"):
            if stem in wavs:
                logger.warning("Ambiguous WAV pairing for stem %s: %s vs %s", stem, wavs[stem], f)
            wavs[stem] = f
    
    # Build part records: group by label, part_id = stem
    by_label: Dict[str, List[Tuple[str, Path, Path]]] = {lb: [] for lb in PART_LABELS}
    for stem in set(pdfs.keys()) | set(wavs.keys()):
        pdf = pdfs.get(stem)
        wav = wavs.get(stem)
        if not pdf or not wav:
            logger.warning("Part %s: missing PDF or WAV pair", stem)
            continue
        label = _get_part_label(stem)
        if label:
            by_label[label].append((stem, pdf, wav))
    
    # Order: phrase, line, part. Within each, sort by streak (need items for streak)
    def streak_for(part_stem: str) -> int:
        full_id = f"{set_id}|Parts|{part_stem}"
        rec = items.get(full_id, {})
        return rec.get("streak", 0)
    
    for label in PART_LABELS:
        parts_in_label = by_label.get(label, [])
        # Sort by streak ascending
        parts_in_label.sort(key=lambda x: streak_for(x[0]))
        for stem, pdf_path, wav_path in parts_in_label:
            discovered.append({
                "part_id": stem,
                "label": label,
                "pdf_path": pdf_path,
                "wav_path": wav_path,
            })
    
    return discovered


def discover(
    library_root: Path,
    data_dir: Path,
    items: Dict[str, Dict],
) -> List[Dict[str, Any]]:
    """
    Discover all sets (with tunes and parts) from the library.
    
    Returns a flat list of set dicts, each with:
      - section_name, set_folder_name, set_path
      - set_id (Section|SetFolder)
      - tunes: [{tune_name, tune_id, ...}]
      - parts: [{part_id, label, pdf_path, wav_path}, ...] (from Parts/ if exists)
    
    items: current practice status items (for streak-based part ordering)
    """
    structure = _load_structure_map(data_dir)
    result: List[Dict[str, Any]] = []
    
    # Find section folders
    for item in library_root.iterdir():
        if not item.is_dir() or _should_exclude_dir(item.name):
            continue
        # Match "Section N - Name"
        if not re.match(r"Section\s+\d+\s+-", item.name, re.IGNORECASE):
            continue
        
        section_name = item.name
        
        for set_item in item.iterdir():
            if not set_item.is_dir() or set_item.name.startswith("."):
                continue
            
            set_folder_name = set_item.name
            set_path = set_item
            set_id = f"{section_name}|{set_folder_name}"
            
            # Tunes from structure or inference
            tunes: List[Dict[str, Any]] = []
            if structure:
                for sec in structure:
                    if sec.get("section_name") == section_name:
                        for s in sec.get("sets", []):
                            if s.get("folder_name") == set_folder_name:
                                for t in s.get("tunes", []):
                                    tune_name = t.get("tune_name", "")
                                    if tune_name:
                                        tune_id = f"{set_id}|{tune_name}"
                                        tunes.append({
                                            "tune_name": tune_name,
                                            "tune_id": tune_id,
                                        })
                                break
                        break
            
            if not tunes:
                inferred = _infer_tunes_from_set_folder(set_path)
                for tune_name in inferred:
                    tune_id = f"{set_id}|{tune_name}"
                    tunes.append({"tune_name": tune_name, "tune_id": tune_id})
            
            # Parts from Parts/ subfolder
            parts: List[Dict[str, Any]] = []
            parts_dir = set_path / "Parts"
            if parts_dir.is_dir():
                parts = _discover_parts(parts_dir, set_id, items)
                for p in parts:
                    p["part_full_id"] = f"{set_id}|Parts|{p['part_id']}"
            
            result.append({
                "section_name": section_name,
                "set_folder_name": set_folder_name,
                "set_path": set_path,
                "set_id": set_id,
                "tunes": tunes,
                "parts": parts,
            })
    
    # Sort by section then set folder name
    result.sort(key=lambda x: (x["section_name"], x["set_folder_name"]))
    return result
