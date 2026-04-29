"""Tests for mcp_coder.utils.ssl_setup.

Tests ensure_truststore() idempotent helper for optional
OS certificate store integration.
"""

import logging
from collections.abc import Generator
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.utils import ssl_setup
from mcp_coder.utils.ssl_setup import ensure_truststore


@pytest.fixture(autouse=True)
def _reset_injected() -> Generator[None, None, None]:
    """Reset the global _injected flag before and after each test.

    The CLI entry call (Step 3) flips this flag to True for the lifetime of
    the pytest worker process; without this fixture, tests after CLI tests
    in the same xdist worker would see an already-injected state.
    """
    ssl_setup._injected = False
    yield
    ssl_setup._injected = False


class TestEnsureTruststore:
    """Tests for ensure_truststore() helper."""

    def test_calls_inject_when_truststore_available(self) -> None:
        """When truststore is installed, inject_into_ssl() is called."""
        mock_truststore = MagicMock()
        with patch.dict("sys.modules", {"truststore": mock_truststore}):
            ensure_truststore()
        mock_truststore.inject_into_ssl.assert_called_once()

    def test_noop_when_truststore_not_installed(self) -> None:
        """When truststore is not installed, no crash occurs."""
        # Setting sys.modules entry to None causes import to raise ImportError
        with patch.dict("sys.modules", {"truststore": None}):
            ensure_truststore()  # Should not raise
        # _injected should remain False
        assert ssl_setup._injected is False

    def test_idempotent_only_calls_once(self) -> None:
        """Calling ensure_truststore() twice only calls inject_into_ssl() once."""
        mock_truststore = MagicMock()
        with patch.dict("sys.modules", {"truststore": mock_truststore}):
            ensure_truststore()
            ensure_truststore()
        mock_truststore.inject_into_ssl.assert_called_once()

    def test_logs_activation_on_first_call(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """First call logs a debug message mentioning truststore."""
        mock_truststore = MagicMock()
        with (
            patch.dict("sys.modules", {"truststore": mock_truststore}),
            caplog.at_level(logging.DEBUG, logger="mcp_coder.utils.ssl_setup"),
        ):
            ensure_truststore()
        assert any("truststore" in record.message for record in caplog.records)

    def test_does_not_log_on_second_call(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Second call does not produce a debug log."""
        mock_truststore = MagicMock()
        with (
            patch.dict("sys.modules", {"truststore": mock_truststore}),
            caplog.at_level(logging.DEBUG, logger="mcp_coder.utils.ssl_setup"),
        ):
            ensure_truststore()
            caplog.clear()
            ensure_truststore()
        assert not any("truststore" in record.message for record in caplog.records)
