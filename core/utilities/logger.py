"""
logger.py
=========
Thread-safe, singleton logging utility for the Hybrid Automation Framework.

Design notes
------------
- Uses Python's built-in `logging` module, which is inherently thread-safe at
  the handler/emit level (CPython guards stream writes with a lock).
- Implemented as a singleton (per logger name) so parallel pytest-xdist
  workers or multi-threaded Playwright/Selenium sessions do not create
  duplicate handlers or interleave malformed output.
- Writes to both a rotating file handler (logs/) and the console.
- Log directory / level are driven by config.yaml so QA can tune verbosity
  without touching code.
"""

from __future__ import annotations

import logging
import os
import threading
from datetime import datetime
from logging.handlers import RotatingFileHandler
from typing import Dict, Optional

from core.utilities.data_reader import DataReader


class LoggerFactory:
    """
    Singleton factory that produces named, pre-configured `logging.Logger`
    instances shared safely across threads and test workers.
    """

    _loggers: Dict[str, logging.Logger] = {}
    _lock: threading.RLock = threading.RLock()
    _initialized_dirs: set = set()

    @classmethod
    def get_logger(cls, name: str = "automation_framework") -> logging.Logger:
        """
        Return a thread-safe, singleton logger instance for the given name.

        Args:
            name: Logical logger name, typically `__name__` of the caller.

        Returns:
            A fully configured `logging.Logger` instance.
        """
        if name in cls._loggers:
            return cls._loggers[name]

        with cls._lock:
            # Double-checked locking to avoid race conditions across threads.
            if name in cls._loggers:
                return cls._loggers[name]

            logger = logging.getLogger(name)
            config = cls._load_config()
            log_level = getattr(logging, config.get("log_level", "INFO"), logging.INFO)
            logger.setLevel(log_level)
            logger.propagate = False  # prevent duplicate logs via root logger

            if not logger.handlers:
                log_dir = config.get("log_dir", "logs")
                cls._ensure_log_dir(log_dir)

                formatter = logging.Formatter(
                    fmt="%(asctime)s | %(levelname)-8s | %(threadName)-15s | "
                        "%(name)s | %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S",
                )

                timestamp = datetime.now().strftime("%Y%m%d")
                file_path = os.path.join(log_dir, f"execution_{timestamp}.log")

                file_handler = RotatingFileHandler(
                    file_path, maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"
                )
                file_handler.setFormatter(formatter)
                file_handler.setLevel(log_level)

                console_handler = logging.StreamHandler()
                console_handler.setFormatter(formatter)
                console_handler.setLevel(log_level)

                logger.addHandler(file_handler)
                logger.addHandler(console_handler)

            cls._loggers[name] = logger
            return logger

    @classmethod
    def _ensure_log_dir(cls, log_dir: str) -> None:
        """Create the log directory once, guarded for concurrent workers."""
        if log_dir in cls._initialized_dirs:
            return
        with cls._lock:
            os.makedirs(log_dir, exist_ok=True)
            cls._initialized_dirs.add(log_dir)

    @staticmethod
    def _load_config() -> dict:
        """Fetch the `reporting` section from config.yaml, with safe fallback."""
        try:
            config = DataReader.read_yaml("config/config.yaml")
            return config.get("reporting", {})
        except Exception:
            # Fallback keeps the logger usable even if config is missing,
            # e.g. during isolated unit tests of the logger itself.
            return {"log_dir": "logs", "log_level": "INFO"}


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Convenience module-level accessor so callers can simply do:
        from core.utilities.logger import get_logger
        log = get_logger(__name__)
    """
    return LoggerFactory.get_logger(name or "automation_framework")
