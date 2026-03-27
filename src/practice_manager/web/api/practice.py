"""
Practice API - session start, success, fail.
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from urllib.parse import quote

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.practice_manager.core import (
    discover,
    get_data_dir,
    get_item,
    get_library_root,
    get_part_assets,
    get_tune_assets,
    load,
    save,
    set_item,
)

router = APIRouter()


class StartSessionRequest(BaseModel):
    """Request body for starting a practice session."""

    item_type: str
    item_id: str
    display_name: str
    instrument: str
    set_id: Optional[str] = None
    set_path: Optional[str] = None
    tune_name: Optional[str] = None
    part_record: Optional[dict] = None


class SuccessFailRequest(BaseModel):
    """Request body for success/fail."""

    item_id: str
    item_type: str


def _get_context():
    """Get library_root, data_dir, data."""
    try:
        library_root = get_library_root()
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))
    data_dir = get_data_dir(library_root)
    data = load(data_dir)
    return library_root, data_dir, data


@router.post("/start")
def start_session(req: StartSessionRequest) -> dict:
    """
    Start a practice session. Resets streak to 0, persists instrument.
    Returns pdf_url and wav_url for streaming.
    """
    library_root, data_dir, data = _get_context()
    item_type = req.item_type
    item_id = req.item_id
    instrument = req.instrument
    set_id = req.set_id
    set_path = req.set_path
    tune_name = req.tune_name
    part_record = req.part_record

    pdf_path = None
    wav_path = None

    if item_type == "tune" and set_path and tune_name:
        abs_set_path = (library_root / set_path.lstrip("/")).resolve()
        pdf_path, wav_path = get_tune_assets(abs_set_path, tune_name, instrument)
    elif item_type == "part" and part_record and part_record.get("pdf_path") and part_record.get("wav_path"):
        pr = {
            "pdf_path": library_root / part_record["pdf_path"],
            "wav_path": library_root / part_record["wav_path"],
            "part_id": part_record.get("part_id", ""),
        }
        pdf_path, wav_path = get_part_assets(pr, instrument)
    else:
        # Resolve from discovery
        items = data.get("items", {})
        sets_list = discover(library_root, data_dir, items)
        for s in sets_list:
            if s["set_id"] != (set_id or ""):
                continue
            if item_type == "tune":
                for t in s.get("tunes", []):
                    if t["tune_id"] == item_id:
                        pdf_path, wav_path = get_tune_assets(s["set_path"], t["tune_name"], instrument)
                        break
            else:
                for p in s.get("parts", []):
                    if p.get("part_full_id") == item_id:
                        pdf_path, wav_path = get_part_assets(p, instrument)
                        break
            break

    # Persist instrument
    if set_id:
        si = dict(data.get("set_instruments", {}))
        si[set_id] = instrument
        data["set_instruments"] = si
    data["focus_instrument"] = instrument
    set_item(data, item_id, item_type, 0, 0.0)
    save(data, data_dir)

    def _rel(p):
        if p and p.exists():
            return str(p.relative_to(library_root))
        return None

    def _asset_url(base: str, path):
        r = _rel(path)
        return f"/api/assets/{base}?path={quote(r)}" if r else None

    return {
        "pdf_url": _asset_url("pdf", pdf_path),
        "wav_url": _asset_url("wav", wav_path),
        "streak": 0,
    }


@router.post("/success")
def record_success(req: SuccessFailRequest) -> dict:
    """Record successful practice. Increments streak, updates score."""
    _, data_dir, data = _get_context()
    item_id = req.item_id
    item_type = req.item_type
    rec = get_item(data, item_id) or {}
    streak = rec.get("streak", 0) + 1
    score = min(100.0, (streak / 10) * 100)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    set_item(data, item_id, item_type, streak, score, last_practiced=now, last_score_updated=now)
    save(data, data_dir)
    return {"streak": streak, "score": score}


@router.post("/fail")
def record_fail(req: SuccessFailRequest) -> dict:
    """Record failed practice. Resets streak to 0."""
    _, data_dir, data = _get_context()
    set_item(data, req.item_id, req.item_type, 0, 0.0)
    save(data, data_dir)
    return {"streak": 0}


@router.post("/reset")
def reset_part(req: SuccessFailRequest) -> dict:
    """Reset part streak and score to 0 (manual reset)."""
    _, data_dir, data = _get_context()
    set_item(data, req.item_id, req.item_type, 0, 0.0)
    save(data, data_dir)
    return {"ok": True}
