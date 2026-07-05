"""
screenshot.py
=============
Screenshot capture utility used on test failure (wired via conftest.py's
pytest hook) and optionally on demand from within tests/pages.

Works transparently across Selenium (`WebDriver.save_screenshot`) and
Playwright (`Page.screenshot`) by branching on the object type passed in.
"""

from __future__ import annotations

import os
import re
import threading
from datetime import datetime
from typing import Any

from core.utilities.data_reader import DataReader
from core.utilities.logger import get_logger

log = get_logger(__name__)
_dir_lock = threading.Lock()


class ScreenshotUtility:
    """Static helper for capturing and naming failure/debug screenshots."""

    @staticmethod
    def _sanitize(name: str) -> str:
        """Make a test name filesystem-safe."""
        return re.sub(r"[^A-Za-z0-9_\-]", "_", name)[:150]

    @classmethod
    def _screenshot_dir(cls) -> str:
        config = DataReader.read_yaml("config/config.yaml").get("reporting", {})
        directory = config.get("screenshot_dir", "screenshots")
        with _dir_lock:
            os.makedirs(directory, exist_ok=True)
        return directory

    @classmethod
    def capture(cls, driver_or_page: Any, test_name: str) -> str:
        """
        Capture a screenshot for either a Selenium WebDriver or a
        Playwright Page instance.

        Args:
            driver_or_page: The active Selenium `WebDriver` or Playwright `Page`.
            test_name: Name of the test, used to build a unique filename.

        Returns:
            Absolute path to the saved screenshot file, or empty string on failure.
        """
        directory = cls._screenshot_dir()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{cls._sanitize(test_name)}_{timestamp}.png"
        file_path = os.path.join(directory, filename)

        try:
            # Playwright Page objects expose `.screenshot(path=...)`
            if hasattr(driver_or_page, "screenshot") and not hasattr(
                driver_or_page, "save_screenshot"
            ):
                driver_or_page.screenshot(path=file_path, full_page=True)
            # Selenium WebDriver exposes `.save_screenshot(path)`
            elif hasattr(driver_or_page, "save_screenshot"):
                driver_or_page.save_screenshot(file_path)
            else:
                log.warning("Unsupported driver/page type for screenshot capture.")
                return ""

            log.info("Screenshot captured: %s", file_path)
            return os.path.abspath(file_path)
        except Exception as exc:
            log.error("Failed to capture screenshot for '%s': %s", test_name, exc)
            return ""
