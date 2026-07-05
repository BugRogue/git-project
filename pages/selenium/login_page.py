"""
login_page.py (Selenium)
========================
Page Object for the SauceDemo login screen, Selenium implementation.
"""

from __future__ import annotations

from selenium.webdriver.remote.webdriver import WebDriver

from core.base.selenium_base_page import SeleniumBasePage
from locators.login_locators import LoginLocatorsSelenium as L


class LoginPage(SeleniumBasePage):
    """Encapsulates all interactions with the SauceDemo login page."""

    def __init__(self, driver: WebDriver):
        super().__init__(driver)

    def open(self, base_url: str) -> "LoginPage":
        """Navigate to the login page."""
        self.navigate_to(base_url)
        return self

    def login(self, username: str, password: str) -> None:
        """
        Perform a full login flow: enter credentials and submit.

        Args:
            username: SauceDemo username (e.g. 'standard_user').
            password: SauceDemo password (e.g. 'secret_sauce').
        """
        self.type_text(L.USERNAME_INPUT, username)
        self.type_text(L.PASSWORD_INPUT, password)
        self.click(L.LOGIN_BUTTON)

    def get_error_message(self) -> str:
        """Return the login error banner text (e.g. for locked_out_user)."""
        return self.get_text(L.ERROR_MESSAGE)

    def is_logo_displayed(self) -> bool:
        """Return True if the SauceDemo logo is visible (page loaded correctly)."""
        return self.is_displayed(L.LOGO)
