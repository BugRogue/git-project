"""
playwright_factory.py
======================
Concrete factory responsible for launching a Playwright browser, context,
and page, using `sync_playwright` (the framework standardizes on sync API
for consistency with Selenium's synchronous model and to keep pytest
fixtures simple — no asyncio event-loop juggling required).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

from playwright.sync_api import Browser, BrowserContext, Page, Playwright, sync_playwright

from core.utilities.data_reader import DataReader
from core.utilities.logger import get_logger

log = get_logger(__name__)


@dataclass
class PlaywrightSession:
    """
    Bundles the full Playwright object graph so callers/fixtures can tear
    down every layer (page -> context -> browser -> playwright) in order.
    """
    playwright: Playwright
    browser: Browser
    context: BrowserContext
    page: Page


class PlaywrightFactory:
    """Builds a fully configured Playwright browser/context/page session."""

    @staticmethod
    def create_session() -> PlaywrightSession:
        """
        Launch Playwright and return a `PlaywrightSession` with an active
        page, tracing started (if configured), and viewport/timeouts applied.

        Returns:
            PlaywrightSession: handles for playwright, browser, context, page.
        """
        config = DataReader.read_yaml("config/config.yaml")
        capabilities = DataReader.get_browser_capabilities().get("playwright", {})
        browser_name = config.get("browser", "chrome").lower()
        headless = config.get("headless", True)
        remote_cfg = config.get("remote", {})

        engine_map = {"chrome": "chromium", "chromium": "chromium",
                      "edge": "chromium", "firefox": "firefox", "webkit": "webkit"}
        engine = engine_map.get(browser_name, "chromium")
        engine_caps = capabilities.get(engine, {})

        log.info("Creating Playwright session | engine=%s headless=%s", engine, headless)

        playwright = sync_playwright().start()
        browser_type = getattr(playwright, engine)

        launch_kwargs: Dict[str, Any] = {"headless": headless}
        if engine == "chromium" and engine_caps.get("args"):
            launch_kwargs["args"] = engine_caps["args"]

        if remote_cfg.get("enabled", False):
            browser = browser_type.connect(remote_cfg["hub_url"])
            log.info("Connected to remote Playwright server at %s", remote_cfg["hub_url"])
        else:
            browser = browser_type.launch(**launch_kwargs)

        viewport = engine_caps.get("viewport", {"width": 1920, "height": 1080})
        context = browser.new_context(
            viewport=viewport,
            accept_downloads=True,
        )

        timeouts = config.get("timeouts", {})
        # Playwright uses milliseconds for all timeouts.
        context.set_default_timeout(timeouts.get("explicit_wait", 15) * 1000)
        context.set_default_navigation_timeout(timeouts.get("page_load_timeout", 30) * 1000)

        if config.get("reporting", {}).get("trace_on_failure", False):
            context.tracing.start(screenshots=True, snapshots=True, sources=True)

        page = context.new_page()

        log.info("Playwright session created successfully.")
        return PlaywrightSession(
            playwright=playwright, browser=browser, context=context, page=page
        )
