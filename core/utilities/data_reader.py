"""
data_reader.py
==============
Centralized, cached file-reading utility for configuration and test data.

Supports YAML, JSON, and CSV. All reads are cached in-memory keyed by
absolute file path + modification time, so repeated fixture/page calls
(e.g. every test reading config.yaml) do not re-hit disk, while still
picking up edits made between local test runs.
"""

from __future__ import annotations

import csv
import json
import os
import threading
from typing import Any, Dict, List

import yaml


class DataReader:
    """Static utility class for reading structured test/config data files."""

    _cache: Dict[str, Any] = {}
    _lock = threading.Lock()

    @classmethod
    def read_yaml(cls, file_path: str) -> Dict[str, Any]:
        """
        Read and parse a YAML file, with caching.

        Args:
            file_path: Path to the .yaml/.yml file, relative to project root
                       or absolute.

        Returns:
            Parsed YAML content as a dictionary.

        Raises:
            FileNotFoundError: If the file does not exist.
        """
        return cls._read_cached(file_path, loader=lambda f: yaml.safe_load(f) or {})

    @classmethod
    def read_json(cls, file_path: str) -> Any:
        """Read and parse a JSON file, with caching."""
        return cls._read_cached(file_path, loader=lambda f: json.load(f))

    @classmethod
    def read_csv(cls, file_path: str) -> List[Dict[str, str]]:
        """
        Read a CSV file into a list of row dictionaries (header-keyed).

        Returns:
            List of dicts, one per data row.
        """
        def _load(f):
            return list(csv.DictReader(f))

        return cls._read_cached(file_path, loader=_load)

    @classmethod
    def _read_cached(cls, file_path: str, loader) -> Any:
        abs_path = os.path.abspath(file_path)
        if not os.path.exists(abs_path):
            raise FileNotFoundError(f"Data file not found: {abs_path}")

        mtime = os.path.getmtime(abs_path)
        cache_key = f"{abs_path}:{mtime}"

        if cache_key in cls._cache:
            return cls._cache[cache_key]

        with cls._lock:
            if cache_key in cls._cache:
                return cls._cache[cache_key]
            with open(abs_path, "r", encoding="utf-8") as f:
                data = loader(f)
            cls._cache[cache_key] = data
            return data

    @classmethod
    def get_active_environment_config(cls) -> Dict[str, Any]:
        """
        Convenience method: resolves config.yaml -> active_environment
        against environments.yaml and returns that environment's block.
        """
        config = cls.read_yaml("config/config.yaml")
        env_name = config.get("active_environment", "qa")
        environments = cls.read_yaml("config/environments.yaml")
        if env_name not in environments:
            raise KeyError(f"Environment '{env_name}' not defined in environments.yaml")
        return environments[env_name]

    @classmethod
    def get_browser_capabilities(cls) -> Dict[str, Any]:
        """Convenience method: returns the full browser_capabilities.yaml content."""
        return cls.read_yaml("config/browser_capabilities.yaml")
