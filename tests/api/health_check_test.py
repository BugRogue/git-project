"""
health_check_test.py
=====================
Sample API-layer test using `requests`, independent of both browser engines.
SauceDemo has no public REST API, so this demonstrates the pattern against
its static site availability as a stand-in health check; replace with real
endpoint assertions once an API-backed service is in scope.
"""

from __future__ import annotations

import pytest
import requests

from core.utilities.data_reader import DataReader
from core.utilities.logger import get_logger

log = get_logger(__name__)


@pytest.mark.api
class TestSauceDemoAvailability:
    """Basic availability/health checks that don't require a browser engine."""

    def test_site_returns_200(self) -> None:
        """Verify the SauceDemo base URL is reachable and returns HTTP 200."""
        env_config = DataReader.get_active_environment_config()
        base_url = env_config["api_base_url"]

        response = requests.get(base_url, timeout=10)
        log.info("GET %s -> %s", base_url, response.status_code)

        assert response.status_code == 200, (
            f"Expected HTTP 200 from {base_url}, got {response.status_code}"
        )

    def test_response_contains_expected_title(self) -> None:
        """Verify the raw HTML response includes the expected page title tag."""
        env_config = DataReader.get_active_environment_config()
        base_url = env_config["api_base_url"]

        response = requests.get(base_url, timeout=10)
        assert "Swag Labs" in response.text, "Expected 'Swag Labs' title in page HTML"
