"""
wait.py
=======
Explicit wait strategies shared by both driver implementations.

Selenium waits are implemented with `WebDriverWait` + `expected_conditions`.
Playwright already has robust web-first auto-waiting built into its actions,
but this module exposes explicit helpers for the cases where an assertion
or navigation needs a deliberate, named wait (e.g. waiting for a URL change,
waiting for an element count) rather than relying on implicit auto-waiting.
"""

from __future__ import annotations

from typing import Any, Optional

from core.utilities.data_reader import DataReader
from core.utilities.logger import get_logger

log = get_logger(__name__)


def _explicit_timeout() -> int:
    return DataReader.read_yaml("config/config.yaml").get("timeouts", {}).get(
        "explicit_wait", 15
    )


class SeleniumWait:
    """Explicit wait helpers for Selenium WebDriver."""

    def __init__(self, driver: Any, timeout: Optional[int] = None):
        from selenium.webdriver.support.ui import WebDriverWait
        self.driver = driver
        self.timeout = timeout or _explicit_timeout()
        self.wait = WebDriverWait(
            driver,
            self.timeout,
            poll_frequency=DataReader.read_yaml("config/config.yaml")
            .get("timeouts", {})
            .get("poll_frequency", 0.5),
        )

    def until_visible(self, locator: tuple):
        from selenium.webdriver.support import expected_conditions as EC
        log.debug("Waiting for visibility of element: %s", locator)
        return self.wait.until(EC.visibility_of_element_located(locator))

    def until_clickable(self, locator: tuple):
        from selenium.webdriver.support import expected_conditions as EC
        log.debug("Waiting for element to be clickable: %s", locator)
        return self.wait.until(EC.element_to_be_clickable(locator))

    def until_present(self, locator: tuple):
        from selenium.webdriver.support import expected_conditions as EC
        log.debug("Waiting for presence of element: %s", locator)
        return self.wait.until(EC.presence_of_element_located(locator))

    def until_invisible(self, locator: tuple) -> bool:
        from selenium.webdriver.support import expected_conditions as EC
        log.debug("Waiting for element to become invisible: %s", locator)
        return self.wait.until(EC.invisibility_of_element_located(locator))

    def until_url_contains(self, fragment: str) -> bool:
        from selenium.webdriver.support import expected_conditions as EC
        log.debug("Waiting for URL to contain: %s", fragment)
        return self.wait.until(EC.url_contains(fragment))

    def until_text_present(self, locator: tuple, text: str) -> bool:
        from selenium.webdriver.support import expected_conditions as EC
        log.debug("Waiting for text '%s' in element: %s", text, locator)
        return self.wait.until(EC.text_to_be_present_in_element(locator, text))


class PlaywrightWait:
    """
    Explicit wait helpers for Playwright.

    Playwright's `Locator` API auto-waits for actionability before every
    action, so most of this class exists for scenarios needing an explicit,
    named checkpoint (navigation, custom state) beyond default auto-waiting.
    """

    def __init__(self, page: Any, timeout: Optional[int] = None):
        self.page = page
        # Playwright timeouts are in milliseconds.
        self.timeout_ms = (timeout or _explicit_timeout()) * 1000

    def until_visible(self, selector: str):
        log.debug("Waiting for visibility of selector: %s", selector)
        locator = self.page.locator(selector)
        locator.wait_for(state="visible", timeout=self.timeout_ms)
        return locator

    def until_hidden(self, selector: str) -> None:
        log.debug("Waiting for selector to become hidden: %s", selector)
        self.page.locator(selector).wait_for(state="hidden", timeout=self.timeout_ms)

    def until_attached(self, selector: str):
        log.debug("Waiting for selector to attach to DOM: %s", selector)
        locator = self.page.locator(selector)
        locator.wait_for(state="attached", timeout=self.timeout_ms)
        return locator

    def until_url_contains(self, fragment: str) -> None:
        log.debug("Waiting for URL to contain: %s", fragment)
        self.page.wait_for_url(f"**/*{fragment}*", timeout=self.timeout_ms)

    def until_load_state(self, state: str = "networkidle") -> None:
        log.debug("Waiting for page load state: %s", state)
        self.page.wait_for_load_state(state, timeout=self.timeout_ms)
