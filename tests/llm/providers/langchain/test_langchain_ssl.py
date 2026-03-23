"""Tests for mcp_coder.llm.providers.langchain._ssl.

Tests ensure_truststore() idempotent helper for optional
OS certificate store integration.
"""

import logging
from unittest.mock import MagicMock, patch

from mcp_coder.llm.providers.langchain import _ssl
from mcp_coder.llm.providers.langchain._ssl import ensure_truststore


class TestEnsureTruststore:
    """Tests for ensure_truststore() helper."""

    def _reset(self) -> None:
        """Reset the module-level _injected flag before each test."""
        _ssl._injected = False

    def test_calls_inject_when_truststore_available(self) -> None:
        """When truststore is installed, inject_into_ssl() is called."""
        self._reset()
        mock_truststore = MagicMock()
        with patch.dict("sys.modules", {"truststore": mock_truststore}):
            ensure_truststore()
        mock_truststore.inject_into_ssl.assert_called_once()

    def test_noop_when_truststore_not_installed(self) -> None:
        """When truststore is not installed, no crash occurs."""
        self._reset()
        # Setting sys.modules entry to None causes import to raise ImportError
        with patch.dict("sys.modules", {"truststore": None}):
            ensure_truststore()  # Should not raise
        # _injected should remain False
        assert _ssl._injected is False

    def test_idempotent_only_calls_once(self) -> None:
        """Calling ensure_truststore() twice only calls inject_into_ssl() once."""
        self._reset()
        mock_truststore = MagicMock()
        with patch.dict("sys.modules", {"truststore": mock_truststore}):
            ensure_truststore()
            ensure_truststore()
        mock_truststore.inject_into_ssl.assert_called_once()

    def test_logs_activation_on_first_call(
        self, caplog: "logging.LogCaptureFixture"
    ) -> None:
        """First call logs a debug message mentioning truststore."""
        self._reset()
        mock_truststore = MagicMock()
        with (
            patch.dict("sys.modules", {"truststore": mock_truststore}),
            caplog.at_level(
                logging.DEBUG, logger="mcp_coder.llm.providers.langchain._ssl"
            ),
        ):
            ensure_truststore()
        assert any("truststore" in record.message for record in caplog.records)

    def test_does_not_log_on_second_call(
        self, caplog: "logging.LogCaptureFixture"
    ) -> None:
        """Second call does not produce a debug log."""
        self._reset()
        mock_truststore = MagicMock()
        with (
            patch.dict("sys.modules", {"truststore": mock_truststore}),
            caplog.at_level(
                logging.DEBUG, logger="mcp_coder.llm.providers.langchain._ssl"
            ),
        ):
            ensure_truststore()
            caplog.clear()
            ensure_truststore()
        assert not any("truststore" in record.message for record in caplog.records)
