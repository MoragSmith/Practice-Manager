"""
Library API - browse sets, tunes, parts.
"""

from pathlib import Path

from fastapi import APIRouter, HTTPException

from src.practice_manager.core import discover, get_data_dir, get_library_root, load

router = APIRouter()


def _get_context() -> tuple[Path, Path, dict]:
    """Get library_root, data_dir, and data. Raises HTTPException on failure."""
    try:
        library_root = get_library_root()
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))
    data_dir = get_data_dir(library_root)
    data = load(data_dir)
    return library_root, data_dir, data


def _serialize_set(s: dict, library_root: Path) -> dict:
    """Convert set dict for JSON (paths as strings relative to library)."""
    set_path = s.get("set_path")
    try:
        rel_path = str(set_path.relative_to(library_root)) if set_path else None
    except (ValueError, TypeError):
        rel_path = None
    return {
        "section_name": s["section_name"],
        "set_folder_name": s["set_folder_name"],
        "set_id": s["set_id"],
        "set_path": rel_path,
        "tunes": [
            {"tune_name": t["tune_name"], "tune_id": t["tune_id"]}
            for t in s.get("tunes", [])
        ],
        "parts": [
            {
                "part_id": p["part_id"],
                "short_label": p.get("short_label"),
                "label": p["label"],
                "part_full_id": p.get("part_full_id"),
                "tune_id": p.get("tune_id"),
                "tune_name": p.get("tune_name"),
                "pdf_path": str(p["pdf_path"].relative_to(library_root)) if p.get("pdf_path") else None,
                "wav_path": str(p["wav_path"].relative_to(library_root)) if p.get("wav_path") else None,
            }
            for p in s.get("parts", [])
        ],
    }


@router.get("")
def get_library() -> dict:
    """Return full library: sections, sets, tunes, parts."""
    library_root, data_dir, data = _get_context()
    items = data.get("items", {})
    sets_list = discover(library_root, data_dir, items)
    return {
        "library_root": str(library_root),
        "sets": [_serialize_set(s, library_root) for s in sets_list],
    }


@router.get("/sets/{set_id:path}")
def get_set(set_id: str) -> dict:
    """Return a single set by ID (Section|SetFolder)."""
    library_root, data_dir, data = _get_context()
    items = data.get("items", {})
    sets_list = discover(library_root, data_dir, items)
    for s in sets_list:
        if s["set_id"] == set_id:
            return _serialize_set(s, library_root)
    raise HTTPException(status_code=404, detail=f"Set not found: {set_id}")
