"""
Status API - read/write practice_status.json.
"""

from fastapi import APIRouter, HTTPException

from src.practice_manager.core import apply_decay, get_data_dir, get_library_root, load, save

router = APIRouter()


def _get_data_dir():
    """Get data_dir. Raises HTTPException on failure."""
    try:
        library_root = get_library_root()
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))
    return get_data_dir(library_root)


@router.get("")
def get_status() -> dict:
    """Return practice status (practice_status.json)."""
    data_dir = _get_data_dir()
    return load(data_dir)


@router.post("")
def post_status(data: dict) -> dict:
    """Save practice status. Validates schema before saving."""
    # Basic validation
    if "items" not in data:
        data["items"] = {}
    data.setdefault("schema_version", 1)
    data.setdefault("decay_rate_percent_per_day", 1.0)
    data.setdefault("focus_instrument", "bass")
    data.setdefault("set_instruments", {})
    data.setdefault("focus_set_ids", [])
    data.setdefault("show_focus_only", False)

    data_dir = _get_data_dir()
    save(data, data_dir)
    return {"ok": True}


@router.post("/decay")
def apply_decay_endpoint() -> dict:
    """Apply decay and save. Returns updated status."""
    data_dir = _get_data_dir()
    data = load(data_dir)
    apply_decay(data)
    save(data, data_dir)
    return data
