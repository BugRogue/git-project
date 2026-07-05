"""
playwright_base_test.py
========================
Base test class for Playwright-engine test modules (tests/playwright/*.py).
Exposes `self.page` (the active Playwright Page) alongside `self.context`
and `self.browser` for advanced scenarios (multi-tab, storage state, etc.).

Typical usage:

    class TestLogin(PlaywrightBaseTest):
        def test_valid_login(self):
            login_page = LoginPage(self.page)
            login_page.navigate_to(self.base_url)
            login_page.login(self.env_users["standard_user"]["username"],
                              self.env_users["standard_user"]["password"])
"""

from __future__ import annotations

from typing import Any, Dict

from core.driver_factory.driver_manager import DriverManager
from core.utilities.data_reader import DataReader
from core.utilities.logger import get_logger

log = get_logger(__name__)


class PlaywrightBaseTest:
    """Pytest-compatible base test class for the Playwright engine."""

    page: Any
    context: Any
    browser: Any
    base_url: str
    env_users: Dict[str, Any]

    def setup_method(self, method=None) -> None:
        """Runs before every test method: create session, resolve config."""
        log.info("Setting up Playwright test: %s", getattr(method, "__name__", ""))
        session = DriverManager.get_driver()
        self.page = session.page
        self.context = session.context
        self.browser = session.browser

        env_config = DataReader.get_active_environment_config()
        self.base_url = env_config["base_url"]
        self.env_users = env_config.get("users", {})

    def teardown_method(self, method=None) -> None:
        """Runs after every test method: tear down session (browser/context/trace)."""
        log.info("Tearing down Playwright test: %s", getattr(method, "__name__", ""))
        DriverManager.quit_driver()
