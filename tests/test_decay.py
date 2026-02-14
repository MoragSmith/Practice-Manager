"""Tests for decay calculation."""

from datetime import datetime, timezone, timedelta

import pytest

from src.practice_manager.decay import apply_decay, _parse_iso


def test_parse_iso() -> None:
    s = "2025-02-12T10:00:00Z"
    dt = _parse_iso(s)
    assert dt.year == 2025
    assert dt.month == 2
    assert dt.day == 12


def test_decay_reduces_score() -> None:
    data = {
        "items": {
            "tune1": {
                "type": "tune",
                "streak": 5,
                "score": 50.0,
                "last_score_updated": (datetime.now(timezone.utc) - timedelta(days=5)).strftime(
                    "%Y-%m-%dT%H:%M:%SZ"
                ),
                "missing": False,
            },
        },
        "decay_rate_percent_per_day": 1.0,
    }
    apply_decay(data)
    # 5 days * 1% = 5% decay: 50 - 5 = 45
    assert data["items"]["tune1"]["score"] == 45.0


def test_decay_does_not_affect_parts() -> None:
    data = {
        "items": {
            "part1": {
                "type": "part",
                "streak": 3,
                "score": 30.0,
                "last_score_updated": "2025-02-01T10:00:00Z",
                "missing": False,
            },
        },
        "decay_rate_percent_per_day": 1.0,
    }
    apply_decay(data)
    assert data["items"]["part1"]["score"] == 30.0


def test_decay_clamps_to_zero() -> None:
    data = {
        "items": {
            "tune1": {
                "type": "tune",
                "streak": 2,
                "score": 20.0,
                "last_score_updated": (datetime.now(timezone.utc) - timedelta(days=30)).strftime(
                    "%Y-%m-%dT%H:%M:%SZ"
                ),
                "missing": False,
            },
        },
        "decay_rate_percent_per_day": 1.0,
    }
    apply_decay(data)
    assert data["items"]["tune1"]["score"] == 0.0


def test_decay_no_last_updated_skipped() -> None:
    data = {
        "items": {
            "tune1": {
                "type": "tune",
                "streak": 1,
                "score": 10.0,
                "last_score_updated": None,
                "missing": False,
            },
        },
    }
    apply_decay(data)
    assert data["items"]["tune1"]["score"] == 10.0


def test_decay_does_not_affect_sets() -> None:
    """Sets are for organization only; they do not decay."""
    data = {
        "items": {
            "Section1|Set01": {
                "type": "set",
                "streak": 5,
                "score": 80.0,
                "last_score_updated": (datetime.now(timezone.utc) - timedelta(days=10)).strftime(
                    "%Y-%m-%dT%H:%M:%SZ"
                ),
                "missing": False,
            },
        },
        "decay_rate_percent_per_day": 1.0,
    }
    apply_decay(data)
    assert data["items"]["Section1|Set01"]["score"] == 80.0
