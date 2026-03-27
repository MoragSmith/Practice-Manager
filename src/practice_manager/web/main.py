"""
Practice Manager - Web server entry point

FastAPI app for library browse and practice session.
Run with: uvicorn src.practice_manager.web.main:app --reload

Password protection: set AUTH_USERNAME and AUTH_PASSWORD env vars to enable
HTTP Basic Authentication. If unset, the site is open.
"""

import base64
import logging
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response

from .api import library, practice, assets, status

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

AUTH_USERNAME = os.environ.get("AUTH_USERNAME")
AUTH_PASSWORD = os.environ.get("AUTH_PASSWORD")
AUTH_ENABLED = bool(AUTH_USERNAME and AUTH_PASSWORD)

app = FastAPI(
    title="Practice Manager API",
    description="Library browse and practice session for OTPD Scores",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _check_basic_auth(auth_header: str | None) -> bool:
    """Return True if credentials are valid."""
    if not AUTH_ENABLED:
        return True
    if not auth_header or not auth_header.startswith("Basic "):
        return False
    try:
        decoded = base64.b64decode(auth_header[6:]).decode("utf-8")
        username, _, password = decoded.partition(":")
        return username == AUTH_USERNAME and password == AUTH_PASSWORD
    except Exception:
        return False


@app.middleware("http")
async def basic_auth_middleware(request: Request, call_next):
    """Require HTTP Basic Auth when AUTH_USERNAME and AUTH_PASSWORD are set."""
    if not AUTH_ENABLED:
        return await call_next(request)
    auth = request.headers.get("Authorization")
    if _check_basic_auth(auth):
        return await call_next(request)
    return Response(
        status_code=401,
        headers={"WWW-Authenticate": 'Basic realm="Practice Manager"'},
        content="Authentication required",
    )

app.include_router(library.router, prefix="/api/library", tags=["library"])
app.include_router(practice.router, prefix="/api/practice", tags=["practice"])
app.include_router(assets.router, prefix="/api/assets", tags=["assets"])
app.include_router(status.router, prefix="/api/status", tags=["status"])

# Static files and SPA
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    @app.get("/")
    def serve_app() -> FileResponse:
        """Serve the SPA."""
        return FileResponse(static_dir / "index.html")
else:
    @app.get("/")
    def root() -> dict:
        """Health check (no static files)."""
        return {"status": "ok", "app": "Practice Manager"}
