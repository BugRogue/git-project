"""
playwright_base_page.py
========================
Base class for every Playwright-driven Page Object. Mirrors the public
method surface of `SeleniumBasePage` as closely as Playwright's model
allows, so migrating/porting a page object between engines (see
tests/migration/) mostly means swapping the base class and locator
strings/tuples.
"""

from __future__ import annotations

from playwright.sync_api import Page

from core.utilities.logger import get_logger
from core.wrappers.playwright_actions import PlaywrightActions

log = get_logger(__name__)


class PlaywrightBasePage:
    """
    Generic base page exposing the same interaction surface as
    `SeleniumBasePage`, backed by Playwright.

        class LoginPage(PlaywrightBasePage):
            def login(self, username, password):
                self.type_text(USERNAME_INPUT, username)
                self.type_text(PASSWORD_INPUT, password)
                self.click(LOGIN_BUTTON)
    """

    def __init__(self, page: Page):
        self.page = page
        self.actions = PlaywrightActions(page)

    # --- Generic interaction wrappers (delegate to PlaywrightActions) ---

    def click(self, locator: str) -> None:
        self.actions.click(locator)

    def type_text(self, locator: str, text: str, clear_first: bool = True) -> None:
        self.actions.type_text(locator, text, clear_first)

    def get_text(self, locator: str) -> str:
        return self.actions.get_text(locator)

    def is_displayed(self, locator: str) -> bool:
        return self.actions.is_displayed(locator)

    def get_elements(self, locator: str):
        return self.actions.get_elements(locator)

    def get_attribute(self, locator: str, attribute: str) -> str:
        return self.actions.get_attribute(locator, attribute)

    def hover(self, locator: str) -> None:
        self.actions.hover(locator)

    def select_dropdown_by_value(self, locator: str, value: str) -> None:
        self.actions.select_dropdown_by_value(locator, value)

    # --- Page/browser-level helpers ---

    def navigate_to(self, url: str) -> None:
        self.actions.navigate_to(url)

    def get_current_url(self) -> str:
        return self.actions.get_current_url()

    def get_title(self) -> str:
        return self.actions.get_title()

    def refresh(self) -> None:
        log.info("Refreshing page.")
        self.page.reload()

    def go_back(self) -> None:
        self.page.go_back()
