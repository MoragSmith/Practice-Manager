"""
Assets API - stream PDF and WAV files.
"""

from pathlib import Path
from urllib.parse import unquote

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from src.practice_manager.core import get_library_root

router = APIRouter()


def _resolve_asset_path(path_param: str) -> Path:
    """Resolve a browser-provided library-relative path safely.

    Asset URLs intentionally expose paths relative to the configured OTPD Scores
    library. The final `is_relative_to` check is the important containment
    guard: even if a path is encoded strangely, it must resolve inside the
    library before FileResponse can stream it.
    """
    try:
        library_root = get_library_root()
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))

    path_param = unquote(path_param)
    if ".." in path_param or path_param.startswith("/"):
        raise HTTPException(status_code=400, detail="Invalid path")
    full = (library_root / path_param).resolve()
    if not full.is_relative_to(library_root.resolve()):
        raise HTTPException(status_code=400, detail="Path outside library")
    if not full.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return full


@router.get("/pdf")
def stream_pdf(path: str) -> FileResponse:
    """Stream a PDF file for inline display in the browser."""
    full_path = _resolve_asset_path(path)
    return FileResponse(
        full_path,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{full_path.name}"'},
    )


@router.get("/wav")
def stream_wav(path: str) -> FileResponse:
    """Stream a WAV file. path is relative to library root."""
    full_path = _resolve_asset_path(path)
    return FileResponse(
        full_path,
        media_type="audio/wav",
        filename=full_path.name,
    )
