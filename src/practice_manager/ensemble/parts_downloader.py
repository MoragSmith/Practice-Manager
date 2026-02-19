"""
Practice Manager - Parts downloader (adapted from OTPD Music Manager EnsembleDownloader)

Downloads WAV (complete) and split PDF for a single part from Ensemble score editor.
No database dependency; uses base_name for file naming.
"""

import re
import logging
from pathlib import Path
from typing import List, Optional

from playwright.async_api import Page

logger = logging.getLogger(__name__)

# Instrument order for split PDF (from OTPD Music Manager)
INSTRUMENT_ORDER = ["bagpipes", "snare", "bass", "tenor", "seconds"]


def clean_part_name(raw: str) -> str:
    """
    Clean raw Ensemble part tile name for file naming (OTPD-style).

    e.g. "Competition 08 - Prince Charles Welcome to Lochaber line1 14 FebPrivate"
    -> "Competition 08 - Prince Charles Welcome to Lochaber line1"

    Removes: dates (14 Feb, FebPrivate, etc.), standalone Private.
    Keeps: line1, phrase2, part 1 bass (the number is part of the part identifier).
    Do NOT strip digits after line/phrase - "line 114" may be line1 + "14 Feb" combined.
    """
    if not raw:
        return raw
    cleaned = raw.strip()
    months = r"Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec"
    cleaned = re.sub(rf"\d{{1,2}}\s+({months})[a-z]*,?\s*\d{{0,4}}\s*Private?", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(rf"({months})[a-z]*Private", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(rf"(?<=[A-Za-z\s])(\d{{1,2}})\s*({months})[a-z]*\s*$", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*Private\s*", " ", cleaned, flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", cleaned).strip()


class PartsDownloader:
    """Download WAV and split PDF for Ensemble part items."""

    def __init__(self, page: Page, downloads_dir: Path):
        self.page = page
        self.downloads_dir = Path(downloads_dir)
        self.downloads_dir.mkdir(parents=True, exist_ok=True)

    async def download_part(self, base_name: str) -> List[Path]:
        """
        Download WAV (complete) and split PDF for the currently open part.

        Must be called when page is on the score editor for the part.
        base_name: e.g. "Competition 08 - Prince Charles Welcome to Lochaber part 1 bass"

        Returns list of downloaded file paths.
        """
        results: List[Path] = []
        wav_path = await self._download_wav()
        if wav_path:
            results.append(wav_path)
        split_paths = await self._download_split_pdf(base_name)
        results.extend(split_paths)
        return results

    async def _download_wav(self) -> Optional[Path]:
        """Download complete WAV from File -> Download Audio."""
        try:
            await self.page.wait_for_load_state("domcontentloaded")
            await self.page.wait_for_load_state("networkidle", timeout=30000)
            await self.page.wait_for_timeout(2000)

            for selector in ["#tb-file", "#tbButton-File"]:
                try:
                    btn = await self.page.wait_for_selector(selector, timeout=5000)
                    if btn:
                        await btn.click()
                        await self.page.wait_for_timeout(1000)
                        break
                except Exception:
                    continue
            else:
                logger.error("File menu button not found")
                return None

            download_wav = await self.page.wait_for_selector("#mnuDownloadAudio", timeout=15000)
            if not download_wav:
                logger.error("Download Audio menu item not found")
                return None

            async with self.page.expect_download(timeout=120000) as download_info:
                if not await self._click_with_retry("#mnuDownloadAudio", "Download Audio", timeout=5000):
                    return None

            download = await download_info.value
            suggested = download.suggested_filename
            final_path = self.downloads_dir / suggested
            counter = 1
            while final_path.exists():
                parts = suggested.rsplit(".", 1)
                final_path = self.downloads_dir / (f"{parts[0]}_{counter}.{parts[1]}" if len(parts) == 2 else f"{suggested}_{counter}")
                counter += 1
            await download.save_as(str(final_path))
            logger.info("Downloaded WAV: %s", final_path.name)
            return final_path
        except Exception as e:
            logger.error("WAV download failed: %s", e)
            return None

    async def _download_split_pdf(self, base_name: str) -> List[Path]:
        """Download split PDF (one per instrument page) and save as separate files."""
        try:
            await self.page.wait_for_load_state("domcontentloaded")
            await self.page.wait_for_load_state("networkidle", timeout=30000)
            await self.page.wait_for_timeout(2000)

            if not await self._click_with_retry("#tb-file, #tbButton-File", "File button", timeout=10000):
                return []
            await self.page.wait_for_timeout(1000)

            create_btn = await self.page.wait_for_selector("#mnuCreateSplitPDF", timeout=15000)
            if not create_btn:
                logger.error("Create split PDF button not found")
                return []

            if not await self._click_with_retry("#mnuCreateSplitPDF", "Create split PDF", timeout=5000, max_retries=5):
                return []
            await self.page.wait_for_timeout(2000)

            dialog_btn = await self.page.wait_for_selector("#soSplitPDFSplitButton", timeout=10000)
            if not dialog_btn:
                return []

            async with self.page.expect_download(timeout=60000) as download_info:
                if not await self._click_with_retry("#soSplitPDFSplitButton", "Dialog Create PDF", timeout=5000):
                    return []

            download = await download_info.value
            scores_path = self.downloads_dir / "Scores.pdf"
            counter = 1
            while scores_path.exists():
                scores_path = self.downloads_dir / f"Scores_{counter}.pdf"
                counter += 1
            await download.save_as(str(scores_path))
            if not scores_path.exists():
                return []

            split_files = self._split_pdf_by_instruments(scores_path, clean_part_name(base_name))
            try:
                scores_path.unlink()
            except Exception:
                pass
            return split_files
        except Exception as e:
            logger.error("Split PDF download failed: %s", e)
            return []

    def _split_pdf_by_instruments(self, scores_path: Path, base_name: str) -> List[Path]:
        """Split Scores.pdf into one file per instrument page."""
        try:
            from pypdf import PdfReader, PdfWriter

            reader = PdfReader(str(scores_path))
            total_pages = len(reader.pages)
            split_files = []
            for i, instrument in enumerate(INSTRUMENT_ORDER):
                if i >= total_pages:
                    break
                writer = PdfWriter()
                writer.add_page(reader.pages[i])
                instrument_filename = f"{base_name}_{instrument}.pdf"
                instrument_path = self.downloads_dir / instrument_filename
                counter = 1
                while instrument_path.exists():
                    instrument_path = self.downloads_dir / f"{base_name}_{instrument}_{counter}.pdf"
                    counter += 1
                with open(instrument_path, "wb") as f:
                    writer.write(f)
                split_files.append(instrument_path)
                logger.info("Created %s", instrument_path.name)
            return split_files
        except ImportError:
            logger.error("pypdf not installed. Run: pip install pypdf")
            return []
        except Exception as e:
            logger.error("Split PDF failed: %s", e)
            return []

    async def _click_with_retry(
        self, selector: str, description: str, timeout: int = 15000, max_retries: int = 3
    ) -> bool:
        """Click element with retry logic."""
        for attempt in range(max_retries):
            try:
                element = await self.page.wait_for_selector(selector, timeout=timeout)
                if not element:
                    if attempt < max_retries - 1:
                        await self.page.wait_for_timeout(1000)
                    continue
                try:
                    await element.click(timeout=5000)
                    return True
                except Exception as ce:
                    if "intercepts" in str(ce) or attempt < max_retries - 1:
                        await element.evaluate("el => el.click()")
                        return True
                    raise
            except Exception as e:
                if attempt < max_retries - 1:
                    await self.page.wait_for_timeout(2000)
                else:
                    logger.warning("Click failed for %s: %s", description, e)
        return False
