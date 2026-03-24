"""Utilities for listing available LLM models per LangChain backend.

Note: This module imports the underlying SDKs (google.genai, openai, anthropic)
directly rather than through LangChain wrappers, because the LangChain wrapper
libraries do not expose model-listing APIs. These imports are deferred inside
each function so they only trigger when model listing is actually needed
(e.g. to provide helpful error messages on NOT_FOUND errors).
"""

from __future__ import annotations

from ._exceptions import (
    ANTHROPIC_AUTH_ERRORS,
    CONNECTION_ERRORS,
    GOOGLE_CLIENT_ERRORS,
    OPENAI_AUTH_ERRORS,
    is_google_auth_error,
    raise_auth_error,
    raise_connection_error,
)
from ._ssl import ensure_truststore


def list_gemini_models(api_key: str | None) -> list[str]:
    """Return model names supporting generateContent for the given Gemini API key.

    Returns short names without the 'models/' prefix, matching the format
    expected by ``[llm.langchain] model = "..."`` in config.toml.

    Args:
        api_key: Gemini API key, or None to use default credentials.

    Returns:
        List of model name strings available for the given key.

    Raises:
        ImportError: If google-genai is not installed (part of mcp-coder[langchain]).
        LLMAuthError: If the API key is invalid or unauthorized.
        LLMConnectionError: If the connection to the Gemini API fails.
    """
    try:
        import google.genai as genai  # pylint: disable=import-error
    except ImportError as exc:
        raise ImportError(
            "google-genai is required to list Gemini models.\n"
            "Install with: pip install 'mcp-coder[langchain]'"
        ) from exc
    ensure_truststore()
    try:
        client = genai.Client(api_key=api_key)
        return [
            m.name.removeprefix("models/")
            for m in client.models.list()
            if m.name is not None and "generateContent" in (m.supported_actions or [])
        ]
    except GOOGLE_CLIENT_ERRORS as exc:
        if is_google_auth_error(exc):
            raise_auth_error("Gemini", "GEMINI_API_KEY", exc)
        raise_connection_error("Gemini", "GEMINI_API_KEY", exc)
    except CONNECTION_ERRORS as exc:
        raise_connection_error("Gemini", "GEMINI_API_KEY", exc)


def list_openai_models(api_key: str | None, endpoint: str | None = None) -> list[str]:
    """Return model IDs available for the given OpenAI API key.

    Args:
        api_key: OpenAI API key, or None to use default credentials.
        endpoint: Optional custom base URL for the API.

    Returns:
        Sorted list of model ID strings.

    Raises:
        ImportError: If openai is not installed (part of mcp-coder[langchain]).
        LLMAuthError: If the API key is invalid or unauthorized.
        LLMConnectionError: If the connection to the OpenAI API fails.
    """
    try:
        import openai  # pylint: disable=import-outside-toplevel
    except ImportError as exc:
        raise ImportError(
            "openai is required to list OpenAI models.\n"
            "Install with: pip install 'mcp-coder[langchain]'"
        ) from exc
    ensure_truststore()
    try:
        client = openai.OpenAI(
            api_key=api_key if api_key else None,
            base_url=endpoint if endpoint else None,
        )
        return sorted(m.id for m in client.models.list())
    except OPENAI_AUTH_ERRORS as exc:
        raise_auth_error("OpenAI", "OPENAI_API_KEY", exc)
    except CONNECTION_ERRORS as exc:
        raise_connection_error(
            "OpenAI",
            "OPENAI_API_KEY",
            exc,
            endpoint_hint="endpoint/base_url if using a custom server",
        )


def list_anthropic_models(api_key: str | None) -> list[str]:
    """Return model IDs available for the given Anthropic API key.

    Args:
        api_key: Anthropic API key, or None to use default credentials.

    Returns:
        Sorted list of model ID strings.

    Raises:
        ImportError: If anthropic is not installed (part of mcp-coder[langchain]).
        LLMAuthError: If the API key is invalid or unauthorized.
        LLMConnectionError: If the connection to the Anthropic API fails.
    """
    try:
        import anthropic  # pylint: disable=import-outside-toplevel
    except ImportError as exc:
        raise ImportError(
            "anthropic is required to list Anthropic models.\n"
            "Install with: pip install 'mcp-coder[langchain]'"
        ) from exc
    ensure_truststore()
    try:
        client = anthropic.Anthropic(
            api_key=api_key if api_key else None,
        )
        return sorted(m.id for m in client.models.list())
    except ANTHROPIC_AUTH_ERRORS as exc:
        raise_auth_error("Anthropic", "ANTHROPIC_API_KEY", exc)
    except CONNECTION_ERRORS as exc:
        raise_connection_error("Anthropic", "ANTHROPIC_API_KEY", exc)
