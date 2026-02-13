"""
Practice Manager - Main Window

Left/right layout: sets list (with focus toggle, filter) | details pane (tunes, parts).
"""

from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QPushButton,
    QScrollArea,
    QSplitter,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtCore import Qt

from ..config import INSTRUMENTS
from ..data_model import get_item, set_item
from ..discovery import discover


class MainWindow(QMainWindow):
    """Main application window with sets list and details pane."""

    def __init__(
        self,
        library_root: Path,
        data_dir: Path,
        data: Dict[str, Any],
        on_save: Callable[[], None],
        on_start_session: Callable[[str, str, str, str, Dict[str, Any]], None],
        on_reset_part: Callable[[str], None],
    ):
        super().__init__()
        self.library_root = library_root
        self.data_dir = data_dir
        self._data = data
        self._on_save = on_save
        self._on_start_session = on_start_session
        self._on_reset_part = on_reset_part
        
        self._focus_only = False
        self._discovered: List[Dict[str, Any]] = []
        self._selected_set: Optional[Dict[str, Any]] = None
        
        self.setWindowTitle("Practice Manager")
        self.setMinimumSize(800, 500)
        self.resize(1000, 600)
        
        self._build_ui()
        self._refresh_discovery()
        self._refresh_sets_list()
    
    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        # Instrument selector (global, for session start)
        inst_row = QHBoxLayout()
        inst_row.addWidget(QLabel("Focus instrument:"))
        self.instrument_combo = QComboBox()
        self.instrument_combo.addItems(INSTRUMENTS)
        current = self._data.get("focus_instrument", "bass")
        idx = self.instrument_combo.findText(current)
        if idx >= 0:
            self.instrument_combo.setCurrentIndex(idx)
        self.instrument_combo.currentTextChanged.connect(self._on_instrument_changed)
        inst_row.addWidget(self.instrument_combo)
        inst_row.addWidget(QLabel("Decay %/day:"))
        self.decay_spin = QDoubleSpinBox()
        self.decay_spin.setRange(0.0, 10.0)
        self.decay_spin.setSingleStep(0.1)
        self.decay_spin.setValue(self._data.get("decay_rate_percent_per_day", 1.0))
        self.decay_spin.valueChanged.connect(self._on_decay_changed)
        inst_row.addWidget(self.decay_spin)
        layout.addLayout(inst_row)
        
        splitter = QSplitter(Qt.Horizontal)
        
        # Left: sets list
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.addWidget(QLabel("Sets"))
        
        self.focus_filter = QCheckBox("Show focus only")
        self.focus_filter.toggled.connect(self._on_focus_filter_toggled)
        left_layout.addWidget(self.focus_filter)
        
        self.sets_list = QListWidget()
        self.sets_list.currentItemChanged.connect(self._on_set_selected)
        left_layout.addWidget(self.sets_list)
        
        splitter.addWidget(left)
        
        # Right: details
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.addWidget(QLabel("Set details"))
        
        self.details_scroll = QScrollArea()
        self.details_scroll.setWidgetResizable(True)
        self.details_content = QWidget()
        self.details_layout = QVBoxLayout(self.details_content)
        self.details_scroll.setWidget(self.details_content)
        right_layout.addWidget(self.details_scroll)
        
        splitter.addWidget(right)
        splitter.setSizes([300, 600])
        
        layout.addWidget(splitter)
    
    def _on_instrument_changed(self, text: str) -> None:
        self._data["focus_instrument"] = text
        self._on_save()
    
    def _on_decay_changed(self, value: float) -> None:
        self._data["decay_rate_percent_per_day"] = value
        self._on_save()
    
    def _on_focus_filter_toggled(self, checked: bool) -> None:
        self._focus_only = checked
        self._refresh_sets_list()
    
    def _refresh_discovery(self) -> None:
        items = self._data.get("items", {})
        self._discovered = discover(self.library_root, self.data_dir, items)
        
        # Merge new items into data
        for set_rec in self._discovered:
            set_id = set_rec["set_id"]
            if set_id not in items:
                set_item(self._data, set_id, "set", 0, 0.0)
            for t in set_rec.get("tunes", []):
                tid = t["tune_id"]
                if tid not in items:
                    set_item(self._data, tid, "tune", 0, 0.0)
            for p in set_rec.get("parts", []):
                pid = p.get("part_full_id") or f"{set_id}|Parts|{p['part_id']}"
                if pid not in items:
                    set_item(self._data, pid, "part", 0, 0.0)
    
    def _refresh_sets_list(self) -> None:
        self.sets_list.clear()
        focus_ids = set(self._data.get("focus_set_ids", []))
        items = self._data.get("items", {})
        
        for set_rec in self._discovered:
            set_id = set_rec["set_id"]
            if self._focus_only and set_id not in focus_ids:
                continue
            rec = get_item(self._data, set_id) or {}
            streak = rec.get("streak", 0)
            score = rec.get("score", 0.0)
            missing = rec.get("missing", False)
            is_focus = set_id in focus_ids
            
            label = set_rec["set_folder_name"]
            if is_focus:
                label = "★ " + label
            label += f"  [{score:.0f}% | {streak}]"
            if missing:
                label += " (missing)"
            
            item = QListWidgetItem(label)
            item.setData(Qt.UserRole, set_rec)
            self.sets_list.addItem(item)
    
    def _on_set_selected(self, current: Optional[QListWidgetItem], previous: Optional[QListWidgetItem]) -> None:
        if not current:
            self._selected_set = None
            self._refresh_details()
            return
        self._selected_set = current.data(Qt.UserRole)
        self._refresh_details()
    
    def _refresh_details(self) -> None:
        # Clear
        while self.details_layout.count():
            child = self.details_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        if not self._selected_set:
            return
        
        set_rec = self._selected_set
        set_id = set_rec["set_id"]
        set_path = set_rec["set_path"]
        items = self._data.get("items", {})
        instrument = self._data.get("focus_instrument", "bass")
        
        # Set-level Start Session
        set_group = QGroupBox("Set")
        set_layout = QVBoxLayout(set_group)
        set_rec_item = get_item(self._data, set_id) or {}
        set_layout.addWidget(QLabel(f"Score: {set_rec_item.get('score', 0):.0f}% | Streak: {set_rec_item.get('streak', 0)}"))
        tune_names = [t["tune_name"] for t in set_rec.get("tunes", [])]
        start_set_btn = QPushButton("Start Session")
        start_set_btn.clicked.connect(
            lambda: self._start_session("set", set_id, set_rec["set_folder_name"], self.instrument_combo.currentText(), {
                "set_path": set_path,
                "tune_names": tune_names,
            })
        )
        set_layout.addWidget(start_set_btn)
        
        # Focus toggle
        focus_ids = list(self._data.get("focus_set_ids", []))
        focus_cb = QCheckBox("Focus set")
        focus_cb.setChecked(set_id in focus_ids)
        def _toggle_focus(checked: bool) -> None:
            if checked and set_id not in focus_ids:
                focus_ids.append(set_id)
            elif not checked and set_id in focus_ids:
                focus_ids.remove(set_id)
            self._data["focus_set_ids"] = focus_ids
            self._on_save()
            self._refresh_sets_list()
        focus_cb.toggled.connect(_toggle_focus)
        set_layout.addWidget(focus_cb)
        
        self.details_layout.addWidget(set_group)
        
        # Tunes
        tunes_group = QGroupBox("Tunes")
        tunes_layout = QVBoxLayout(tunes_group)
        for t in set_rec.get("tunes", []):
            tune_id = t["tune_id"]
            tune_name = t["tune_name"]
            rec = get_item(self._data, tune_id) or {}
            row = QHBoxLayout()
            row.addWidget(QLabel(f"{tune_name}: {rec.get('score', 0):.0f}% | {rec.get('streak', 0)}"))
            btn = QPushButton("Start Session")
            btn.clicked.connect(
                lambda checked=False, tid=tune_id, tname=tune_name: self._start_session("tune", tid, tname, self.instrument_combo.currentText(), {
                    "set_path": set_path,
                    "tune_name": tname,
                })
            )
            row.addWidget(btn)
            tunes_layout.addLayout(row)
        self.details_layout.addWidget(tunes_group)
        
        # Parts (if any)
        parts_list = set_rec.get("parts", [])
        if parts_list:
            parts_group = QGroupBox("Parts")
            parts_layout = QVBoxLayout(parts_group)
            for p in parts_list:
                pid = p.get("part_full_id") or f"{set_id}|Parts|{p['part_id']}"
                rec = get_item(self._data, pid) or {}
                row = QHBoxLayout()
                row.addWidget(QLabel(f"{p['part_id']} ({p['label']}): {rec.get('score', 0):.0f}% | {rec.get('streak', 0)}"))
                start_btn = QPushButton("Start Session")
                start_btn.clicked.connect(
                    lambda checked=False, part_id=pid, prec=p: self._start_session("part", part_id, p["part_id"], self.instrument_combo.currentText(), {
                        "part_record": prec,
                    })
                )
                reset_btn = QPushButton("Reset")
                reset_btn.clicked.connect(lambda checked=False, part_id=pid: self._on_reset_part(part_id))
                row.addWidget(start_btn)
                row.addWidget(reset_btn)
                parts_layout.addLayout(row)
            self.details_layout.addWidget(parts_group)
        
        self.details_layout.addStretch()
    
    def _start_session(
        self,
        item_type: str,
        item_id: str,
        display_name: str,
        instrument: str,
        context: Dict[str, Any],
    ) -> None:
        self._on_start_session(item_type, item_id, display_name, instrument, context)
    
    def _on_reset_part(self, part_id: str) -> None:
        self._on_reset_part(part_id)
    
    def refresh_all(self) -> None:
        """Refresh discovery and lists (e.g. after session or part reset)."""
        self._refresh_discovery()
        self._refresh_sets_list()
        if self._selected_set:
            self._refresh_details()
    
    def get_data(self) -> Dict[str, Any]:
        return self._data
