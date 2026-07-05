"""
inventory_page.py (Selenium)
=============================
Page Object for the SauceDemo post-login inventory/products page.
"""

from __future__ import annotations

from selenium.webdriver.remote.webdriver import WebDriver

from core.base.selenium_base_page import SeleniumBasePage
from locators.inventory_locators import InventoryLocatorsSelenium as L


class InventoryPage(SeleniumBasePage):
    """Encapsulates interactions with the post-login products/inventory page."""

    def __init__(self, driver: WebDriver):
        super().__init__(driver)

    def get_page_title(self) -> str:
        """Return the "Products" heading text, used to confirm successful login."""
        return self.get_text(L.PAGE_TITLE)

    def is_inventory_displayed(self) -> bool:
        """Return True if at least one inventory item is rendered."""
        items = self.get_elements(L.INVENTORY_ITEMS)
        return len(items) > 0

    def logout(self) -> None:
        """Open the hamburger menu and click logout."""
        self.click(L.MENU_BUTTON)
        self.click(L.LOGOUT_LINK)
