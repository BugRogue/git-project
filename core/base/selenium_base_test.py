"""
selenium_base_test.py
======================
Base test class for Selenium-engine test modules (tests/selenium/*.py).
Provides a configured `WebDriver` via `self.driver`, resolved base URL,
and environment/user data, so individual test files stay focused on
business logic and assertions.

Typical usage:

    class TestLogin(SeleniumBaseTest):
        def test_valid_login(self):
            login_page = LoginPage(self.driver)
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


class SeleniumBaseTest:
    """
    Pytest-compatible base test class. Relies on the `driver` fixture
    (see conftest.py) being injected as an instance attribute via
    `pytest-selenium`-style autouse fixture, OR can be used standalone by
    calling `setup_method` manually in non-pytest contexts.
    """

    driver: Any
    base_url: str
    env_users: Dict[str, Any]

    def setup_method(self, method=None) -> None:
        """Runs before every test method: create driver, resolve config."""
        log.info("Setting up Selenium test: %s", getattr(method, "__name__", ""))
        self.driver = DriverManager.get_driver()
        env_config = DataReader.get_active_environment_config()
        self.base_url = env_config["base_url"]
        self.env_users = env_config.get("users", {})

    def teardown_method(self, method=None) -> None:
        """Runs after every test method: tear down driver."""
        log.info("Tearing down Selenium test: %s", getattr(method, "__name__", ""))
        DriverManager.quit_driver()
