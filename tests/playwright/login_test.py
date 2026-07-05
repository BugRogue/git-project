"""
login_test.py (Playwright)
============================
Sample end-to-end test: logs into SauceDemo using the Playwright engine and
verifies a successful redirect to the inventory ("Products") page.
Mirrors tests/selenium/login_test.py so the two suites demonstrate true
functional parity across engines.

Run with:
    pytest tests/playwright/login_test.py -m playwright
(ensure config.yaml -> execution_engine: "playwright")
"""

from __future__ import annotations

import pytest

from core.base.playwright_base_test import PlaywrightBaseTest
from core.utilities.assertions import Assertions
from pages.playwright.inventory_page import InventoryPage
from pages.playwright.login_page import LoginPage


@pytest.mark.playwright
@pytest.mark.smoke
class TestPlaywrightLogin(PlaywrightBaseTest):
    """Smoke test suite for SauceDemo authentication (Playwright engine)."""

    def test_valid_login_redirects_to_inventory(self) -> None:
        """
        Verify that a standard user can log in and is redirected to the
        inventory page, confirmed by URL fragment and page title.
        """
        credentials = self.env_users["standard_user"]

        login_page = LoginPage(self.page)
        login_page.open(self.base_url)
        login_page.login(credentials["username"], credentials["password"])

        inventory_page = InventoryPage(self.page)

        Assertions.assert_url_contains(
            inventory_page.get_current_url(),
            "inventory.html",
            message="Expected redirect to inventory page after login",
        )
        Assertions.assert_equal(
            inventory_page.get_page_title(),
            "Products",
            message="Inventory page title mismatch after login",
        )
        Assertions.assert_true(
            inventory_page.is_inventory_displayed(),
            message="Expected inventory items to be visible after login",
        )

    def test_locked_out_user_sees_error(self) -> None:
        """Verify a locked-out user is blocked with the expected error message."""
        credentials = self.env_users["locked_out_user"]

        login_page = LoginPage(self.page)
        login_page.open(self.base_url)
        login_page.login(credentials["username"], credentials["password"])

        Assertions.assert_contains(
            login_page.get_error_message(),
            "locked out",
            message="Expected locked-out error message to be displayed",
        )
