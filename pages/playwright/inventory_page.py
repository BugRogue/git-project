"""
inventory_page.py (Playwright)
================================
Page Object for the SauceDemo post-login inventory/products page.
"""

from __future__ import annotations

from playwright.sync_api import Page

from core.base.playwright_base_page import PlaywrightBasePage
from locators.inventory_locators import InventoryLocatorsPlaywright as L


class InventoryPage(PlaywrightBasePage):
    """Encapsulates interactions with the post-login products/inventory page."""

    def __init__(self, page: Page):
        super().__init__(page)

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
