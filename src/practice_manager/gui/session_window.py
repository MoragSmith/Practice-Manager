"""
Practice Manager - Integrated Practice Session Window

Provides a single-window practice session with:
- PDF viewer (left): Displays score sheet, scaled to full width of its panel with
  vertical scroll for tall pages. Supports multi-page navigation.
- Music player (upper right): WAV playback with play/pause, loop, and seek.
- Control buttons (lower right): Success/Fail/End Session for tracking practice.

Uses PyMuPDF for PDF rendering and QtMultimedia for audio playback.
"""

import logging
from pathlib import Path
from typing import Callable, Optional

from PySide6.QtCore import QUrl, Qt
from PySide6.QtGui import QImage, QPainter, QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QGraphicsPixmapItem,
    QGraphicsScene,
    QGraphicsView,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

logger = logging.getLogger(__name__)


def _render_pdf_page(pdf_path: Path, page_num: int = 0, dpi: int = 150) -> Optional[QPixmap]:
    """Render a single PDF page to a QPixmap using PyMuPDF.

    Args:
        pdf_path: Path to the PDF file.
        page_num: Zero-based page index. Clamped to valid range.
        dpi: Resolution for rendering (default 150).

    Returns:
        QPixmap of the rendered page, or None if PyMuPDF is unavailable or
        rendering fails.
    """
    try:
        import fitz
    except ImportError:
        logger.warning("PyMuPDF not installed; PDF display disabled")
        return None
    try:
        doc = fitz.open(pdf_path)
        if page_num >= doc.page_count:
            page_num = doc.page_count - 1
        if page_num < 0:
            page_num = 0
        page = doc.load_page(page_num)
        mat = fitz.Matrix(dpi / 72, dpi / 72)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        doc.close()
        # Convert to QImage then QPixmap
        qimg = QImage(
            pix.samples,
            pix.width,
            pix.height,
            pix.stride,
            QImage.Format.Format_RGB888,
        )
        return QPixmap.fromImage(qimg)
    except Exception as e:
        logger.exception("Failed to render PDF %s: %s", pdf_path, e)
        return None


class PdfViewer(QWidget):
    """Displays a PDF page with optional prev/next for multi-page documents.

    Scales the page to span the full width of the view; vertical scroll is
    available when the page is taller than the viewport.
    """

    def __init__(self, pdf_path: Optional[Path] = None) -> None:
        """Initialize the viewer.

        Args:
            pdf_path: Optional path to a PDF file. If provided, loads and
                displays the first page.
        """
        super().__init__()
        self._pdf_path = pdf_path
        self._page_num = 0
        self._page_count = 0
        self._scene = QGraphicsScene()
        self._view = QGraphicsView(self._scene)
        self._view.setMinimumSize(400, 500)
        self._view.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        self._view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self._view.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._view.setStyleSheet("QGraphicsView { background: #2b2b2b; }")
        layout = QVBoxLayout(self)
        self._page_label = QLabel("")
        layout.addWidget(self._page_label)
        layout.addWidget(self._view)
        self._nav_row = QHBoxLayout()
        self._prev_btn = QPushButton("← Previous")
        self._next_btn = QPushButton("Next →")
        self._prev_btn.clicked.connect(self._prev_page)
        self._next_btn.clicked.connect(self._next_page)
        self._nav_row.addWidget(self._prev_btn)
        self._nav_row.addStretch()
        self._nav_row.addWidget(self._next_btn)
        layout.addLayout(self._nav_row)
        if pdf_path:
            self._load_pdf(pdf_path)

    def _load_pdf(self, path: Path) -> None:
        """Load a PDF file and display its first page."""
        self._pdf_path = path
        try:
            import fitz
            doc = fitz.open(path)
            self._page_count = doc.page_count
            doc.close()
        except Exception:
            self._page_count = 0
        self._page_num = 0
        self._render_current()

    def _render_current(self) -> None:
        """Render the current page and update navigation state."""
        if not self._pdf_path:
            self._page_label.setText("No PDF")
            self._prev_btn.setEnabled(False)
            self._next_btn.setEnabled(False)
            return
        pix = _render_pdf_page(self._pdf_path, self._page_num)
        self._scene.clear()
        if pix and not pix.isNull():
            item = QGraphicsPixmapItem(pix)
            self._scene.addItem(item)
            self._fit_to_width()
        self._page_label.setText(
            f"Page {self._page_num + 1} of {self._page_count}" if self._page_count > 0 else "Page 1"
        )
        self._prev_btn.setEnabled(self._page_num > 0)
        self._next_btn.setEnabled(self._page_num < self._page_count - 1)
        self._prev_btn.setVisible(self._page_count > 1)
        self._next_btn.setVisible(self._page_count > 1)

    def _prev_page(self) -> None:
        """Navigate to the previous page."""
        if self._page_num > 0:
            self._page_num -= 1
            self._render_current()

    def _next_page(self) -> None:
        """Navigate to the next page."""
        if self._page_num < self._page_count - 1:
            self._page_num += 1
            self._render_current()

    def _fit_to_width(self) -> None:
        """Scale the displayed PDF to span the full width of the viewport.

        Vertical scroll is enabled when the page is taller than the view.
        Called on render and when the widget is resized.
        """
        for item in self._scene.items():
            if isinstance(item, QGraphicsPixmapItem):
                br = item.boundingRect()
                if br.width() > 0:
                    vp = self._view.viewport()
                    if vp and vp.width() > 0:
                        scale = vp.width() / br.width()
                        self._view.resetTransform()
                        self._view.scale(scale, scale)
                break

    def resizeEvent(self, event) -> None:
        """Re-fit PDF to width when the widget is resized."""
        super().resizeEvent(event)
        self._fit_to_width()


class MusicPlayer(QWidget):
    """Simple WAV player with play/pause, loop, and seek.

    Uses QtMultimedia. Falls back to a disabled placeholder if no audio
    backend is available.
    """

    def __init__(self, wav_path: Optional[Path] = None) -> None:
        """Initialize the player.

        Args:
            wav_path: Optional path to a WAV file. If provided and exists,
                loads and starts playback (looped).
        """
        super().__init__()
        self._player = None
        self._play_btn = QPushButton("Play")
        self._progress = QSlider(Qt.Orientation.Horizontal)
        self._time_label = QLabel("--:-- / --:--")

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Playback"))
        layout.addWidget(self._play_btn)
        layout.addWidget(self._progress)
        layout.addWidget(self._time_label)

        try:
            from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer

            self._player = QMediaPlayer()
            self._audio_output = QAudioOutput()
            self._player.setAudioOutput(self._audio_output)
            self._player.setLoops(-1)
            self._progress.setRange(0, 0)
            self._progress.sliderMoved.connect(self._seek)
            self._play_btn.clicked.connect(self._toggle_play)
            self._player.positionChanged.connect(self._on_position)
            self._player.durationChanged.connect(self._on_duration)
            self._player.playbackStateChanged.connect(self._on_state)

            if wav_path and wav_path.exists():
                self._player.setSource(QUrl.fromLocalFile(str(wav_path.resolve())))
                self._play_btn.setEnabled(True)
                self._player.play()
            else:
                self._play_btn.setEnabled(False)
                self._time_label.setText("No audio")
        except Exception as e:
            logger.warning("QtMultimedia unavailable, playback disabled: %s", e)
            self._play_btn.setEnabled(False)
            self._time_label.setText("Playback unavailable (install QtMultimedia backend)")

    def _toggle_play(self) -> None:
        """Toggle between play and pause."""
        if self._player:
            from PySide6.QtMultimedia import QMediaPlayer
            if self._player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
                self._player.pause()
            else:
                self._player.play()

    def _on_state(self, state) -> None:
        """Update playback button label when state changes."""
        from PySide6.QtMultimedia import QMediaPlayer
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self._play_btn.setText("Pause")
        else:
            self._play_btn.setText("Play")

    def _on_position(self, pos: int) -> None:
        """Update progress slider and time label when position changes."""
        self._progress.blockSignals(True)
        self._progress.setValue(pos)
        self._progress.blockSignals(False)
        if self._player:
            d = self._player.duration()
            if d > 0:
                self._time_label.setText(f"{pos // 1000 // 60}:{pos // 1000 % 60:02d} / {d // 1000 // 60}:{d // 1000 % 60:02d}")

    def _on_duration(self, d: int) -> None:
        """Set progress slider range when duration is known."""
        self._progress.setRange(0, max(0, d))

    def _seek(self, pos: int) -> None:
        """Seek to position (ms) when user drags the progress slider."""
        if self._player:
            self._player.setPosition(pos)

    def stop(self) -> None:
        """Stop playback."""
        if self._player:
            self._player.stop()


class SessionWindow(QDialog):
    """Integrated practice session dialog.

    Layout: PDF viewer on the left; music player and controls on the right.
    """

    def __init__(
        self,
        item_type: str,
        item_id: str,
        display_name: str,
        parent_context: str,
        initial_streak: int,
        pdf_path: Optional[Path],
        wav_path: Optional[Path],
        on_success: Callable[[], None],
        on_fail: Callable[[], None],
        get_streak: Callable[[], int],
        on_end_session: Optional[Callable[[], None]] = None,
    ):
        """Initialize the session window.

        Args:
            item_type: Type of item (e.g. "tune", "part").
            item_id: Unique identifier for the item.
            display_name: Human-readable name for display.
            parent_context: Context string (e.g. set name).
            initial_streak: Current streak count.
            pdf_path: Path to score PDF, or None.
            wav_path: Path to WAV audio, or None.
            on_success: Callback when user marks success.
            on_fail: Callback when user marks fail.
            get_streak: Callable returning current streak.
            on_end_session: Optional callback when session ends.
        """
        super().__init__()
        self._item_id = item_id
        self._on_success = on_success
        self._on_fail = on_fail
        self._get_streak = get_streak
        self._on_end_session = on_end_session
        self._music_player: Optional[MusicPlayer] = None

        self.setWindowTitle(f"Practice Session - {display_name}")
        self.setModal(False)
        self.setMinimumSize(1000, 600)
        self.resize(1200, 700)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left: PDF
        self._pdf_viewer = PdfViewer(pdf_path)
        splitter.addWidget(self._pdf_viewer)

        # Right: player + controls
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.addWidget(QLabel(f"{item_type.title()}: {display_name}"))
        right_layout.addWidget(QLabel(f"Context: {parent_context}"))

        # Music player (upper right)
        self._music_player = MusicPlayer(wav_path)
        right_layout.addWidget(self._music_player)

        # Control buttons (lower right)
        self.streak_label = QLabel(f"Current streak: {initial_streak}")
        right_layout.addWidget(self.streak_label)
        btn_row = QHBoxLayout()
        success_btn = QPushButton("Success")
        success_btn.clicked.connect(self._do_success)
        fail_btn = QPushButton("Fail")
        fail_btn.clicked.connect(self._do_fail)
        end_btn = QPushButton("End Session")
        end_btn.clicked.connect(self._do_end_session)
        btn_row.addWidget(success_btn)
        btn_row.addWidget(fail_btn)
        btn_row.addWidget(end_btn)
        right_layout.addLayout(btn_row)
        right_layout.addStretch()

        splitter.addWidget(right)
        splitter.setSizes([700, 400])

        main_layout = QVBoxLayout(self)
        main_layout.addWidget(splitter)

    def _do_success(self) -> None:
        """Handle Success button: record success and refresh streak."""
        self._on_success()
        self._refresh_streak()

    def _do_fail(self) -> None:
        """Handle Fail button: record fail and refresh streak."""
        self._on_fail()
        self._refresh_streak()

    def _do_end_session(self) -> None:
        """Handle End Session: stop playback, close window, run callback."""
        if self._music_player:
            self._music_player.stop()
        if self._on_end_session:
            self._on_end_session()
        self.close()

    def _refresh_streak(self) -> None:
        """Update the streak label from the current value."""
        self.streak_label.setText(f"Current streak: {self._get_streak()}")

    def refresh(self) -> None:
        """Refresh displayed data (e.g. streak after success/fail)."""
        self._refresh_streak()
