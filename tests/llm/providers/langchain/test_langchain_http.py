"""Tests for mcp_coder.llm.providers.langchain._http.

Tests the shared httpx client factory: SSL context creation,
sync/async client construction, proxy logging, and secret safety.
"""

import logging
import os
import ssl
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.llm.providers.langchain._http import (
    create_async_http_client,
    create_http_client,
    create_ssl_context,
)

_LOGGER_NAME = "mcp_coder.llm.providers.langchain._http"

# Proxy env vars that must be cleared for "no proxy" tests
_PROXY_VARS = ("HTTPS_PROXY", "https_proxy", "HTTP_PROXY", "http_proxy")


class TestCreateSslContext:
    """Tests for create_ssl_context()."""

    def test_returns_truststore_context_when_available(self) -> None:
        """When truststore is installed, SSLContext is built via truststore."""
        mock_truststore = MagicMock()
        mock_ctx = MagicMock(spec=ssl.SSLContext)
        mock_truststore.SSLContext.return_value = mock_ctx

        with patch.dict("sys.modules", {"truststore": mock_truststore}):
            result = create_ssl_context()

        mock_truststore.SSLContext.assert_called_once_with(ssl.PROTOCOL_TLS_CLIENT)
        assert result is mock_ctx

    def test_returns_default_context_when_truststore_missing(self) -> None:
        """When truststore is absent, ssl.create_default_context() is used."""
        mock_ctx = MagicMock(spec=ssl.SSLContext)
        with (
            patch.dict("sys.modules", {"truststore": None}),
            patch("ssl.create_default_context", return_value=mock_ctx) as mock_default,
        ):
            result = create_ssl_context()

        mock_default.assert_called_once()
        assert result is mock_ctx

    def test_logs_truststore_context_type(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Debug log mentions 'truststore' when truststore is available."""
        mock_truststore = MagicMock()
        with (
            patch.dict("sys.modules", {"truststore": mock_truststore}),
            caplog.at_level(logging.DEBUG, logger=_LOGGER_NAME),
        ):
            create_ssl_context()

        assert any("truststore" in r.message for r in caplog.records)

    def test_logs_default_context_type(self, caplog: pytest.LogCaptureFixture) -> None:
        """Debug log mentions 'default' when truststore is absent."""
        with (
            patch.dict("sys.modules", {"truststore": None}),
            caplog.at_level(logging.DEBUG, logger=_LOGGER_NAME),
        ):
            create_ssl_context()

        assert any("default" in r.message for r in caplog.records)


class TestCreateHttpClient:
    """Tests for create_http_client()."""

    def test_returns_httpx_client(self) -> None:
        """Return type is httpx.Client."""
        mock_ctx = MagicMock(spec=ssl.SSLContext)
        mock_httpx_mod = MagicMock()
        mock_httpx_client = MagicMock()
        mock_httpx_mod.Client.return_value = mock_httpx_client

        with (
            patch(
                "mcp_coder.llm.providers.langchain._http.create_ssl_context",
                return_value=mock_ctx,
            ),
            patch.dict("sys.modules", {"httpx": mock_httpx_mod}),
        ):
            result = create_http_client()

        assert result is mock_httpx_client

    def test_passes_ssl_context_as_verify(self) -> None:
        """httpx.Client is called with verify=<ssl_context>."""
        mock_ctx = MagicMock(spec=ssl.SSLContext)
        mock_httpx_mod = MagicMock()

        with (
            patch(
                "mcp_coder.llm.providers.langchain._http.create_ssl_context",
                return_value=mock_ctx,
            ),
            patch.dict("sys.modules", {"httpx": mock_httpx_mod}),
        ):
            create_http_client()

        mock_httpx_mod.Client.assert_called_once_with(verify=mock_ctx)

    def test_logs_proxy_configured_true(self, caplog: pytest.LogCaptureFixture) -> None:
        """Logs proxy_configured=True when HTTPS_PROXY is set."""
        mock_httpx_mod = MagicMock()
        env = {v: "" for v in _PROXY_VARS}
        env["HTTPS_PROXY"] = "http://proxy:8080"

        with (
            patch(
                "mcp_coder.llm.providers.langchain._http.create_ssl_context",
                return_value=MagicMock(spec=ssl.SSLContext),
            ),
            patch.dict("sys.modules", {"httpx": mock_httpx_mod}),
            patch.dict("os.environ", env, clear=False),
            caplog.at_level(logging.DEBUG, logger=_LOGGER_NAME),
        ):
            # Clear lowercase variants that might exist in real env
            for var in ("https_proxy", "http_proxy"):
                os.environ.pop(var, None)
            os.environ["HTTPS_PROXY"] = "http://proxy:8080"
            create_http_client()

        assert any("proxy_configured=True" in r.message for r in caplog.records)

    def test_logs_proxy_configured_true_lowercase(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Logs proxy_configured=True when https_proxy (lowercase) is set."""
        mock_httpx_mod = MagicMock()

        clean_env = {v: "" for v in _PROXY_VARS}
        with (
            patch(
                "mcp_coder.llm.providers.langchain._http.create_ssl_context",
                return_value=MagicMock(spec=ssl.SSLContext),
            ),
            patch.dict("sys.modules", {"httpx": mock_httpx_mod}),
            patch.dict("os.environ", clean_env, clear=False),
            caplog.at_level(logging.DEBUG, logger=_LOGGER_NAME),
        ):
            # Remove all proxy vars then set only lowercase
            for var in _PROXY_VARS:
                os.environ.pop(var, None)
            os.environ["https_proxy"] = "http://proxy:8080"
            create_http_client()

        assert any("proxy_configured=True" in r.message for r in caplog.records)

    def test_logs_proxy_configured_false(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Logs proxy_configured=False when no proxy env vars are set."""
        mock_httpx_mod = MagicMock()

        with (
            patch(
                "mcp_coder.llm.providers.langchain._http.create_ssl_context",
                return_value=MagicMock(spec=ssl.SSLContext),
            ),
            patch.dict("sys.modules", {"httpx": mock_httpx_mod}),
            caplog.at_level(logging.DEBUG, logger=_LOGGER_NAME),
        ):
            # Clear all proxy env vars
            for var in _PROXY_VARS:
                os.environ.pop(var, None)
            create_http_client()

        assert any("proxy_configured=False" in r.message for r in caplog.records)

    def test_never_logs_proxy_value(self, caplog: pytest.LogCaptureFixture) -> None:
        """Proxy URL (which may contain credentials) must never appear in logs."""
        mock_httpx_mod = MagicMock()
        secret_url = "http://secret:pass@proxy:8080"

        with (
            patch(
                "mcp_coder.llm.providers.langchain._http.create_ssl_context",
                return_value=MagicMock(spec=ssl.SSLContext),
            ),
            patch.dict("sys.modules", {"httpx": mock_httpx_mod}),
            caplog.at_level(logging.DEBUG, logger=_LOGGER_NAME),
        ):
            for var in _PROXY_VARS:
                os.environ.pop(var, None)
            os.environ["HTTPS_PROXY"] = secret_url
            create_http_client()

        for record in caplog.records:
            assert secret_url not in record.message


class TestCreateAsyncHttpClient:
    """Tests for create_async_http_client()."""

    def test_returns_httpx_async_client(self) -> None:
        """Return type is httpx.AsyncClient."""
        mock_ctx = MagicMock(spec=ssl.SSLContext)
        mock_httpx_mod = MagicMock()
        mock_async_client = MagicMock()
        mock_httpx_mod.AsyncClient.return_value = mock_async_client

        with (
            patch(
                "mcp_coder.llm.providers.langchain._http.create_ssl_context",
                return_value=mock_ctx,
            ),
            patch.dict("sys.modules", {"httpx": mock_httpx_mod}),
        ):
            result = create_async_http_client()

        assert result is mock_async_client

    def test_passes_ssl_context_as_verify(self) -> None:
        """httpx.AsyncClient is called with verify=<ssl_context>."""
        mock_ctx = MagicMock(spec=ssl.SSLContext)
        mock_httpx_mod = MagicMock()

        with (
            patch(
                "mcp_coder.llm.providers.langchain._http.create_ssl_context",
                return_value=mock_ctx,
            ),
            patch.dict("sys.modules", {"httpx": mock_httpx_mod}),
        ):
            create_async_http_client()

        mock_httpx_mod.AsyncClient.assert_called_once_with(verify=mock_ctx)
