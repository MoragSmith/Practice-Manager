"""
Practice Manager - Download Parts workflow

Runs the full workflow: login -> Parts -> for each part: download WAV + split PDF -> organize.
Designed to run in a background thread; emits progress via callback.
"""

import asyncio
import logging
from pathlib import Path
from typing import Callable, List, Optional

from playwright.async_api import async_playwright

from ..config import get_ensemble_config, get_library_root
from .navigator import EnsembleNavigator
from .parts_downloader import PartsDownloader

logger = logging.getLogger(__name__)


async def run_download_parts(
    on_progress: Optional[Callable[[str], None]] = None,
    on_error: Optional[Callable[[str], None]] = None,
    base_url: Optional[str] = None,
    headless: bool = False,
    username: Optional[str] = None,
    password: Optional[str] = None,
    downloads_dir: Optional[Path] = None,
    scores_dir: Optional[Path] = None,
    max_parts: Optional[int] = None,
) -> dict:
    """
    Run the full Download Parts workflow.

    Returns dict with success, failed, organized counts and any error message.
    Optional params (base_url, headless, username, etc.) allow tests to override config.
    """
    result = {"success": 0, "failed": 0, "organized": 0, "error": None}

    def progress(msg: str) -> None:
        logger.info("%s", msg)
        if on_progress:
            on_progress(msg)

    def error_msg(msg: str) -> None:
        logger.error("%s", msg)
        if on_error:
            on_error(msg)

    config = get_ensemble_config()
    username = username or config.get("username")
    password = password or config.get("password")
    downloads_dir = Path(downloads_dir) if downloads_dir else Path(config.get("downloads_dir") or str(Path.home() / "Downloads"))
    if scores_dir is not None:
        scores_dir = Path(scores_dir)
    else:
        try:
            scores_dir = Path(config.get("scores_dir") or str(get_library_root()))
        except FileNotFoundError:
            result["error"] = "Could not find library root."
            return result

    if not username or not password:
        result["error"] = "Ensemble credentials not configured. Set ENSEMBLE_USERNAME and ENSEMBLE_PASSWORD."
        return result

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless)
        context = await browser.new_context(accept_downloads=True)
        page = await context.new_page()

        try:
            nav = EnsembleNavigator(page, base_url=base_url)
            progress("Logging in to Ensemble...")
            if not await nav.login(username, password):
                result["error"] = "Login failed."
                return result
            progress("Logged in.")

            progress("Navigating to Parts...")
            if not await nav.goto_scores():
                result["error"] = "Could not navigate to scores."
                return result
            if not await nav.navigate_to_parts():
                result["error"] = "Could not find Parts workspace."
                return result
            progress("In Parts workspace.")

            async def get_part_tiles():
                """Get clickable part tiles - same pattern as OTPD url_capture (wait .tile, query .tile)."""
                await page.wait_for_selector(".tile", timeout=10000)
                tiles = await page.query_selector_all(".tile")
                out = []
                for t in tiles:
                    try:
                        text = await t.text_content()
                        if not text or not text.strip():
                            continue
                        if text.strip().startswith("Section"):
                            continue
                        tile_type = await t.get_attribute("type")
                        if tile_type == "folder":
                            continue
                        out.append((text.strip(), t))
                    except Exception:
                        continue
                return out

            part_tiles = await get_part_tiles()
            if not part_tiles:
                result["error"] = "No parts found in Parts workspace."
                return result
            progress(f"Found {len(part_tiles)} part(s).")

            async def wait_for_editor_load(target_page):
                """OTPD url_capture._wait_for_editor_load - wait for File menu/button."""
                for attempt in range(5):
                    try:
                        await target_page.wait_for_selector("text=File", timeout=5000)
                        return True
                    except Exception:
                        if attempt < 4:
                            await target_page.wait_for_timeout(2000)
                try:
                    await target_page.wait_for_selector("#tb-file, #tbButton-File", timeout=5000)
                    return True
                except Exception:
                    pass
                return False

            all_downloaded: List[Path] = []
            limit = len(part_tiles) if max_parts is None else min(max_parts, len(part_tiles))
            for i in range(limit):
                await page.wait_for_timeout(500)
                if not await nav.goto_scores() or not await nav.navigate_to_parts():
                    result["error"] = "Lost Parts workspace; stopping."
                    break
                current = await get_part_tiles()
                if i >= len(current):
                    continue
                part_name, tile = current[i]
                progress(f"Downloading ({i + 1}/{len(part_tiles)}): {part_name[:60]}...")
                editor_page = page
                try:
                    await tile.click(timeout=5000)
                    await page.wait_for_timeout(3000)
                    editor_page = page
                    if len(context.pages) > 1 and "editor" not in page.url.lower():
                        for tab in context.pages:
                            if "editor" in tab.url.lower():
                                editor_page = tab
                                break
                    if not await wait_for_editor_load(editor_page):
                        raise TimeoutError("Editor did not load (File menu/button not found)")
                    await editor_page.wait_for_timeout(1000)

                    downloader = PartsDownloader(editor_page, downloads_dir)
                    files = await downloader.download_part(part_name)
                    if files:
                        result["success"] += 1
                        all_downloaded.extend(files)
                    else:
                        result["failed"] += 1

                    if editor_page != page:
                        await editor_page.close()
                    else:
                        await editor_page.go_back()
                    await page.wait_for_timeout(3000)
                except Exception as e:
                    result["failed"] += 1
                    error_msg(f"Failed {part_name[:40]}: {e}")
                    try:
                        if editor_page != page:
                            await editor_page.close()
                        else:
                            await page.go_back()
                        await page.wait_for_timeout(2000)
                    except Exception:
                        pass

            progress("Organizing files...")
            from .parts_organizer import PartsOrganizer

            organizer = PartsOrganizer(downloads_dir, scores_dir, scores_dir)
            stats = organizer.organize_downloads(dry_run=False, only_files=all_downloaded)
            result["organized"] = stats.get("organized", 0)
            progress(f"Organized {result['organized']} file(s).")

        finally:
            await browser.close()

    return result
