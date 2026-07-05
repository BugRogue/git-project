"""
retry.py
========
Generic retry decorator with exponential backoff, driven by config.yaml's
`retry` block. Used by wrapper/action classes to absorb transient flakiness
(StaleElementReferenceException, TimeoutError, click interception, etc.)
without masking genuine functional failures.
"""

from __future__ import annotations

import functools
import time
from typing import Callable, Tuple, Type

from core.utilities.data_reader import DataReader
from core.utilities.logger import get_logger

log = get_logger(__name__)


def _resolve_exception_types(names: list) -> Tuple[Type[BaseException], ...]:
    """
    Map string exception names from config.yaml to actual exception classes,
    pulling from both Selenium and Playwright exception modules, plus builtins.
    """
    resolved = []
    candidates = {}

    try:
        from selenium.common import exceptions as sel_exc
        candidates.update(vars(sel_exc))
    except ImportError:
        pass

    candidates.setdefault("Exception", Exception)
    # Built-in TimeoutError is always a candidate for the "TimeoutError" name,
    # in addition to Playwright's own TimeoutError (they are NOT the same
    # class), so either one triggers a retry regardless of which library
    # raised it.
    candidates["TimeoutError"] = (TimeoutError,)

    try:
        from playwright.sync_api import TimeoutError as PWTimeoutError
        candidates["TimeoutError"] = candidates["TimeoutError"] + (PWTimeoutError,)
    except ImportError:
        pass

    for name in names:
        exc_cls = candidates.get(name)
        if exc_cls is None:
            continue
        if isinstance(exc_cls, tuple):
            resolved.extend(exc_cls)
        else:
            resolved.append(exc_cls)
    return tuple(resolved) if resolved else (Exception,)


def retry_on_failure(max_attempts: int = None, backoff_seconds: float = None):
    """
    Decorator factory that retries the wrapped function on configured
    exception types with linear backoff.

    Args:
        max_attempts: Overrides config.yaml -> retry.max_attempts if provided.
        backoff_seconds: Overrides config.yaml -> retry.backoff_seconds if provided.

    Usage:
        @retry_on_failure()
        def click(self, locator):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            config = DataReader.read_yaml("config/config.yaml").get("retry", {})
            attempts = max_attempts or config.get("max_attempts", 3)
            backoff = backoff_seconds or config.get("backoff_seconds", 2)
            exception_types = _resolve_exception_types(
                config.get("retry_on_exceptions", ["Exception"])
            )

            last_exception = None
            for attempt in range(1, attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exception_types as exc:
                    last_exception = exc
                    log.warning(
                        "Attempt %s/%s failed for '%s': %s",
                        attempt, attempts, func.__name__, exc,
                    )
                    if attempt < attempts:
                        time.sleep(backoff * attempt)  # linear backoff
            log.error("All %s attempts failed for '%s'.", attempts, func.__name__)
            raise last_exception

        return wrapper
    return decorator
