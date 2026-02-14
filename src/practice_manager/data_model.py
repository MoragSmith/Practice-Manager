"""
Practice Manager - Data Model

Schema, loader/saver for practice_status.json with timestamped backups.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

SCHEMA_VERSION = 1
DEFAULT_DECAY_RATE = 1.0
DEFAULT_FOCUS_INSTRUMENT = "bass"


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def create_empty_state() -> Dict[str, Any]:
    """Create a fresh practice status structure."""
    return {
        "schema_version": SCHEMA_VERSION,
        "last_updated": _now_iso(),
        "decay_rate_percent_per_day": DEFAULT_DECAY_RATE,
        "focus_instrument": DEFAULT_FOCUS_INSTRUMENT,
        "focus_set_ids": [],
        "show_focus_only": False,
        "items": {},
    }


def create_item(
    item_type: str,
    streak: int = 0,
    score: float = 0.0,
    last_practiced: Optional[str] = None,
    last_score_updated: Optional[str] = None,
    missing: bool = False,
) -> Dict[str, Any]:
    """Create an item record for sets, tunes, or parts."""
    return {
        "type": item_type,
        "streak": streak,
        "score": score,
        "last_practiced": last_practiced,
        "last_score_updated": last_score_updated,
        "missing": missing,
    }


def _ensure_backup_dir(data_dir: Path) -> Path:
    """Ensure backups/ exists; return its path."""
    backup_dir = data_dir / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    return backup_dir


def _create_backup(json_path: Path, data_dir: Path) -> None:
    """Create timestamped backup before overwriting."""
    if not json_path.exists():
        return
    backup_dir = _ensure_backup_dir(data_dir)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    backup_name = f"practice_status_{timestamp}.json"
    backup_path = backup_dir / backup_name
    try:
        content = json_path.read_text(encoding="utf-8")
        backup_path.write_text(content, encoding="utf-8")
    except Exception as e:
        logger.warning("Failed to create backup: %s", e)


def load(data_dir: Path) -> Dict[str, Any]:
    """
    Load practice status from practice_status.json.

    Creates and returns an empty state if the file does not exist or is invalid.
    Normalizes schema_version, decay_rate, focus_instrument, etc. to defaults.

    Args:
        data_dir: Directory containing practice_status.json.

    Returns:
        Dict with schema_version, items, focus_set_ids, etc.
    """
    json_path = data_dir / "practice_status.json"
    if not json_path.exists():
        return create_empty_state()
    
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        logger.error("Invalid JSON in practice_status.json: %s", e)
        return create_empty_state()
    
    # Normalize schema version
    data.setdefault("schema_version", SCHEMA_VERSION)
    data.setdefault("decay_rate_percent_per_day", DEFAULT_DECAY_RATE)
    data.setdefault("focus_instrument", DEFAULT_FOCUS_INSTRUMENT)
    data.setdefault("focus_set_ids", [])
    data.setdefault("show_focus_only", False)
    data.setdefault("items", {})
    
    return data


def save(data: Dict[str, Any], data_dir: Path) -> None:
    """
    Save practice status to practice_status.json.

    Creates a timestamped backup in backups/ before overwriting.
    Updates last_updated and schema_version on the data dict.
    """
    json_path = data_dir / "practice_status.json"
    data_dir.mkdir(parents=True, exist_ok=True)
    
    data["last_updated"] = _now_iso()
    data["schema_version"] = SCHEMA_VERSION
    
    _create_backup(json_path, data_dir)
    
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def get_item(data: Dict[str, Any], item_id: str) -> Optional[Dict[str, Any]]:
    """Get item by ID."""
    return data.get("items", {}).get(item_id)


def set_item(
    data: Dict[str, Any],
    item_id: str,
    item_type: str,
    streak: int,
    score: float,
    last_practiced: Optional[str] = None,
    last_score_updated: Optional[str] = None,
    missing: bool = False,
) -> None:
    """Set or update an item."""
    if "items" not in data:
        data["items"] = {}
    data["items"][item_id] = create_item(
        item_type=item_type,
        streak=streak,
        score=score,
        last_practiced=last_practiced,
        last_score_updated=last_score_updated,
        missing=missing,
    )
