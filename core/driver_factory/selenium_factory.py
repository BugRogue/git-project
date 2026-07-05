"""
selenium_factory.py
====================
Concrete factory responsible for instantiating and configuring a Selenium
`WebDriver` instance for the requested browser, using Selenium Manager
(built into Selenium 4.6+) for automatic driver binary resolution — no
manual chromedriver/geckodriver path management required.
"""

from __future__ import annotations

from typing import Any, Dict

from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions

from core.utilities.data_reader import DataReader
from core.utilities.logger import get_logger

log = get_logger(__name__)


class SeleniumFactory:
    """Builds fully configured Selenium `WebDriver` instances."""

    @staticmethod
    def create_driver() -> webdriver.Remote:
        """
        Create and return a Selenium WebDriver instance based on
        config.yaml (browser, headless, remote) and
        browser_capabilities.yaml (launch arguments/preferences).

        Returns:
            A ready-to-use `selenium.webdriver` instance with timeouts applied.
        """
        config = DataReader.read_yaml("config/config.yaml")
        capabilities = DataReader.get_browser_capabilities().get("selenium", {})
        browser = config.get("browser", "chrome").lower()
        headless = config.get("headless", True)
        remote_cfg = config.get("remote", {})

        log.info("Creating Selenium driver | browser=%s headless=%s", browser, headless)

        options = SeleniumFactory._build_options(browser, headless, capabilities.get(browser, {}))

        if remote_cfg.get("enabled", False):
            driver = webdriver.Remote(command_executor=remote_cfg["hub_url"], options=options)
            log.info("Connected to remote Selenium Grid at %s", remote_cfg["hub_url"])
        else:
            driver_map = {
                "chrome": webdriver.Chrome,
                "firefox": webdriver.Firefox,
                "edge": webdriver.Edge,
            }
            driver_cls = driver_map.get(browser)
            if driver_cls is None:
                raise ValueError(f"Unsupported Selenium browser: '{browser}'")
            driver = driver_cls(options=options)

        SeleniumFactory._apply_timeouts(driver, config.get("timeouts", {}))

        if config.get("maximize_window", True) and not headless:
            driver.maximize_window()

        log.info("Selenium driver created successfully.")
        return driver

    @staticmethod
    def _build_options(browser: str, headless: bool, browser_caps: Dict[str, Any]):
        """Translate browser_capabilities.yaml into engine-specific Options objects."""
        if browser == "chrome":
            options = ChromeOptions()
            for arg in browser_caps.get("arguments", []):
                options.add_argument(arg)
            for key, value in browser_caps.get("experimental_options", {}).items():
                options.add_experimental_option(key, value)
            if headless:
                options.add_argument("--headless=new")
            return options

        if browser == "firefox":
            options = FirefoxOptions()
            for arg in browser_caps.get("arguments", []):
                options.add_argument(arg)
            for key, value in browser_caps.get("preferences", {}).items():
                options.set_preference(key, value)
            if headless:
                options.add_argument("-headless")
            return options

        if browser == "edge":
            options = EdgeOptions()
            for arg in browser_caps.get("arguments", []):
                options.add_argument(arg)
            if headless:
                options.add_argument("--headless=new")
            return options

        raise ValueError(f"Unsupported Selenium browser: '{browser}'")

    @staticmethod
    def _apply_timeouts(driver: webdriver.Remote, timeouts: Dict[str, Any]) -> None:
        driver.implicitly_wait(timeouts.get("implicit_wait", 5))
        driver.set_page_load_timeout(timeouts.get("page_load_timeout", 30))
        driver.set_script_timeout(timeouts.get("script_timeout", 30))
