"""
Practice Manager - Asset resolution and OS open

Resolves PDF/WAV paths for sets, tunes, and parts.
Opens files using OS default apps (macOS: open, Windows: os.startfile, Linux: xdg-open).
"""

import logging
import os
import platform
import subprocess
from pathlib import Path
from typing import List, Optional, Tuple

from .config import INSTRUMENTS

logger = logging.getLogger(__name__)


def get_tune_assets(
    set_path: Path,
    tune_name: str,
    instrument: str,
) -> Tuple[Optional[Path], Optional[Path]]:
    """
    Get (pdf_path, wav_path) for a tune.
    WAV: complete tune (no instrument suffix).
    PDF: instrument-specific (e.g. _bass.pdf).
    """
    # WAV: complete tune
    wav_complete = set_path / f"{tune_name}.wav"
    if wav_complete.exists():
        wav_path = wav_complete
    else:
        # Fallback: instrument WAV
        wav_instr = set_path / f"{tune_name}_{instrument}.wav"
        if wav_instr.exists():
            wav_path = wav_instr
            logger.warning("No complete WAV for %s, using instrument WAV", tune_name)
        else:
            wav_path = None
    
    # PDF: instrument-specific
    pdf_instr = set_path / f"{tune_name}_{instrument}.pdf"
    if pdf_instr.exists():
        pdf_path = pdf_instr
    else:
        pdf_complete = set_path / f"{tune_name}.pdf"
        pdf_path = pdf_complete if pdf_complete.exists() else None
    
    return (pdf_path, wav_path)


def get_set_assets(
    set_path: Path,
    tune_names: List[str],
    instrument: str,
) -> Tuple[Optional[Path], Optional[Path]]:
    """
    Get (pdf_path, wav_path) for a set.
    Opens first tune's assets (user practices set as first tune + can advance).
    PDF: first tune's instrument PDF.
    WAV: first tune's complete WAV.
    """
    if not tune_names:
        return (None, None)
    return get_tune_assets(set_path, tune_names[0], instrument)


def get_part_assets(part_record: dict) -> Tuple[Path, Path]:
    """Get (pdf_path, wav_path) from a discovered part record."""
    return (part_record["pdf_path"], part_record["wav_path"])


def open_file(path: Path) -> None:
    """Open a file with the OS default application."""
    path = path.resolve()
    if not path.exists():
        logger.error("File not found: %s", path)
        return
    
    system = platform.system()
    try:
        if system == "Darwin":  # macOS
            subprocess.run(["open", str(path)], check=True)
        elif system == "Windows":
            os.startfile(str(path))
        else:
            # Linux
            subprocess.run(["xdg-open", str(path)], check=True)
    except Exception as e:
        logger.error("Failed to open %s: %s", path, e)


def open_assets(pdf_path: Optional[Path], wav_path: Optional[Path]) -> None:
    """Open both PDF and WAV if available."""
    if pdf_path:
        open_file(pdf_path)
    if wav_path:
        open_file(wav_path)
