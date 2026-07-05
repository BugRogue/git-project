"""
playwright_actions.py
======================
Concrete `CommonActions` implementation backed by Playwright's sync API.
Playwright locators auto-wait for actionability, so this wrapper leans on
that behavior directly and only reaches for `PlaywrightWait` for
navigation/state checks that fall outside single-action auto-waiting.
"""

from __future__ import annotations

from typing import List

from playwright.sync_api import Locator, Page

from core.utilities.logger import get_logger
from core.utilities.retry import retry_on_failure
from core.utilities.wait import PlaywrightWait
from core.wrappers.common_actions import CommonActions

log = get_logger(__name__)


class PlaywrightActions(CommonActions):
    """Playwright-backed implementation of the generic action interface."""

    def __init__(self, page: Page):
        self.page = page
        self.wait = PlaywrightWait(page)

    @retry_on_failure()
    def click(self, locator: str) -> None:
        log.info("Clicking selector: %s", locator)
        self.page.locator(locator).click()

    @retry_on_failure()
    def type_text(self, locator: str, text: str, clear_first: bool = True) -> None:
        log.info("Typing '%s' into selector: %s", text, locator)
        element = self.page.locator(locator)
        if clear_first:
            element.fill("")
        element.fill(text)

    @retry_on_failure()
    def get_text(self, locator: str) -> str:
        text = self.page.locator(locator).inner_text()
        log.debug("Retrieved text '%s' from selector: %s", text, locator)
        return text

    def is_displayed(self, locator: str) -> bool:
        try:
            return self.page.locator(locator).is_visible()
        except Exception:
            return False

    def get_elements(self, locator: str) -> List[Locator]:
        loc = self.page.locator(locator)
        count = loc.count()
        return [loc.nth(i) for i in range(count)]

    def navigate_to(self, url: str) -> None:
        log.info("Navigating to URL: %s", url)
        self.page.goto(url)

    def get_current_url(self) -> str:
        return self.page.url

    def get_title(self) -> str:
        return self.page.title()

    @retry_on_failure()
    def select_dropdown_by_value(self, locator: str, value: str) -> None:
        self.page.locator(locator).select_option(value=value)

    # --- Playwright-specific extras beyond the common interface ---

    def get_attribute(self, locator: str, attribute: str) -> str:
        return self.page.locator(locator).get_attribute(attribute) or ""

    def hover(self, locator: str) -> None:
        self.page.locator(locator).hover()

    def evaluate(self, script: str, *args):
        return self.page.evaluate(script, *args)
