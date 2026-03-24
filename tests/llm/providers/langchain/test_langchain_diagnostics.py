"""Tests for error classification and diagnostics in _exceptions.py.

Tests classify_connection_error(), format_diagnostics(), and
_is_connection_reset() — the diagnostic helpers added for corporate
proxy / SSL troubleshooting.
"""

import ssl
from unittest.mock import patch

import pytest

from mcp_coder.llm.providers.langchain._exceptions import (
    _is_connection_reset,
    classify_connection_error,
    format_diagnostics,
)

# Proxy env vars to clear for clean tests
_PROXY_VARS = ("HTTPS_PROXY", "https_proxy", "HTTP_PROXY", "http_proxy")


# ---------------------------------------------------------------------------
# _is_connection_reset
# ---------------------------------------------------------------------------


class TestIsConnectionReset:
    """Tests for _is_connection_reset()."""

    def test_oserror_errno_10054(self) -> None:
        """WinError 10054 detected via errno."""
        exc = OSError()
        exc.errno = 10054
        assert _is_connection_reset(exc) is True

    def test_oserror_errno_104(self) -> None:
        """Linux ECONNRESET (errno 104) detected."""
        exc = OSError()
        exc.errno = 104
        assert _is_connection_reset(exc) is True

    def test_oserror_winerror_10054(self) -> None:
        """WinError 10054 detected via winerror attribute."""
        exc = OSError()
        setattr(
            exc, "winerror", 10054
        )  # noqa: B010  # Windows-only attr; bypass type checker for cross-platform CI
        assert _is_connection_reset(exc) is True

    def test_string_connection_reset(self) -> None:
        """'connection reset' in message is detected."""
        exc = Exception("Connection reset by peer")
        assert _is_connection_reset(exc) is True

    def test_string_10054(self) -> None:
        """'10054' in message is detected."""
        exc = Exception("WinError 10054: connection forcibly closed")
        assert _is_connection_reset(exc) is True

    def test_string_econnreset(self) -> None:
        """'econnreset' in message is detected."""
        exc = Exception("ECONNRESET")
        assert _is_connection_reset(exc) is True

    def test_chained_cause(self) -> None:
        """Connection reset in __cause__ chain is detected."""
        inner = OSError()
        inner.errno = 10054
        outer = RuntimeError("wrapper")
        outer.__cause__ = inner
        assert _is_connection_reset(outer) is True

    def test_chained_context(self) -> None:
        """Connection reset in __context__ chain is detected."""
        inner = OSError()
        inner.errno = 104
        outer = RuntimeError("wrapper")
        outer.__context__ = inner
        assert _is_connection_reset(outer) is True

    def test_max_depth_exceeded(self) -> None:
        """Chain deeper than 5 is not followed (avoids unbounded walk)."""
        # Build chain of 7 generic exceptions
        exc = Exception("level0")
        current = exc
        for i in range(1, 7):
            cause = Exception(f"level{i}")
            current.__cause__ = cause
            current = cause
        # Put a reset at the very end (depth 7) — should NOT be found
        reset = OSError()
        reset.errno = 10054
        current.__cause__ = reset
        assert _is_connection_reset(exc) is False

    def test_unrelated_error(self) -> None:
        """Non-reset error returns False."""
        exc = ValueError("something else")
        assert _is_connection_reset(exc) is False


# ---------------------------------------------------------------------------
# classify_connection_error
# ---------------------------------------------------------------------------


class TestClassifyConnectionError:
    """Tests for classify_connection_error()."""

    def test_connection_reset(self) -> None:
        exc = OSError()
        exc.errno = 10054
        result = classify_connection_error(exc)
        assert "connection-reset" in result
        assert "proxy/firewall" in result

    def test_connection_refused_linux(self) -> None:
        exc = OSError()
        exc.errno = 111
        result = classify_connection_error(exc)
        assert result == "connection-refused"

    def test_connection_refused_windows(self) -> None:
        exc = OSError()
        exc.errno = 10061
        result = classify_connection_error(exc)
        assert result == "connection-refused"

    def test_connection_timeout_linux(self) -> None:
        exc = OSError()
        exc.errno = 110
        result = classify_connection_error(exc)
        assert result == "connection-timeout"

    def test_connection_timeout_windows(self) -> None:
        exc = OSError()
        exc.errno = 10060
        result = classify_connection_error(exc)
        assert result == "connection-timeout"

    def test_timeout_by_class_name(self) -> None:
        """Exception class with 'timeout' in name is classified."""

        class ConnectTimeout(Exception):
            pass

        exc = ConnectTimeout("timed out")
        result = classify_connection_error(exc)
        assert result == "connection-timeout"

    def test_ssl_by_class_name(self) -> None:
        """ssl.SSLError is classified as ssl-error."""
        exc = ssl.SSLError("certificate verify failed")
        result = classify_connection_error(exc)
        assert "ssl-error" in result

    def test_certificate_in_message(self) -> None:
        """'certificate' in message triggers ssl-error."""
        exc = Exception("certificate verify failed")
        result = classify_connection_error(exc)
        assert "ssl-error" in result

    def test_generic_fallback(self) -> None:
        """Unknown exception type falls back to generic category."""
        exc = RuntimeError("something unexpected")
        result = classify_connection_error(exc)
        assert "connection-error" in result
        assert "RuntimeError" in result


# ---------------------------------------------------------------------------
# format_diagnostics
# ---------------------------------------------------------------------------


class TestFormatDiagnostics:
    """Tests for format_diagnostics()."""

    def test_contains_error_category(self) -> None:
        exc = OSError()
        exc.errno = 10054
        result = format_diagnostics(exc)
        assert "Error category" in result
        assert "connection-reset" in result

    def test_proxy_configured_true(self) -> None:
        """Proxy status shown when HTTPS_PROXY is set."""
        exc = OSError("fail")
        with patch.dict(
            "os.environ", {"HTTPS_PROXY": "http://proxy:8080"}, clear=False
        ):
            result = format_diagnostics(exc)
        assert "Proxy configured: True" in result

    @pytest.mark.parametrize("var", _PROXY_VARS)
    def test_proxy_detected_all_variants(self, var: str) -> None:
        """Each proxy env var variant is detected."""
        exc = OSError("fail")
        env = {v: "" for v in _PROXY_VARS}
        env[var] = "http://proxy:8080"
        with patch.dict("os.environ", env, clear=False):
            # Clear all then set only our target
            import os

            for v in _PROXY_VARS:
                os.environ.pop(v, None)
            os.environ[var] = "http://proxy:8080"
            result = format_diagnostics(exc)
        assert "Proxy configured: True" in result

    def test_no_proxy_shows_hint(self) -> None:
        """When no proxy is configured, a hint is shown."""
        exc = OSError("fail")
        import os

        with patch.dict("os.environ", {}, clear=False):
            for v in _PROXY_VARS:
                os.environ.pop(v, None)
            result = format_diagnostics(exc)
        assert "Proxy configured: False" in result
        assert "HTTPS_PROXY" in result

    def test_truststore_available(self) -> None:
        """Truststore active shown when truststore is importable."""
        exc = OSError("fail")
        import os

        with patch.dict("os.environ", {}, clear=False):
            for v in _PROXY_VARS:
                os.environ.pop(v, None)
            with patch(
                "mcp_coder.llm.providers.langchain._exceptions._truststore_available",
                return_value=True,
            ):
                result = format_diagnostics(exc)
        assert "Truststore active: True" in result

    def test_truststore_not_available_shows_hint(self) -> None:
        """When truststore is absent, install hint is shown."""
        exc = OSError("fail")
        import os

        with patch.dict("os.environ", {}, clear=False):
            for v in _PROXY_VARS:
                os.environ.pop(v, None)
            with patch(
                "mcp_coder.llm.providers.langchain._exceptions._truststore_available",
                return_value=False,
            ):
                result = format_diagnostics(exc)
        assert "Truststore active: False" in result
        assert "truststore" in result.lower()
        assert "pip install" in result
