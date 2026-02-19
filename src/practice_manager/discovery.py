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


def _short_part_label(full_part_id: str) -> str:
    """
    Extract short display name from full part_id.
    e.g. "Competition 08 - Prince Charles Welcome to Lochaber line 1" -> "line 1"
    """
    lower = full_part_id.lower()
    for lb in PART_LABELS:
        idx = lower.find(f" {lb}")
        if idx >= 0:
            return full_part_id[idx + 1 :].strip()
    return full_part_id


def _assign_part_to_tune(
    part_id: str,
    tune_names: List[str],
    set_id: str,
    set_folder_name: str,
) -> Tuple[Optional[str], str]:
    """
    Assign part to a tune by longest prefix match.
    Returns (tune_id, tune_name). Uses set_folder_name when no tunes or no match.
    """
    if not tune_names:
        return (f"{set_id}|{set_folder_name}", set_folder_name)
    best_tune: Optional[str] = None
    best_len = 0
    for t in tune_names:
        if part_id.startswith(t) and len(t) > best_len:
            best_tune = t
            best_len = len(t)
    if best_tune:
        return (f"{set_id}|{best_tune}", best_tune)
    return (f"{set_id}|{set_folder_name}", set_folder_name)


def _stem_to_base_key(stem: str, is_pdf: bool) -> str:
    """
    Normalize stem for PDF/WAV pairing.
    PDFs may have instrument suffix (e.g. 'part 1 bass'); WAVs typically don't.
    Strip instrument suffix from PDF stem to match WAV stem.
    """
    if not is_pdf:
        return stem
    lower = stem.lower()
    for inst in INSTRUMENTS:
        for suffix in (f"_{inst}", f" {inst}"):
            if lower.endswith(suffix):
                return stem[: -len(suffix)]
    return stem


def _discover_parts(
    parts_path: Path,
    set_id: str,
    items: Dict[str, Dict],
) -> List[Dict[str, Any]]:
    """
    Discover parts in Parts/ folder.
    Group by label (phrase, line, part). Within each group, sort by streak ascending.
    Pair PDF+WAV by base stem (strip instrument suffix from PDF stem to match WAV).
    """
    discovered: List[Dict[str, Any]] = []
    pdfs_by_key: Dict[str, Path] = {}
    wavs_by_key: Dict[str, Path] = {}
    
    for f in parts_path.iterdir():
        if not f.is_file():
            continue
        name_lower = f.name.lower()
        if _get_part_label(f.name) is None:
            continue  # Ignore files without phrase/line/part
        stem = f.stem
        if name_lower.endswith(".pdf"):
            key = _stem_to_base_key(stem, is_pdf=True)
            if key in pdfs_by_key:
                logger.debug("Multiple instrument PDFs for key %s (using %s)", key, f.name)
            pdfs_by_key[key] = f
        elif name_lower.endswith(".wav"):
            key = _stem_to_base_key(stem, is_pdf=False)
            if key in wavs_by_key:
                logger.debug("Multiple WAVs for key %s (using %s)", key, f.name)
            wavs_by_key[key] = f
    
    # Build part records: group by label, part_id = display name (base key for pairing)
    by_label: Dict[str, List[Tuple[str, Path, Path]]] = {lb: [] for lb in PART_LABELS}
    for key in set(pdfs_by_key.keys()) | set(wavs_by_key.keys()):
        pdf = pdfs_by_key.get(key)
        wav = wavs_by_key.get(key)
        if not pdf or not wav:
            logger.debug("Part %s: missing PDF or WAV pair (orphaned file)", key)
            continue
        label = _get_part_label(key)
        if label:
            by_label[label].append((key, pdf, wav))
    
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
                "short_label": _short_part_label(stem),
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
            # Single-tune sets (e.g. competition): if no tunes, add set folder as tune for "practice complete"
            if not tunes:
                tune_id = f"{set_id}|{set_folder_name}"
                tunes.append({"tune_name": set_folder_name, "tune_id": tune_id})
            
            # Parts from Parts/ subfolder
            parts: List[Dict[str, Any]] = []
            parts_dir = set_path / "Parts"
            if parts_dir.is_dir():
                parts = _discover_parts(parts_dir, set_id, items)
                tune_names = [t["tune_name"] for t in tunes]
                for p in parts:
                    p["part_full_id"] = f"{set_id}|Parts|{p['part_id']}"
                    p["tune_id"], p["tune_name"] = _assign_part_to_tune(
                        p["part_id"], tune_names, set_id, set_folder_name
                    )
            
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
