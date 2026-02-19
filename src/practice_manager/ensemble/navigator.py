"""
Practice Manager - Ensemble Navigator (adapted from OTPD Music Manager)

Browser navigation for Ensemble website. Includes navigate_to_parts for Parts workspace.
"""

import logging
from typing import Optional

from playwright.async_api import Page

logger = logging.getLogger(__name__)


class EnsembleNavigator:
    """
    Navigate Ensemble website structure.

    Handles login, navigation to Scores, Parts workspace, and tune/part selection.
    """

    def __init__(self, page: Page, base_url: Optional[str] = None):
        self.page = page
        self.base_url = base_url or "https://www.thisisensemble.com"

    async def login(self, username: str, password: str) -> bool:
        """Login to Ensemble."""
        try:
            logger.info("Logging in to Ensemble...")
            await self.page.goto(f"{self.base_url}/Login.html")
            await self.page.wait_for_load_state("networkidle")
            await self.page.wait_for_selector("#txtEmailAddress", timeout=10000)
            await self.page.fill("#txtEmailAddress", username)
            await self.page.keyboard.press("Tab")
            await self.page.fill("#txtPassword", password)
            await self.page.keyboard.press("Tab")
            await self.page.wait_for_selector("#btnLogin:not(.button-disabled)", timeout=5000)
            await self.page.click("#btnLogin")
            await self.page.wait_for_url(f"{self.base_url}/ScoreList.html", timeout=30000)
            if "ScoreList.html" in self.page.url:
                logger.info("Logged in and redirected to ScoreList")
                return True
            logger.error("Login redirect failed: %s", self.page.url)
            return False
        except Exception as e:
            logger.error("Login failed: %s", e)
            return False

    async def goto_scores(self) -> bool:
        """Navigate to Scores page."""
        try:
            current_url = self.page.url
            if "ScoreList.html" in current_url:
                if "#home" in current_url or "#scores" not in current_url:
                    await self.page.wait_for_timeout(2000)
                    scores_link = await self.page.query_selector("#leftNavScores")
                    if scores_link:
                        await scores_link.click()
                        await self.page.wait_for_timeout(3000)
                    else:
                        await self.page.goto(f"{self.base_url}/ScoreList.html#scores?wsID=-1")
                        await self.page.wait_for_timeout(3000)
                else:
                    await self.page.wait_for_timeout(2000)
                return True
            await self.page.goto(f"{self.base_url}/ScoreList.html#scores?wsID=-1")
            await self.page.wait_for_timeout(3000)
            return True
        except Exception as e:
            logger.error("Failed to navigate to scores: %s", e)
            return False

    async def navigate_to_parts(self) -> bool:
        """
        Navigate to Parts workspace (same level as OTPD Music Book).

        Scores -> click Parts tile -> we're in flat list of part items.
        """
        try:
            logger.debug("Navigating to scores view...")
            await self.page.wait_for_timeout(2000)
            current_url = self.page.url
            if "ScoreList.html" not in current_url:
                await self.page.goto(f"{self.base_url}/ScoreList.html#scores?wsID=-1")
                await self.page.wait_for_timeout(3000)
            elif "#home" in current_url or "#scores" not in current_url:
                scores_link = await self.page.query_selector("#leftNavScores")
                if scores_link:
                    await scores_link.click()
                    await self.page.wait_for_timeout(3000)
                else:
                    await self.page.goto(f"{self.base_url}/ScoreList.html#scores?wsID=-1")
                    await self.page.wait_for_timeout(3000)

            logger.debug("Looking for Parts workspace...")
            await self.page.wait_for_timeout(2000)
            parts_tile = await self.page.query_selector("text=Parts")
            if not parts_tile:
                parts_tile = await self.page.query_selector("text=/^Parts$/i")
            if not parts_tile:
                parts_tile = await self.page.query_selector("[title*='Parts' i]")
            if not parts_tile:
                logger.error("Parts workspace not found")
                return False

            await parts_tile.click()
            await self.page.wait_for_timeout(3000)
            logger.info("Navigated to Parts")
            return True
        except Exception as e:
            logger.error("Failed to navigate to Parts: %s", e)
            return False

    async def get_part_editor_url(self, part_name: str) -> Optional[str]:
        """
        Click on a part tile and get its editor URL.
        Uses OTPD url_capture pattern: wait for "text=File" or "#tb-file".
        """
        try:
            await self.page.wait_for_selector(".tile", timeout=10000)
            all_tiles = await self.page.query_selector_all(".tile")
            for tile in all_tiles:
                try:
                    text = await tile.text_content()
                    if text and part_name in text.strip():
                        tile_type = await tile.get_attribute("type")
                        if tile_type == "folder":
                            continue
                        await tile.click()
                        await self.page.wait_for_timeout(2000)
                        for _ in range(5):
                            try:
                                await self.page.wait_for_selector("text=File", timeout=5000)
                                break
                            except Exception:
                                await self.page.wait_for_timeout(2000)
                        else:
                            try:
                                await self.page.wait_for_selector("#tb-file, #tbButton-File", timeout=5000)
                            except Exception:
                                return None
                        await self.page.wait_for_timeout(1000)
                        if "editor" in self.page.url.lower():
                            return self.page.url
                        return None
                except Exception:
                    continue
            logger.warning("Part not found: %s", part_name[:60])
            return None
        except Exception as e:
            logger.error("Error getting editor URL for %s: %s", part_name[:40], e)
            return None
