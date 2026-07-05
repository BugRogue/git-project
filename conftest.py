"""
conftest.py
===========
Root pytest configuration: fixtures for driver lifecycle, and hooks for
automatic screenshot capture on test failure (engine-agnostic).

Design notes
------------
- `driver` / `page` fixtures are intentionally thin: they call
  `DriverManager.get_driver()` / `DriverManager.quit_driver()`, keeping all
  engine-branching logic inside the driver factory layer rather than here.
- The `pytest_runtest_makereport` hook inspects the test outcome and, on
  failure, pulls the active thread-local session from `BrowserManager` to
  capture a screenshot — this works identically for both engines because
  `ScreenshotUtility.capture()` branches on the object's API shape.
- `execution_engine` is read once per session via config.yaml, so tests can
  reference `request.config.stash` (or just re-read config directly) to
  know which engine they're running under, e.g. for engine-specific skips.
"""

from __future__ import annotations

import os
from typing import Generator

import pytest

from core.driver_factory.browser_manager import BrowserManager
from core.driver_factory.driver_manager import DriverManager
from core.utilities.data_reader import DataReader
from core.utilities.logger import get_logger
from core.utilities.screenshot import ScreenshotUtility

log = get_logger(__name__)


# ---------------------------------------------------------------------------
# Session-scoped setup
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session", autouse=True)
def _ensure_report_directories() -> None:
    """Create reports/screenshots/logs directories once per test session."""
    config = DataReader.read_yaml("config/config.yaml").get("reporting", {})
    for directory in (
        config.get("report_dir", "reports"),
        config.get("screenshot_dir", "screenshots"),
        config.get("log_dir", "logs"),
    ):
        os.makedirs(directory, exist_ok=True)


# ---------------------------------------------------------------------------
# Function-scoped driver fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def driver() -> Generator:
    """
    Selenium fixture: yields a live `WebDriver` instance for the test,
    then tears it down. Use in tests/selenium/*.py.
    """
    session = DriverManager.get_driver()
    yield session
    DriverManager.quit_driver()


@pytest.fixture
def page() -> Generator:
    """
    Playwright fixture: yields the active `Page` object for the test,
    then tears down the full playwright/browser/context stack.
    Use in tests/playwright/*.py.
    """
    session = DriverManager.get_driver()
    yield session.page
    DriverManager.quit_driver()


# ---------------------------------------------------------------------------
# Failure screenshot hook (engine-agnostic)
# ---------------------------------------------------------------------------

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    Wraps each test phase report. On failure during the 'call' phase,
    captures a screenshot from whatever driver/session is currently
    registered in BrowserManager for this thread, and attaches the path
    to the test node for visibility in reports/console output.
    """
    outcome = yield
    report = outcome.get_result()

    if report.when != "call" or not report.failed:
        return

    config = DataReader.read_yaml("config/config.yaml").get("reporting", {})
    if not config.get("screenshot_on_failure", True):
        return

    session = BrowserManager.get_session()
    if session is None:
        return

    # Resolve the underlying driver/page object regardless of engine.
    target = getattr(session, "page", session)  # PlaywrightSession has .page

    screenshot_path = ScreenshotUtility.capture(target, item.nodeid)
    if screenshot_path:
        log.error("Test '%s' FAILED. Screenshot: %s", item.nodeid, screenshot_path)
        report.sections.append(("Screenshot", screenshot_path))
