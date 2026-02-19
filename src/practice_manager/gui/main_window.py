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

from ..config import INSTRUMENTS, PART_LABELS
from ..data_model import get_item, set_item
from ..discovery import discover


class MainWindow(QMainWindow):
    """
    Main application window with sets list and details pane.

    Left pane: instrument selector, decay rate, focus filter, sets list.
    Right pane: selected set details (Set/Tunes/Parts) with Start Session and Reset.
    """

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
        self._reset_part_cb = on_reset_part
        
        self._focus_only = self._data.get("show_focus_only", False)
        self._discovered: List[Dict[str, Any]] = []
        self._selected_set: Optional[Dict[str, Any]] = None
        
        self.setWindowTitle("Practice Manager")
        self.setMinimumSize(1000, 650)
        self.resize(1200, 800)
        
        self._build_ui()
        self._refresh_discovery()
        self._refresh_sets_list()
    
    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        inst_row = QHBoxLayout()
        inst_row.addWidget(QLabel("Decay %/day:"))
        self.decay_spin = QDoubleSpinBox()
        self.decay_spin.setRange(0.0, 10.0)
        self.decay_spin.setSingleStep(0.1)
        self.decay_spin.setValue(self._data.get("decay_rate_percent_per_day", 1.0))
        self.decay_spin.valueChanged.connect(self._on_decay_changed)
        inst_row.addWidget(self.decay_spin)
        self.download_parts_btn = QPushButton("Download Parts")
        self.download_parts_btn.setToolTip("Download all parts from Ensemble Parts workspace (WAV + PDFs)")
        self.download_parts_btn.clicked.connect(self._on_download_parts)
        inst_row.addWidget(self.download_parts_btn)
        layout.addLayout(inst_row)
        
        splitter = QSplitter(Qt.Horizontal)
        
        # Left: sets list
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.addWidget(QLabel("Sets"))
        
        self.focus_filter = QCheckBox("Show focus only")
        self.focus_filter.setChecked(self._focus_only)
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
        splitter.setSizes([350, 800])
        
        layout.addWidget(splitter)
    
    def _on_decay_changed(self, value: float) -> None:
        self._data["decay_rate_percent_per_day"] = value
        self._on_save()
    
    def _on_focus_filter_toggled(self, checked: bool) -> None:
        self._focus_only = checked
        self._data["show_focus_only"] = checked
        self._on_save()
        self._refresh_sets_list()
    
    def _refresh_discovery(self) -> None:
        items = self._data.get("items", {})
        self._discovered = discover(self.library_root, self.data_dir, items)
        
        # Merge new tune and part items (sets are for organization only, no practice tracking)
        for set_rec in self._discovered:
            set_id = set_rec["set_id"]
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
            is_focus = set_id in focus_ids
            
            # Summary from tunes and parts (practice/mastery apply to these, not sets)
            tune_ids = [t["tune_id"] for t in set_rec.get("tunes", [])]
            part_ids = [p.get("part_full_id") or f"{set_id}|Parts|{p['part_id']}" for p in set_rec.get("parts", [])]
            practiced = tune_ids + part_ids
            mastered = sum(1 for iid in practiced if (items.get(iid) or {}).get("score", 0) >= 100)
            total = len(practiced)
            summary = f"{mastered}/{total}" if total else "—"
            
            label = set_rec["set_folder_name"]
            if is_focus:
                label = "★ " + label
            label += f"  [{summary}]"
            
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
        set_instruments = self._data.get("set_instruments", {})
        default_inst = self._data.get("focus_instrument", "bass")
        instrument = set_instruments.get(set_id, default_inst)
        
        # Set group: organization only (practice/mastery apply to tunes and parts)
        set_group = QGroupBox("Set")
        set_layout = QVBoxLayout(set_group)
        set_layout.addWidget(QLabel("Practice and mastery apply to individual tunes and parts below."))
        
        # Per-set instrument selector
        inst_row = QHBoxLayout()
        inst_row.addWidget(QLabel("Instrument for this set:"))
        inst_combo = QComboBox()
        inst_combo.addItems(INSTRUMENTS)
        idx = inst_combo.findText(instrument)
        if idx >= 0:
            inst_combo.setCurrentIndex(idx)
        def _on_set_instrument_changed(text: str) -> None:
            si = dict(self._data.get("set_instruments", {}))
            si[set_id] = text
            self._data["set_instruments"] = si
            self._on_save()
        inst_combo.currentTextChanged.connect(_on_set_instrument_changed)
        inst_row.addWidget(inst_combo)
        set_layout.addLayout(inst_row)
        
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
                lambda checked=False, tid=tune_id, tname=tune_name, combo=inst_combo: self._start_session("tune", tid, tname, combo.currentText(), {
                    "set_path": set_path,
                    "set_id": set_id,
                    "tune_name": tname,
                })
            )
            row.addWidget(btn)
            tunes_layout.addLayout(row)
        self.details_layout.addWidget(tunes_group)
        
        # Parts (if any): group by tune, then by phrase/line/part
        parts_list = set_rec.get("parts", [])
        if parts_list:
            parts_group = QGroupBox("Parts")
            parts_layout = QVBoxLayout(parts_group)
            # Group parts by tune_id, then by label (phrase, line, part)
            by_tune: Dict[str, Dict[str, list]] = {}
            for p in parts_list:
                tid = p.get("tune_id") or ""
                tname = p.get("tune_name") or "Parts"
                lbl = p.get("label") or "part"
                if tid not in by_tune:
                    by_tune[tid] = {"tune_name": tname, "phrase": [], "line": [], "part": []}
                if lbl in by_tune[tid]:
                    by_tune[tid][lbl].append(p)
            # Order tunes: use set's tune order; unmapped parts at end
            tune_order = [t["tune_id"] for t in set_rec.get("tunes", [])]
            ordered_tune_ids = []
            for tid in tune_order:
                if tid in by_tune and tid not in ordered_tune_ids:
                    ordered_tune_ids.append(tid)
            for tid in by_tune:
                if tid not in ordered_tune_ids:
                    ordered_tune_ids.append(tid)
            for tid in ordered_tune_ids:
                if tid not in by_tune:
                    continue
                tdata = by_tune[tid]
                tname = tdata["tune_name"]
                tune_label = QLabel(f"<b>{tname}</b>")
                parts_layout.addWidget(tune_label)
                for lbl in PART_LABELS:
                    plist = tdata.get(lbl, [])
                    if not plist:
                        continue
                    for p in plist:
                        pid = p.get("part_full_id") or f"{set_id}|Parts|{p['part_id']}"
                        rec = get_item(self._data, pid) or {}
                        row = QHBoxLayout()
                        display = p.get("short_label") or p["part_id"]
                        row.addWidget(QLabel(f"  {display} ({p['label']}): {rec.get('score', 0):.0f}% | {rec.get('streak', 0)}"))
                        start_btn = QPushButton("Start Session")
                        start_btn.clicked.connect(
                            lambda checked=False, part_id=pid, prec=p, combo=inst_combo: self._start_session("part", part_id, p.get("short_label") or p["part_id"], combo.currentText(), {
                                "part_record": prec,
                                "set_id": set_id,
                            })
                        )
                        reset_btn = QPushButton("Reset")
                        reset_btn.clicked.connect(lambda checked=False, part_id=pid: self._handle_reset_part(part_id))
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
    
    def _on_download_parts(self) -> None:
        """Open Download Parts dialog and start workflow."""
        from .download_parts_dialog import DownloadPartsDialog

        dlg = DownloadPartsDialog(self)
        dlg.start()
        dlg.exec()

    def _handle_reset_part(self, part_id: str) -> None:
        """Reset part streak and score to 0; delegate to main app callback."""
        self._reset_part_cb(part_id)
    
    def refresh_all(self) -> None:
        """Refresh discovery and lists (e.g. after session or part reset)."""
        self._refresh_discovery()
        self._refresh_sets_list()
        if self._selected_set:
            self._refresh_details()
    
    def get_data(self) -> Dict[str, Any]:
        return self._data
