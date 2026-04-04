"""
Scraper Service — Self-healing web scraper for live cricket data.
Uses Playwright + AI auto-fix when selectors break.
"""

from __future__ import annotations

import asyncio
import json
import os
from typing import Any, Optional

try:
    import structlog
    logger = structlog.get_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

# Default headers to avoid bot detection
_DEFAULT_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/130.0.0.0 Safari/537.36"
)
_SCRAPE_TIMEOUT_MS = 15_000


class ScraperService:
    """Self-healing cricket data scraper with AI-powered selector recovery."""

    async def scrape_live_score(self, match_id: str) -> dict[str, Any]:
        """Scrape live score from Cricbuzz with self-healing fallback."""
        try:
            from playwright.async_api import async_playwright

            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(user_agent=_DEFAULT_UA)
                page = await context.new_page()

                url = f"https://www.cricbuzz.com/live-cricket-scores/{match_id}"
                await page.goto(url, wait_until="networkidle", timeout=_SCRAPE_TIMEOUT_MS)

                # Extract score element
                score_el = page.locator(".cb-scr-wll-chvrn")
                score = (
                    await score_el.text_content()
                    if await score_el.count() > 0
                    else None
                )

                await context.close()
                await browser.close()

                logger.info("scraper.success", match_id=match_id, has_score=score is not None)
                return {"match_id": match_id, "score": score, "source": "cricbuzz"}

        except Exception as exc:
            logger.warning("scraper.failed", match_id=match_id, error=str(exc))
            return await self._self_heal(str(exc), match_id)

    async def scrape_player_stats(self, player_id: str) -> dict[str, Any]:
        """Scrape player statistics from ESPN Cricinfo."""
        # TODO: Implement ESPN scraper
        return {"player_id": player_id, "stats": {}, "source": "espn"}

    async def scrape_news(self, query: str) -> list[dict]:
        """Fetch latest cricket news using Jina AI Reader."""
        # TODO: Implement Jina Reader integration
        return []

    async def _self_heal(self, error: str, match_id: str) -> dict[str, Any]:
        """AI analyzes broken scraper and suggests CSS selector fixes."""
        claude_key = os.getenv("CLAUDE_API_KEY")
        if not claude_key:
            logger.warning("self_heal.no_api_key")
            return {"match_id": match_id, "error": error, "fix": None}

        try:
            from anthropic import Anthropic

            claude = Anthropic(api_key=claude_key)

            response = await asyncio.to_thread(
                claude.messages.create,
                model="claude-haiku-4",
                max_tokens=500,
                messages=[
                    {
                        "role": "user",
                        "content": (
                            f"Cricket scraper failed with: {error}. "
                            "The page is cricbuzz.com live scores. "
                            "Suggest a new CSS selector for the score element. "
                            "Return JSON only with keys: selector, confidence, reasoning."
                        ),
                    }
                ],
            )

            fix = json.loads(response.content[0].text)
            logger.info("self_heal.fix_generated", match_id=match_id, fix=fix)
            return {"match_id": match_id, "error": "self_healing_triggered", "fix": fix}

        except Exception as heal_exc:
            logger.error("self_heal.failed", match_id=match_id, error=str(heal_exc))
            return {"match_id": match_id, "error": error, "fix": None}
