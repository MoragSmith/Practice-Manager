"""Web API regression tests.

These tests use a tiny temporary OTPD Scores-style library instead of the real
Google Drive library. That keeps write endpoints safe to test repeatedly while
still exercising the same FastAPI routers, discovery logic, asset streaming,
and practice-status persistence used by the web app.
"""

import json
from pathlib import Path

from fastapi.testclient import TestClient

from src.practice_manager.web.main import app
from src.practice_manager.web.api import assets, library, practice, status


def _write_json(path: Path, data: dict) -> None:
    """Write JSON fixture data, creating the parent directory when needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")


def _make_library(tmp_path: Path) -> Path:
    """Create the smallest library shape that discovery and asset APIs expect."""
    root = tmp_path / "OTPD Scores"
    set_dir = root / "Section 1 - Test" / "Set 01 - Test Set"
    set_dir.mkdir(parents=True)
    (set_dir / "Set 01a - Test Tune.pdf").write_bytes(b"%PDF-1.4\n% test\n")
    (set_dir / "Set 01a - Test Tune_bass.pdf").write_bytes(b"%PDF-1.4\n% test\n")
    (set_dir / "Set 01a - Test Tune.wav").write_bytes(b"RIFF....WAVEfmt ")
    _write_json(
        root / "#Script Resources" / "data" / "practice_status.json",
        {
            "schema_version": 1,
            "last_updated": "2026-05-21T00:00:00Z",
            "decay_rate_percent_per_day": 1.0,
            "focus_instrument": "bass",
            "set_instruments": {},
            "focus_set_ids": [],
            "show_focus_only": False,
            "items": {},
        },
    )
    return root


def _patch_library_root(monkeypatch, root: Path) -> None:
    """Point every web router at the temporary library fixture.

    The API modules import `get_library_root` directly, so patching the core
    function alone would not affect already-imported router modules.
    """
    for module in (assets, library, practice, status):
        monkeypatch.setattr(module, "get_library_root", lambda: root)


def test_web_library_and_status_endpoints_use_configured_library(tmp_path, monkeypatch):
    root = _make_library(tmp_path)
    _patch_library_root(monkeypatch, root)
    client = TestClient(app)

    status_response = client.get("/api/status")
    assert status_response.status_code == 200
    assert status_response.json()["schema_version"] == 1

    library_response = client.get("/api/library")
    assert library_response.status_code == 200
    payload = library_response.json()
    assert payload["library_root"] == str(root)
    assert len(payload["sets"]) == 1
    assert payload["sets"][0]["set_id"] == "Section 1 - Test|Set 01 - Test Set"
    assert payload["sets"][0]["tunes"][0]["tune_name"] == "Set 01a - Test Tune"


def test_web_asset_endpoint_streams_pdf_and_rejects_path_escape(tmp_path, monkeypatch):
    root = _make_library(tmp_path)
    _patch_library_root(monkeypatch, root)
    client = TestClient(app)

    pdf_response = client.get(
        "/api/assets/pdf",
        params={"path": "Section 1 - Test/Set 01 - Test Set/Set 01a - Test Tune_bass.pdf"},
    )
    assert pdf_response.status_code == 200
    assert pdf_response.headers["content-type"].startswith("application/pdf")

    escape_response = client.get("/api/assets/pdf", params={"path": "../secret.pdf"})
    assert escape_response.status_code == 400


def test_web_practice_start_success_fail_reset_flow(tmp_path, monkeypatch):
    root = _make_library(tmp_path)
    _patch_library_root(monkeypatch, root)
    client = TestClient(app)

    start_response = client.post(
        "/api/practice/start",
        json={
            "item_type": "tune",
            "item_id": "Section 1 - Test|Set 01 - Test Set|Set 01a - Test Tune",
            "display_name": "Set 01a - Test Tune",
            "instrument": "bass",
            "set_id": "Section 1 - Test|Set 01 - Test Set",
            "set_path": "Section 1 - Test/Set 01 - Test Set",
            "tune_name": "Set 01a - Test Tune",
        },
    )
    assert start_response.status_code == 200
    assert start_response.json()["pdf_url"].endswith("Set%2001a%20-%20Test%20Tune_bass.pdf")
    assert start_response.json()["wav_url"].endswith("Set%2001a%20-%20Test%20Tune.wav")

    body = {
        "item_id": "Section 1 - Test|Set 01 - Test Set|Set 01a - Test Tune",
        "item_type": "tune",
    }
    success_response = client.post("/api/practice/success", json=body)
    assert success_response.status_code == 200
    assert success_response.json() == {"streak": 1, "score": 10.0}

    fail_response = client.post("/api/practice/fail", json=body)
    assert fail_response.status_code == 200
    assert fail_response.json() == {"streak": 0}

    reset_response = client.post("/api/practice/reset", json=body)
    assert reset_response.status_code == 200
    assert reset_response.json() == {"ok": True}
