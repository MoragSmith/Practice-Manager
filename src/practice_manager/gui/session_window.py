"""
Practice Manager - Practice Session Window

Small dialog with item name, streak display, Success/Fail/End Session buttons.
"""

from typing import Any, Callable, Dict, Optional

from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication


class SessionWindow(QDialog):
    """
    Practice session dialog (stays on top, bottom-right of screen).

    Success: increment streak, score = (streak/10)*100 capped at 100.
    Fail: streak=0, score=0.
    End Session: close (state is persisted on each Success/Fail press).
    """

    def __init__(
        self,
        item_type: str,
        item_id: str,
        display_name: str,
        parent_context: str,
        initial_streak: int,
        on_success: Callable[[], None],
        on_fail: Callable[[], None],
        get_streak: Callable[[], int],
    ):
        super().__init__()
        self._item_id = item_id
        self._on_success = on_success
        self._on_fail = on_fail
        self._get_streak = get_streak
        
        self.setWindowTitle(f"Practice Session - {display_name}")
        self.setModal(False)
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        self.setMinimumSize(420, 200)
        self.resize(450, 220)
        # Tile to lower-right quadrant (bottom-right of screen)
        screen = QGuiApplication.primaryScreen().availableGeometry()
        w, h = 450, 220
        mid_x = screen.x() + screen.width() // 2
        self.move(mid_x + 20, screen.y() + screen.height() - h - 80)
        
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(f"{item_type.title()}: {display_name}"))
        layout.addWidget(QLabel(f"Context: {parent_context}"))
        
        self.streak_label = QLabel(f"Current streak: {initial_streak}")
        layout.addWidget(self.streak_label)
        
        btn_row = QHBoxLayout()
        success_btn = QPushButton("Success")
        success_btn.clicked.connect(self._do_success)
        fail_btn = QPushButton("Fail")
        fail_btn.clicked.connect(self._do_fail)
        end_btn = QPushButton("End Session")
        end_btn.clicked.connect(self.close)
        
        btn_row.addWidget(success_btn)
        btn_row.addWidget(fail_btn)
        btn_row.addWidget(end_btn)
        layout.addLayout(btn_row)
    
    def _do_success(self) -> None:
        self._on_success()
        self._refresh_streak()
    
    def _do_fail(self) -> None:
        self._on_fail()
        self._refresh_streak()
    
    def _refresh_streak(self) -> None:
        self.streak_label.setText(f"Current streak: {self._get_streak()}")
    
    def refresh(self) -> None:
        """Refresh streak display from current data."""
        self._refresh_streak()
