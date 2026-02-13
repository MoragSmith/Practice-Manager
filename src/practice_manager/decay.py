"""
Practice Manager - Score decay

Apply decay on launch: sets and tunes only, based on last_score_updated.
Parts do not decay.
"""

from datetime import datetime, timezone
from typing import Any, Dict


def _parse_iso(s: str) -> datetime:
    """Parse ISO timestamp to timezone-aware datetime."""
    if not s:
        return datetime.now(timezone.utc)
    dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def apply_decay(data: Dict[str, Any]) -> None:
    """
    Apply decay to all sets and tunes in-place.
    score = max(0, score - decay_rate * days_since_last_score_updated)
    Update last_score_updated to now after applying.
    """
    now = datetime.now(timezone.utc)
    # 1% per day = subtract 1 percentage point per day (e.g. 50 -> 49 after 1 day)
    rate = data.get("decay_rate_percent_per_day", 1.0)
    items = data.get("items", {})
    
    for item_id, rec in items.items():
        if rec.get("type") == "part":
            continue  # Parts do not decay
        
        last_updated = rec.get("last_score_updated")
        if not last_updated:
            continue
        
        try:
            last_dt = _parse_iso(last_updated)
        except Exception:
            continue
        
        delta = now - last_dt
        days = max(0, delta.total_seconds() / 86400)
        if days <= 0:
            continue
        
        score = rec.get("score", 0.0)
        decay_amount = rate * days  # percentage points
        decayed = max(0.0, score - decay_amount)
        rec["score"] = round(decayed, 1)
        rec["last_score_updated"] = now.strftime("%Y-%m-%dT%H:%M:%SZ")
