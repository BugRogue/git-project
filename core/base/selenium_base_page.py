"""
selenium_base_page.py
======================
Base class for every Selenium-driven Page Object. Concrete pages
(pages/selenium/*.py) subclass this and add only page-specific methods
(`login()`, `add_item_to_cart()`, etc.), never raw Selenium calls — those
are delegated to `SeleniumActions`.
"""

from __future__ import annotations

from typing import Tuple

from selenium.webdriver.remote.webdriver import WebDriver

from core.utilities.logger import get_logger
from core.wrappers.selenium_actions import SeleniumActions

log = get_logger(__name__)

Locator = Tuple[str, str]


class SeleniumBasePage:
    """
    Generic base page exposing driver-agnostic-looking interaction methods
    (click, type_text, get_text, ...) that are actually backed by Selenium.

    Every concrete Selenium page object should inherit from this class:

        class LoginPage(SeleniumBasePage):
            def login(self, username, password):
                self.type_text(USERNAME_INPUT, username)
                self.type_text(PASSWORD_INPUT, password)
                self.click(LOGIN_BUTTON)
    """

    def __init__(self, driver: WebDriver):
        self.driver = driver
        self.actions = SeleniumActions(driver)

    # --- Generic interaction wrappers (delegate to SeleniumActions) ---

    def click(self, locator: Locator) -> None:
        self.actions.click(locator)

    def type_text(self, locator: Locator, text: str, clear_first: bool = True) -> None:
        self.actions.type_text(locator, text, clear_first)

    def get_text(self, locator: Locator) -> str:
        return self.actions.get_text(locator)

    def is_displayed(self, locator: Locator) -> bool:
        return self.actions.is_displayed(locator)

    def get_elements(self, locator: Locator):
        return self.actions.get_elements(locator)

    def get_attribute(self, locator: Locator, attribute: str) -> str:
        return self.actions.get_attribute(locator, attribute)

    def hover(self, locator: Locator) -> None:
        self.actions.hover(locator)

    def select_dropdown_by_value(self, locator: Locator, value: str) -> None:
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
        self.driver.refresh()

    def go_back(self) -> None:
        self.driver.back()
