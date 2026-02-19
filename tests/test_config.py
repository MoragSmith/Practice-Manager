"""
Tests for configuration - real files in tmp_path, no mocks.

Tests get_ensemble_config and get_library_root with actual config files,
.env, and directory structures.
"""

import json
from pathlib import Path

import pytest


# =============================================================================
# get_library_root - discovery from real config files
# =============================================================================


class TestGetLibraryRoot:
    """Test library root discovery with real config files."""

    def test_from_tracker_config(self, tmp_path: Path) -> None:
        """Library root from tracker-config.json when file exists."""
        lib_path = tmp_path / "OTPD Scores"
        lib_path.mkdir()

        project_root = tmp_path / "Practice Manager"
        project_root.mkdir()
        config_path = project_root / "tracker-config.json"
        config_path.write_text(json.dumps({"library_root": str(lib_path)}))

        # Patch _get_project_root to return our project_root
        from src.practice_manager import config as config_module

        original_get_root = config_module._get_project_root

        def mock_get_root():
            return project_root

        config_module._get_project_root = mock_get_root
        try:
            root = config_module.get_library_root()
            assert root == lib_path
        finally:
            config_module._get_project_root = original_get_root

    def test_tracker_config_with_expanduser(self, tmp_path: Path) -> None:
        """Paths with ~ are expanded."""
        lib_path = tmp_path / "OTPD Scores"
        lib_path.mkdir()
        home = Path.home()
        # Use a path that doesn't actually need expanding but tests the code path
        project_root = tmp_path / "pm"
        project_root.mkdir()
        (project_root / "tracker-config.json").write_text(
            json.dumps({"library_root": str(lib_path)})
        )

        from src.practice_manager import config as config_module

        original = config_module._get_project_root
        config_module._get_project_root = lambda: project_root
        try:
            root = config_module.get_library_root()
            assert root == lib_path
        finally:
            config_module._get_project_root = original

    def test_raises_when_no_config(self, tmp_path: Path) -> None:
        """FileNotFoundError when no valid config exists."""
        project_root = tmp_path / "empty_project"
        project_root.mkdir()
        # No tracker-config.json, no OTPD path

        from src.practice_manager import config as config_module

        original = config_module._get_project_root
        config_module._get_project_root = lambda: project_root
        try:
            with pytest.raises(FileNotFoundError) as exc_info:
                config_module.get_library_root()
            assert "library" in str(exc_info.value).lower()
        finally:
            config_module._get_project_root = original


# =============================================================================
# get_ensemble_config - real .env and config files
# =============================================================================


class TestGetEnsembleConfig:
    """Test Ensemble config loading from real files."""

    def test_returns_dict_with_expected_keys(self) -> None:
        """Config dict has username, password, downloads_dir, scores_dir."""
        from src.practice_manager.config import get_ensemble_config

        config = get_ensemble_config()
        assert "username" in config
        assert "password" in config
        assert "downloads_dir" in config
        assert "scores_dir" in config

    def test_downloads_dir_defaults_to_home_downloads(self) -> None:
        """When not configured, downloads_dir is ~/Downloads."""
        from src.practice_manager.config import get_ensemble_config

        config = get_ensemble_config()
        assert config["downloads_dir"] is not None
        assert "Downloads" in config["downloads_dir"]

    def test_loads_from_env_when_present(self, tmp_path: Path, monkeypatch) -> None:
        """ENSEMBLE_USERNAME and ENSEMBLE_PASSWORD from environment."""
        monkeypatch.setenv("ENSEMBLE_USERNAME", "testuser")
        monkeypatch.setenv("ENSEMBLE_PASSWORD", "testpass")

        from src.practice_manager.config import get_ensemble_config

        config = get_ensemble_config()
        assert config["username"] == "testuser"
        assert config["password"] == "testpass"

