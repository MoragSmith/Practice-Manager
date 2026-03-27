"""
Practice Manager - Core

Shared logic for desktop and web: config, data model, discovery, assets, decay.
No GUI or platform-specific code (except assets.open_file for desktop).
"""

from .config import (
    INSTRUMENTS,
    PART_LABELS,
    get_data_dir,
    get_ensemble_config,
    get_library_root,
)
from .data_model import (
    create_empty_state,
    create_item,
    get_item,
    load,
    save,
    set_item,
)
from .discovery import discover
from .assets import get_part_assets, get_set_assets, get_tune_assets
from .decay import apply_decay

__all__ = [
    "INSTRUMENTS",
    "PART_LABELS",
    "get_data_dir",
    "get_ensemble_config",
    "get_library_root",
    "create_empty_state",
    "create_item",
    "get_item",
    "load",
    "save",
    "set_item",
    "discover",
    "get_part_assets",
    "get_set_assets",
    "get_tune_assets",
    "apply_decay",
]
