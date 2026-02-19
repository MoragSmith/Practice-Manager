"""
E2E tests for Ensemble Parts download workflow.

Runs against the real Ensemble site. Uses credentials from get_ensemble_config()
(.env, OTPD config, or ENSEMBLE_USERNAME/ENSEMBLE_PASSWORD env vars).
Skipped if library root or Ensemble credentials are not configured.
"""

from pathlib import Path

import pytest

from src.practice_manager.config import get_ensemble_config, get_library_root
from src.practice_manager.ensemble.download_parts_workflow import run_download_parts


pytestmark = pytest.mark.asyncio


def _can_run_integration() -> bool:
    """True if library and Ensemble credentials are configured."""
    try:
        get_library_root()
    except FileNotFoundError:
        return False
    cfg = get_ensemble_config()
    return bool(cfg.get("username") and cfg.get("password"))


async def _run_workflow(
    downloads_dir: Path,
    scores_dir: Path,
    max_parts: int = 1,
) -> dict:
    """Run download parts workflow against real Ensemble."""
    return await run_download_parts(
        headless=True,
        downloads_dir=downloads_dir,
        scores_dir=scores_dir,
        max_parts=max_parts,
    )


@pytest.mark.skipif(not _can_run_integration(), reason="Library root or Ensemble credentials not configured")
class TestEnsemblePartsE2E:
    """E2E tests against real Ensemble site."""

    async def test_login_navigate_parts_download_one(
        self,
        tmp_path: Path,
    ) -> None:
        """
        Log in to Ensemble, navigate to Parts, download first part.
        Full flow: real site, real auth, real downloads.
        """
        library_root = get_library_root()
        downloads_dir = tmp_path / "downloads"
        scores_dir = library_root

        result = await _run_workflow(
            downloads_dir=downloads_dir,
            scores_dir=scores_dir,
            max_parts=1,
        )

        assert result.get("error") is None, result.get("error")
        assert result["success"] >= 1, "Expected at least one part downloaded from Ensemble"
        assert result["organized"] >= 1, (
            "Expected files organized. If failed: ensure library has a set folder "
            "matching the downloaded part prefix (e.g. Competition 08 - ...)."
        )
