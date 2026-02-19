"""
Practice Manager - Configuration

Discovers library root from (in order):
1. OTPD Music Manager config/default.yaml or data/preferences.json (paths.scores_dir)
2. #Script Resources/config.json in library (otpd_scores_directory)
3. tracker-config.json in Practice Manager project (library_root)
"""

import json
from pathlib import Path
from typing import Optional

# Default instruments from OTPD
INSTRUMENTS = ["bagpipes", "seconds", "bass", "snare", "tenor"]

# Part grouping labels (order: phrase, line, part)
PART_LABELS = ["phrase", "line", "part"]


def _get_project_root() -> Path:
    """Return Practice Manager project root."""
    return Path(__file__).resolve().parent.parent.parent


def _load_yaml_safe(path: Path) -> Optional[dict]:
    """Load YAML if pyyaml available."""
    try:
        import yaml
        with open(path, "r") as f:
            return yaml.safe_load(f)
    except Exception:
        return None


def _get_from_otpd_manager() -> Optional[Path]:
    """Try to get scores_dir from OTPD Music Manager."""
    project_root = _get_project_root()
    tracker_config_path = project_root / "tracker-config.json"
    
    otpd_path: Optional[Path] = None
    if tracker_config_path.exists():
        try:
            with open(tracker_config_path) as f:
                data = json.load(f)
                p = data.get("otpd_manager_path")
                if p:
                    otpd_path = Path(p).expanduser()
        except Exception:
            pass
    
    if not otpd_path or not otpd_path.exists():
        return None
    
    # Try preferences.json first (user overrides)
    prefs_path = otpd_path / "data" / "preferences.json"
    if prefs_path.exists():
        try:
            with open(prefs_path) as f:
                data = json.load(f)
                scores_dir = data.get("paths", {}).get("scores_dir")
                if scores_dir:
                    p = Path(scores_dir).expanduser()
                    if p.exists():
                        return p
        except Exception:
            pass
    
    # Try config/default.yaml
    config_path = otpd_path / "config" / "default.yaml"
    if config_path.exists():
        data = _load_yaml_safe(config_path)
        if data:
            scores_dir = data.get("paths", {}).get("scores_dir")
            if scores_dir:
                p = Path(scores_dir).expanduser()
                if p.exists():
                    return p
    
    return None


def _get_from_script_resources(candidate_root: Path) -> Optional[Path]:
    """
    Check #Script Resources/config.json for otpd_scores_directory.

    Used to override the library root when the config inside the library
    points to a different location (e.g. shared library path).
    """
    config_path = candidate_root / "#Script Resources" / "config.json"
    if not config_path.exists():
        return None
    try:
        with open(config_path) as f:
            data = json.load(f)
            dir_path = data.get("otpd_scores_directory")
            if dir_path:
                p = Path(dir_path).expanduser()
                if p.exists():
                    return p
    except Exception:
        pass
    return None


def _get_from_tracker_config() -> Optional[Path]:
    """Get library_root from tracker-config.json."""
    project_root = _get_project_root()
    config_path = project_root / "tracker-config.json"
    if not config_path.exists():
        return None
    try:
        with open(config_path) as f:
            data = json.load(f)
            lib = data.get("library_root")
            if lib:
                p = Path(lib).expanduser()
                if p.exists():
                    return p
    except Exception:
        pass
    return None


def get_library_root() -> Path:
    """
    Discover and return the OTPD Scores library root.

    Tries, in order:
    1. OTPD Music Manager's paths.scores_dir (preferences.json or config/default.yaml)
    2. #Script Resources/config.json otpd_scores_directory (if present in candidate root)
    3. tracker-config.json library_root in project directory

    Returns:
        Path: The resolved OTPD Scores library root directory.

    Raises:
        FileNotFoundError: If no valid library root can be found.
    """
    root = _get_from_otpd_manager()
    if root is not None:
        # Optionally override from Script Resources
        override = _get_from_script_resources(root)
        if override is not None:
            return override
        return root
    
    root = _get_from_tracker_config()
    if root is not None:
        return root
    
    raise FileNotFoundError(
        "Could not discover OTPD Scores library. "
        "Create tracker-config.json with 'library_root' and optionally 'otpd_manager_path'."
    )


def get_ensemble_config() -> dict:
    """
    Load Ensemble credentials and paths from OTPD Music Manager config.

    Returns dict with username, password, downloads_dir, scores_dir.
    Username/password from: .env (OTPD or Practice Manager), env vars, or config.
    """
    import os

    project_root = _get_project_root()
    tracker_config_path = project_root / "tracker-config.json"
    otpd_path: Optional[Path] = None
    if tracker_config_path.exists():
        try:
            with open(tracker_config_path) as f:
                data = json.load(f)
                p = data.get("otpd_manager_path")
                if p:
                    otpd_path = Path(p).expanduser()
        except Exception:
            pass

    # Load .env from OTPD Music Manager or Practice Manager (for ENSEMBLE_USERNAME/PASSWORD)
    try:
        from dotenv import load_dotenv
        if otpd_path and otpd_path.exists():
            load_dotenv(otpd_path / ".env")
        load_dotenv(project_root / ".env")
    except ImportError:
        pass

    result: dict = {
        "username": os.environ.get("ENSEMBLE_USERNAME"),
        "password": os.environ.get("ENSEMBLE_PASSWORD"),
        "downloads_dir": None,
        "scores_dir": None,
    }

    if otpd_path and otpd_path.exists():
        config_path = otpd_path / "config" / "default.yaml"
        if config_path.exists():
            data = _load_yaml_safe(config_path)
            if data:
                paths = data.get("paths", {})
                if paths.get("downloads_dir"):
                    result["downloads_dir"] = str(Path(paths["downloads_dir"]).expanduser())
                if paths.get("scores_dir"):
                    result["scores_dir"] = str(Path(paths["scores_dir"]).expanduser())
                ensemble = data.get("ensemble", {})
                if not result["username"] and ensemble.get("username"):
                    result["username"] = ensemble["username"]
                if not result["password"] and ensemble.get("password"):
                    result["password"] = ensemble["password"]

    if result["downloads_dir"] is None:
        result["downloads_dir"] = str(Path.home() / "Downloads")
    if result["scores_dir"] is None:
        try:
            result["scores_dir"] = str(get_library_root())
        except FileNotFoundError:
            pass

    return result


def get_data_dir(library_root: Optional[Path] = None) -> Path:
    """
    Return the directory for practice_status.json and related data files.

    Uses the same location as otpd_music_book_structure.json:
    {library_root}/#Script Resources/data

    Args:
        library_root: OTPD Scores library root. If None, uses get_library_root().

    Returns:
        Path: The data directory (e.g. .../OTPD Scores/#Script Resources/data).
    """
    if library_root is None:
        library_root = get_library_root()
    return library_root / "#Script Resources" / "data"
