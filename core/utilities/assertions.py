"""
assertions.py
=============
Soft/hard assertion wrapper that logs every assertion outcome (pass or fail)
before raising, so failures are traceable in the log file even when pytest's
own traceback is truncated in CI console output.
"""

from __future__ import annotations

from typing import Any, List

from core.utilities.logger import get_logger

log = get_logger(__name__)


class Assertions:
    """
    Hard assertion helpers. Each method logs the check, then raises a
    standard `AssertionError` on failure so pytest reporting is unaffected.
    """

    @staticmethod
    def assert_equal(actual: Any, expected: Any, message: str = "") -> None:
        log.info("ASSERT_EQUAL | actual='%s' expected='%s' | %s", actual, expected, message)
        assert actual == expected, (
            f"{message} | Expected: '{expected}', Actual: '{actual}'"
        )

    @staticmethod
    def assert_true(condition: bool, message: str = "") -> None:
        log.info("ASSERT_TRUE | condition=%s | %s", condition, message)
        assert condition, f"{message} | Expected condition to be True"

    @staticmethod
    def assert_contains(container: Any, member: Any, message: str = "") -> None:
        log.info("ASSERT_CONTAINS | container='%s' member='%s' | %s", container, member, message)
        assert member in container, (
            f"{message} | Expected '{member}' to be present in '{container}'"
        )

    @staticmethod
    def assert_url_contains(actual_url: str, fragment: str, message: str = "") -> None:
        log.info("ASSERT_URL_CONTAINS | url='%s' fragment='%s'", actual_url, fragment)
        assert fragment in actual_url, (
            f"{message} | Expected URL to contain '{fragment}', got '{actual_url}'"
        )


class SoftAssertions:
    """
    Soft assertion collector: accumulates failures instead of raising
    immediately, allowing a test to verify multiple conditions in one pass
    (useful for multi-field page verifications, e.g. product listing checks).
    Call `assert_all()` at the end of the test to raise if any check failed.
    """

    def __init__(self) -> None:
        self._failures: List[str] = []

    def check_equal(self, actual: Any, expected: Any, message: str = "") -> None:
        if actual != expected:
            failure = f"{message} | Expected: '{expected}', Actual: '{actual}'"
            log.warning("SOFT_ASSERT_FAILED | %s", failure)
            self._failures.append(failure)

    def check_true(self, condition: bool, message: str = "") -> None:
        if not condition:
            failure = f"{message} | Expected condition to be True"
            log.warning("SOFT_ASSERT_FAILED | %s", failure)
            self._failures.append(failure)

    def assert_all(self) -> None:
        """Raise `AssertionError` summarizing all accumulated soft failures."""
        if self._failures:
            summary = "\n".join(f"  - {f}" for f in self._failures)
            raise AssertionError(f"Soft assertion failures ({len(self._failures)}):\n{summary}")
