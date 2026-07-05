"""
login_locators.py
==================
Centralized locators for the SauceDemo login page.

Two locator formats are exposed side by side:
  - `By.*` tuples for Selenium (consumed as `(By.ID, "value")`)
  - CSS selector strings for Playwright (consumed directly by `page.locator()`)

Keeping both in one file avoids hunting across two page-object trees when
the DOM changes, and makes the "same element, two engines" relationship
explicit.
"""

from __future__ import annotations

from selenium.webdriver.common.by import By


class LoginLocatorsSelenium:
    """Selenium `By` tuples for the SauceDemo login page."""
    USERNAME_INPUT = (By.ID, "user-name")
    PASSWORD_INPUT = (By.ID, "password")
    LOGIN_BUTTON = (By.ID, "login-button")
    ERROR_MESSAGE = (By.CSS_SELECTOR, "h3[data-test='error']")
    LOGO = (By.CLASS_NAME, "app_logo")


class LoginLocatorsPlaywright:
    """Playwright CSS selectors for the SauceDemo login page."""
    USERNAME_INPUT = "#user-name"
    PASSWORD_INPUT = "#password"
    LOGIN_BUTTON = "#login-button"
    ERROR_MESSAGE = "h3[data-test='error']"
    LOGO = ".app_logo"
