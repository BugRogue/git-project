"""
selenium_actions.py
====================
Concrete `CommonActions` implementation backed by Selenium WebDriver.
Every method is wrapped with retry + explicit-wait handling so page objects
never need to import `WebDriverWait` or exception classes directly.
"""

from __future__ import annotations

from typing import List, Tuple

from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import Select

from core.utilities.logger import get_logger
from core.utilities.retry import retry_on_failure
from core.utilities.wait import SeleniumWait
from core.wrappers.common_actions import CommonActions

log = get_logger(__name__)

Locator = Tuple[str, str]  # e.g. (By.ID, "user-name")


class SeleniumActions(CommonActions):
    """Selenium-backed implementation of the generic action interface."""

    def __init__(self, driver: WebDriver):
        self.driver = driver
        self.wait = SeleniumWait(driver)

    @retry_on_failure()
    def click(self, locator: Locator) -> None:
        log.info("Clicking element: %s", locator)
        element = self.wait.until_clickable(locator)
        element.click()

    @retry_on_failure()
    def type_text(self, locator: Locator, text: str, clear_first: bool = True) -> None:
        log.info("Typing '%s' into element: %s", text, locator)
        element = self.wait.until_visible(locator)
        if clear_first:
            element.clear()
        element.send_keys(text)

    @retry_on_failure()
    def get_text(self, locator: Locator) -> str:
        element = self.wait.until_visible(locator)
        text = element.text
        log.debug("Retrieved text '%s' from element: %s", text, locator)
        return text

    def is_displayed(self, locator: Locator) -> bool:
        try:
            element = self.wait.until_visible(locator)
            return element.is_displayed()
        except Exception:
            return False

    def get_elements(self, locator: Locator) -> List[WebElement]:
        self.wait.until_present(locator)
        return self.driver.find_elements(*locator)

    def navigate_to(self, url: str) -> None:
        log.info("Navigating to URL: %s", url)
        self.driver.get(url)

    def get_current_url(self) -> str:
        return self.driver.current_url

    def get_title(self) -> str:
        return self.driver.title

    @retry_on_failure()
    def select_dropdown_by_value(self, locator: Locator, value: str) -> None:
        element = self.wait.until_visible(locator)
        Select(element).select_by_value(value)

    # --- Selenium-specific extras beyond the common interface ---

    def get_attribute(self, locator: Locator, attribute: str) -> str:
        element = self.wait.until_present(locator)
        return element.get_attribute(attribute) or ""

    def hover(self, locator: Locator) -> None:
        from selenium.webdriver.common.action_chains import ActionChains
        element = self.wait.until_visible(locator)
        ActionChains(self.driver).move_to_element(element).perform()

    def execute_script(self, script: str, *args) -> object:
        return self.driver.execute_script(script, *args)
