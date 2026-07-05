"""
browser_manager.py
===================
Thread-local storage manager for active driver/session instances.

Why this exists
---------------
When tests run in parallel via `pytest-xdist` (multiple worker processes)
combined with in-process threading (e.g. data-driven tests using
ThreadPoolExecutor) or simply many sequential pytest fixtures, each test
must get its own isolated browser instance. Storing the active
driver/session in a `threading.local()` container guarantees:
  1. No cross-test contamination of browser state.
  2. Safe concurrent access without explicit locking for reads/writes,
     since each thread only ever sees its own slot.

`driver_manager.py` delegates all "current session" bookkeeping to this
class; it does not know about threading internals itself.
"""

from __future__ import annotations

import threading
from typing import Any, Optional

from core.utilities.logger import get_logger

log = get_logger(__name__)


class BrowserManager:
    """Thread-local registry of the active driver/session per test thread."""

    _local = threading.local()

    @classmethod
    def set_session(cls, session: Any) -> None:
        """Register the active session (WebDriver or PlaywrightSession) for this thread."""
        cls._local.session = session
        log.debug(
            "Session registered for thread '%s': %s",
            threading.current_thread().name, type(session).__name__,
        )

    @classmethod
    def get_session(cls) -> Optional[Any]:
        """Return the active session for the current thread, or None if unset."""
        return getattr(cls._local, "session", None)

    @classmethod
    def clear_session(cls) -> None:
        """Remove the session reference for the current thread (post-teardown)."""
        if hasattr(cls._local, "session"):
            log.debug("Clearing session for thread '%s'", threading.current_thread().name)
            del cls._local.session
