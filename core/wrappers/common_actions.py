"""
common_actions.py
==================
Abstract interface defining the generic interaction contract that both
`SeleniumActions` and `PlaywrightActions` must implement. `BasePage`
subclasses (selenium_base_page.py / playwright_base_page.py) depend only
on this interface, which is what allows page objects and tests to be
written once and be largely engine-agnostic.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, List


class CommonActions(ABC):
    """Engine-agnostic interaction contract for UI automation actions."""

    @abstractmethod
    def click(self, locator: Any) -> None:
        """Click the element identified by `locator`."""

    @abstractmethod
    def type_text(self, locator: Any, text: str, clear_first: bool = True) -> None:
        """Type `text` into the element identified by `locator`."""

    @abstractmethod
    def get_text(self, locator: Any) -> str:
        """Return the visible text of the element identified by `locator`."""

    @abstractmethod
    def is_displayed(self, locator: Any) -> bool:
        """Return True if the element is visible on the page."""

    @abstractmethod
    def get_elements(self, locator: Any) -> List[Any]:
        """Return all elements matching `locator`."""

    @abstractmethod
    def navigate_to(self, url: str) -> None:
        """Navigate the browser to `url`."""

    @abstractmethod
    def get_current_url(self) -> str:
        """Return the current page URL."""

    @abstractmethod
    def get_title(self) -> str:
        """Return the current page title."""

    @abstractmethod
    def select_dropdown_by_value(self, locator: Any, value: str) -> None:
        """Select an <select> option by its `value` attribute."""
