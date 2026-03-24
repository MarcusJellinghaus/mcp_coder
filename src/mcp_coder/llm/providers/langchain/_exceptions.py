"""Custom exceptions, error tuples, and message helpers for LangChain providers.

Single source of truth for error detection and user-facing error messaging.
All subsequent provider modules import from here.
"""

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
