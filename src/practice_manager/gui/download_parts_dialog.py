"""
Practice Manager - Download Parts dialog

Runs the Ensemble Parts download workflow in a background thread,
shows progress and result.
"""

import asyncio
import logging
from typing import Optional

from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (
    QDialog,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
)

from ..ensemble.download_parts_workflow import run_download_parts

logger = logging.getLogger(__name__)


class DownloadPartsWorker(QThread):
    """Run download workflow in background."""

    progress = Signal(str)
    finished = Signal(dict)
    error = Signal(str)

    def run(self) -> None:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                run_download_parts(
                    on_progress=lambda msg: self.progress.emit(msg),
                    on_error=lambda msg: self.error.emit(msg),
                )
            )
            self.finished.emit(result)
        except Exception as e:
            logger.exception("Download Parts failed")
            self.finished.emit({"error": str(e)})
        finally:
            loop.close()


class DownloadPartsDialog(QDialog):
    """Dialog for Download Parts workflow."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Download Parts from Ensemble")
        self.setMinimumSize(450, 350)
        self.resize(500, 400)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Downloading all parts from Ensemble Parts workspace..."))
        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        layout.addWidget(self.log)
        self.close_btn = QPushButton("Close")
        self.close_btn.setEnabled(False)
        self.close_btn.clicked.connect(self.accept)
        layout.addWidget(self.close_btn)
        self._worker: Optional[DownloadPartsWorker] = None

    def _append(self, text: str) -> None:
        self.log.appendPlainText(text)
        scrollbar = self.log.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def start(self) -> None:
        self._append("Starting...")
        self.close_btn.setEnabled(False)
        self._worker = DownloadPartsWorker()
        self._worker.progress.connect(self._on_progress)
        self._worker.error.connect(self._on_error)
        self._worker.finished.connect(self._on_finished)
        self._worker.start()

    def _on_progress(self, msg: str) -> None:
        self._append(msg)

    def _on_error(self, msg: str) -> None:
        self._append(f"Error: {msg}")

    def _on_finished(self, result: dict) -> None:
        err = result.get("error")
        if err:
            self._append(f"\nFailed: {err}")
        else:
            self._append(
                f"\nDone. Success: {result.get('success', 0)}, "
                f"Failed: {result.get('failed', 0)}, "
                f"Organized: {result.get('organized', 0)}"
            )
        self.close_btn.setEnabled(True)
