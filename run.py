"""
Practice Manager - Entry Point

Launches the GUI, performs discovery, on-launch decay, load/save JSON with backups.
"""

import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

from PySide6.QtWidgets import QApplication, QMessageBox

from src.practice_manager.config import get_library_root, get_data_dir
from src.practice_manager.data_model import get_item, load, save, set_item
from src.practice_manager.decay import apply_decay
from src.practice_manager.assets import get_tune_assets, get_part_assets
from src.practice_manager.gui.main_window import MainWindow
from src.practice_manager.gui.session_window import SessionWindow


# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


def main() -> None:
    """Launch Practice Manager: discover library, load data, apply decay, show GUI."""
    app = QApplication(sys.argv)
    app.setApplicationName("Practice Manager")

    # Discover library (OTPD Manager config, Script Resources, or tracker-config.json)
    try:
        library_root = get_library_root()
    except FileNotFoundError as e:
        logger.error("%s", e)
        sys.exit(1)
    
    data_dir = get_data_dir(library_root)
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # Load data
    data = load(data_dir)
    
    # Apply decay on launch
    apply_decay(data)
    save(data, data_dir)
    
    def do_save() -> None:
        save(data, data_dir)
    
    def do_start_session(
        item_type: str,
        item_id: str,
        display_name: str,
        instrument: str,
        context: dict,
    ) -> None:
        """Open PDF/WAV, persist focus_instrument, reset streak to 0, show SessionWindow."""
        logger.info("Starting session: %s %s", item_type, display_name)
        pdf_path = None
        wav_path = None

        if item_type == "tune":
            set_path = context.get("set_path")
            tune_name = context.get("tune_name")
            if set_path and tune_name:
                pdf_path, wav_path = get_tune_assets(set_path, tune_name, instrument)
        elif item_type == "part":
            part_record = context.get("part_record")
            if part_record:
                pdf_path, wav_path = get_part_assets(part_record, instrument)
        
        # Persist instrument for this set (and default for new sets)
        set_id = context.get("set_id")
        if set_id:
            si = dict(data.get("set_instruments", {}))
            si[set_id] = instrument
            data["set_instruments"] = si
        data["focus_instrument"] = instrument  # default for sets without override
        do_save()
        
        # Parent context for display
        if "|" in item_id:
            parts = item_id.split("|")
            if item_type == "tune":
                parent_context = " | ".join(parts[:2]) if len(parts) >= 2 else item_id
            else:
                parent_context = " | ".join(parts[:2]) if len(parts) >= 2 else item_id
        else:
            parent_context = item_id
        
        # Reset streak to 0 when starting a new session
        set_item(data, item_id, item_type, 0, 0.0)
        do_save()
        streak = 0
        
        def on_success() -> None:
            nonlocal streak
            new_streak = streak + 1
            score = min(100.0, (new_streak / 10) * 100)
            now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            set_item(
                data,
                item_id,
                item_type,
                new_streak,
                score,
                last_practiced=now,
                last_score_updated=now,
            )
            do_save()
            streak = new_streak
            if sw:
                sw.refresh()
            if main_win:
                main_win.refresh_all()
        
        def on_fail() -> None:
            nonlocal streak
            set_item(data, item_id, item_type, 0, 0.0)
            do_save()
            streak = 0
            if sw:
                sw.refresh()
            if main_win:
                main_win.refresh_all()
        
        def get_streak() -> int:
            r = get_item(data, item_id) or {}
            return r.get("streak", 0)
        
        try:
            sw = SessionWindow(
                item_type=item_type,
                item_id=item_id,
                display_name=display_name,
                parent_context=parent_context,
                initial_streak=streak,
                pdf_path=pdf_path,
                wav_path=wav_path,
                on_success=on_success,
                on_fail=on_fail,
                get_streak=get_streak,
            )
            sw.show()
            sw.raise_()
            sw.activateWindow()
        except Exception as e:
            logger.exception("Failed to open session window")
            QMessageBox.critical(
                main_win,
                "Session Error",
                f"Could not open practice session:\n{e}",
            )
    
    def do_reset_part(part_id: str) -> None:
        set_item(data, part_id, "part", 0, 0.0)
        do_save()
        # Refresh main window
        if main_win:
            main_win.refresh_all()
    
    main_win = MainWindow(
        library_root=library_root,
        data_dir=data_dir,
        data=data,
        on_save=do_save,
        on_start_session=do_start_session,
        on_reset_part=do_reset_part,
    )
    main_win.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
