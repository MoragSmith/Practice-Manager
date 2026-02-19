"""
Practice Manager - Asset resolution and OS open

Resolves PDF/WAV paths for sets, tunes, and parts.
Opens files using OS default apps (macOS: open, Windows: os.startfile, Linux: xdg-open).
On macOS: PDF in Acrobat (left half), Music mini player only, session dialog (right half).
"""

import logging
import os
import platform
import subprocess
import time
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
    Checks set_path first (complete tune often in set folder), then set_path/Parts/ as fallback.
    If tune_name finds nothing, tries set_folder_name (set_path.name) - common for single-tune sets.
    """
    set_path = Path(set_path).resolve()
    set_folder_name = set_path.name

    def _find_wav(name: str) -> Optional[Path]:
        for base in (set_path, set_path / "Parts"):
            p = base / f"{name}.wav"
            if p.exists():
                return p
        for base in (set_path, set_path / "Parts"):
            p = base / f"{name}_{instrument}.wav"
            if p.exists():
                logger.warning("No complete WAV for %s, using instrument WAV", name)
                return p
        return None

    def _find_pdf(name: str) -> Optional[Path]:
        for base in (set_path, set_path / "Parts"):
            p = base / f"{name}_{instrument}.pdf"
            if p.exists():
                return p
        for base in (set_path, set_path / "Parts"):
            p = base / f"{name}.pdf"
            if p.exists():
                return p
        return None

    wav_path = _find_wav(tune_name)
    pdf_path = _find_pdf(tune_name)
    if (not wav_path or not pdf_path) and tune_name != set_folder_name:
        wav_path = wav_path or _find_wav(set_folder_name)
        pdf_path = pdf_path or _find_pdf(set_folder_name)
    if not wav_path:
        logger.warning(
            "No WAV found for tune %r in %s (tried %s.wav, %s.wav)",
            tune_name, set_path, tune_name, set_folder_name,
        )
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


def get_part_assets(
    part_record: dict,
    instrument: str,
) -> Tuple[Optional[Path], Optional[Path]]:
    """
    Get (pdf_path, wav_path) from a discovered part record.
    Prefers instrument-specific PDF (e.g. {part_id}_bass.pdf) when it exists.
    """
    parts_dir = part_record["pdf_path"].parent
    part_id = part_record["part_id"]
    wav_path = part_record["wav_path"]

    # Prefer instrument-specific PDF
    pdf_instr = parts_dir / f"{part_id}_{instrument}.pdf"
    if pdf_instr.exists():
        return (pdf_instr, wav_path)
    # Fallback: stored PDF (may be a different instrument)
    return (part_record["pdf_path"], wav_path)


def open_file(path: Path, app: Optional[str] = None) -> None:
    """Open a file with the OS default application (or specified app on macOS)."""
    path = path.resolve()
    if not path.exists():
        logger.error("File not found: %s", path)
        return
    
    system = platform.system()
    try:
        if system == "Darwin":  # macOS
            if app:
                subprocess.run(["open", "-a", app, str(path)], check=True)
            else:
                subprocess.run(["open", str(path)], check=True)
        elif system == "Windows":
            os.startfile(str(path))
        else:
            subprocess.run(["xdg-open", str(path)], check=True)
    except Exception as e:
        logger.error("Failed to open %s: %s", path, e)


def close_music_app() -> None:
    """Quit the Music app (macOS). No-op on other platforms."""
    if platform.system() == "Darwin":
        _run_applescript('tell application "Music" to quit')


def _run_applescript(script: str) -> bool:
    """Run AppleScript; return True on success."""
    try:
        subprocess.run(
            ["osascript", "-e", script],
            check=True,
            capture_output=True,
            timeout=5,
        )
        return True
    except Exception:
        return False


def _arrange_macos_windows(
    left: int, top: int, width: int, height: int,
) -> None:
    """
    Resize PDF to left half of screen. Position Music mini player and session on right.
    left, top, width, height = screen available geometry.
    """
    half_w = width // 2
    mid_x = left + half_w
    right = left + width

    # Adobe Acrobat: try Ctrl+Left (native tile), then ensure left edge via position/size
    _run_applescript(
        'try\n'
        '  tell application "System Events"\n'
        '    set acrobatProc to first process whose name contains "Acrobat"\n'
        '    tell acrobatProc to activate\n'
        '    delay 0.4\n'
        '  end tell\n'
        '  key code 123 using {control down}\n'
        'end try'
    )
    time.sleep(0.2)
    # Ensure PDF is fully left (in case shortcut not enabled or partial)
    _run_applescript(
        f'try\n'
        f'  tell application "System Events" to tell (first process whose name contains "Acrobat")\n'
        f'    tell front window\n'
        f'      set position to {{{left}, {top}}}\n'
        f'      set size to {{{half_w}, {height}}}\n'
        f'    end tell\n'
        f'  end tell\n'
        f'end try'
    )
    time.sleep(0.3)

    # Music: Option+Cmd+M shows mini player (keeps it visible); activate to bring to front
    _run_applescript(
        'tell application "Music" to activate\n'
        'delay 0.3\n'
        'tell application "System Events" to keystroke "m" using {option down, command down}\n'
        'delay 0.2'
    )


def open_assets(
    pdf_path: Optional[Path],
    wav_path: Optional[Path],
    screen_rect: Optional[object] = None,
) -> None:
    """
    Open PDF and WAV with the OS default applications.

    On macOS: PDF opens in Acrobat (or Reader), WAV in Music. Windows are
    arranged (PDF left half, Music mini player). The session dialog
    is positioned separately in session_window.py (bottom-right).

    Args:
        pdf_path: Path to PDF, or None.
        wav_path: Path to WAV, or None.
        screen_rect: Optional QRect for window layout (e.g. primaryScreen().availableGeometry()).
    """
    if platform.system() == "Darwin":
        if pdf_path:
            try:
                subprocess.run(
                    ["open", "-a", "Adobe Acrobat", str(pdf_path.resolve())],
                    check=True, capture_output=True,
                )
            except subprocess.CalledProcessError:
                try:
                    subprocess.run(
                        ["open", "-a", "Adobe Acrobat Reader DC", str(pdf_path.resolve())],
                        check=True, capture_output=True,
                    )
                except subprocess.CalledProcessError:
                    open_file(pdf_path)
            time.sleep(0.5)
        if wav_path:
            open_file(wav_path, app="Music")
            # Allow Music to load the file and establish current track (longer for cloud/network paths)
            time.sleep(1.5)
            _run_applescript('tell application "Music" to play')
            time.sleep(0.3)
            _run_applescript('tell application "Music" to set song repeat to one')
            # Switch to Mini Player (can reset repeat, so we re-apply after)
            _run_applescript(
                'tell application "Music" to activate\n'
                'delay 0.5\n'
                'tell application "System Events" to tell process "Music"\n'
                '  tell menu bar 1 to tell menu bar item "Window" to tell menu "Window"\n'
                '    click menu item "Switch to Mini Player"\n'
                '  end tell\n'
                'end tell\n'
                'delay 0.5\n'
                'tell application "Music" to activate'
            )
            time.sleep(0.4)
            _run_applescript('tell application "Music" to set song repeat to one')
            time.sleep(0.2)
        if screen_rect and (pdf_path or wav_path):
            _arrange_macos_windows(
                screen_rect.x(), screen_rect.y(),
                screen_rect.width(), screen_rect.height(),
            )
    else:
        if pdf_path:
            open_file(pdf_path)
        if wav_path:
            open_file(wav_path)
