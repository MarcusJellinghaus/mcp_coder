"""Custom exceptions, error tuples, and message helpers for LangChain providers.

Single source of truth for error detection and user-facing error messaging.
All subsequent provider modules import from here.
"""

import os
from typing import NoReturn


class LLMConnectionError(ConnectionError):
    """Network, SSL, or transport failure connecting to an LLM provider."""


class LLMAuthError(Exception):
    """Authentication failure (HTTP 401/403) from an LLM provider."""


# ---------------------------------------------------------------------------
# Try-import fallback tuples
# ---------------------------------------------------------------------------

# Connection errors — httpx transport failures + OS-level socket errors
try:
    import httpx

    CONNECTION_ERRORS: tuple[type[Exception], ...] = (
        httpx.ConnectError,
        httpx.ConnectTimeout,
        OSError,
    )
except ImportError:
    CONNECTION_ERRORS = (OSError,)

# Auth errors per provider — SDK-native exception classes
try:
    import openai

    OPENAI_AUTH_ERRORS: tuple[type[Exception], ...] = (openai.AuthenticationError,)
except ImportError:
    OPENAI_AUTH_ERRORS = ()

try:
    import anthropic

    ANTHROPIC_AUTH_ERRORS: tuple[type[Exception], ...] = (
        anthropic.AuthenticationError,
    )
except ImportError:
    ANTHROPIC_AUTH_ERRORS = ()

try:
    from google.genai import errors as genai_errors

    GOOGLE_CLIENT_ERRORS: tuple[type[Exception], ...] = (genai_errors.ClientError,)
except ImportError:
    GOOGLE_CLIENT_ERRORS = ()


# ---------------------------------------------------------------------------
# Message helpers
# ---------------------------------------------------------------------------

_SSL_HINT = (
    "For SSL errors behind a corporate proxy, try:\n"
    "  pip install 'mcp-coder[truststore]'\n"
    "  or set SSL_CERT_FILE / REQUESTS_CA_BUNDLE env var to your corporate CA bundle."
)


def raise_connection_error(
    provider: str,
    env_var: str,
    original: Exception,
    endpoint_hint: str = "",
) -> NoReturn:
    """Build multi-line connection error message and raise LLMConnectionError.

    Args:
        provider: Name of the LLM provider (e.g. "OpenAI").
        env_var: Environment variable name for the API key.
        original: The original exception that triggered the error.
        endpoint_hint: Optional hint about the endpoint/base_url.

    Raises:
        LLMConnectionError: Always raised with a formatted error message.
    """
    lines = [f"Connection to {provider} API failed: {original}", "Check:"]
    item = 1
    lines.append(f"  {item}. {env_var} env var or api_key in config.toml")
    item += 1
    if endpoint_hint:
        lines.append(f"  {item}. endpoint/base_url: {endpoint_hint}")
        item += 1
    lines.append(f"  {item}. Network/firewall/proxy settings")
    lines.append(_SSL_HINT)
    raise LLMConnectionError("\n".join(lines)) from original


def raise_auth_error(
    provider: str,
    env_var: str,
    original: Exception,
) -> NoReturn:
    """Build multi-line auth error message and raise LLMAuthError.

    Args:
        provider: Name of the LLM provider (e.g. "OpenAI").
        env_var: Environment variable name for the API key.
        original: The original exception that triggered the error.

    Raises:
        LLMAuthError: Always raised with a formatted error message.
    """
    lines = [
        f"Authentication to {provider} API failed: {original}",
        "Check:",
        f"  1. {env_var} env var is set and valid",
        "  2. api_key in config.toml is correct",
    ]
    raise LLMAuthError("\n".join(lines)) from original


def is_google_auth_error(exc: Exception) -> bool:
    """Check if a google.genai ClientError is an auth error (code 401 or 403).

    Args:
        exc: The exception to check.

    Returns:
        True if the exception is a Google client error with code 401 or 403.
    """
    if not GOOGLE_CLIENT_ERRORS:
        return False
    if not isinstance(exc, GOOGLE_CLIENT_ERRORS):
        return False
    return getattr(exc, "code", None) in (401, 403)


# ---------------------------------------------------------------------------
# Error classification & diagnostics
# ---------------------------------------------------------------------------

_MAX_CHAIN_DEPTH = 5


def _is_connection_reset(exc: Exception) -> bool:
    """Check if *exc* or any chained cause is a connection-reset error.

    Walks the exception chain iteratively (max depth 5) to avoid
    unbounded recursion on pathological chains.

    Args:
        exc: The exception to inspect.

    Returns:
        ``True`` if a connection-reset indicator is found.
    """
    current: BaseException | None = exc
    for _ in range(_MAX_CHAIN_DEPTH):
        if current is None:
            break
        # WinError 10054 / errno 104 (ECONNRESET)
        if isinstance(current, OSError) and getattr(current, "errno", None) in (
            10054,
            104,
        ):
            return True
        if isinstance(current, OSError) and getattr(current, "winerror", None) == 10054:
            return True
        # Check string representation for connection reset messages
        msg = str(current).lower()
        if "connection reset" in msg or "10054" in msg or "econnreset" in msg:
            return True
        current = current.__cause__ or current.__context__
    return False


def classify_connection_error(exc: Exception) -> str:
    """Map an exception to a human-readable connection-error category.

    Args:
        exc: The connection-related exception to classify.

    Returns:
        A short human-readable category string.
    """
    if _is_connection_reset(exc):
        return "connection-reset (possible proxy/firewall interference)"

    if isinstance(exc, OSError):
        err = getattr(exc, "errno", None)
        if err in (111, 10061):  # ECONNREFUSED / WinError
            return "connection-refused"
        if err in (110, 10060):  # ETIMEDOUT / WinError
            return "connection-timeout"

    exc_name = type(exc).__name__.lower()
    if "timeout" in exc_name:
        return "connection-timeout"
    if "ssl" in exc_name or "certificate" in str(exc).lower():
        return "ssl-error (check certificates or truststore)"

    return f"connection-error ({type(exc).__name__})"


def _proxy_configured() -> bool:
    """Return ``True`` if any HTTP(S) proxy env var is set."""
    return bool(
        os.environ.get("HTTPS_PROXY")
        or os.environ.get("https_proxy")
        or os.environ.get("HTTP_PROXY")
        or os.environ.get("http_proxy")
    )


def _truststore_available() -> bool:
    """Return ``True`` if the *truststore* package can be imported."""
    try:
        import truststore  # pylint: disable=import-outside-toplevel  # noqa: F401

        return True
    except ImportError:
        return False


def format_diagnostics(exc: Exception) -> str:
    """Build a diagnostic block for a connection failure.

    Includes the error classification, proxy status, and truststore
    availability to help users self-diagnose corporate proxy / SSL issues.

    Args:
        exc: The connection-related exception.

    Returns:
        A multi-line diagnostic string.
    """
    category = classify_connection_error(exc)
    proxy = _proxy_configured()
    truststore_active = _truststore_available()
    lines = [
        f"Error category : {category}",
        f"Proxy configured: {proxy}",
        f"Truststore active: {truststore_active}",
    ]
    if not proxy:
        lines.append("Hint: If behind a corporate proxy, set HTTPS_PROXY / HTTP_PROXY.")
    if not truststore_active:
        lines.append(
            "Hint: Install truststore (pip install 'mcp-coder[truststore]') "
            "for OS certificate store support."
        )
    return "\n".join(lines)
