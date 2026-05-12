"""Utilities for listing available LLM models per LangChain backend.

Note: This module imports the underlying SDKs (google.genai, openai, anthropic)
directly rather than through LangChain wrappers, because the LangChain wrapper
libraries do not expose model-listing APIs. These imports are deferred inside
each function so they only trigger when model listing is actually needed
(e.g. to provide helpful error messages on NOT_FOUND errors).
"""

from __future__ import annotations

import os
from typing import Any

from ._exceptions import (
    ANTHROPIC_AUTH_ERRORS,
    CONNECTION_ERRORS,
    GOOGLE_CLIENT_ERRORS,
    OPENAI_AUTH_ERRORS,
    is_google_auth_error,
    raise_auth_error,
    raise_connection_error,
)
from ._http import create_http_client


def _resolve_ollama_host(endpoint: str | None) -> str | None:
    """Resolve OLLAMA_HOST env > endpoint config > None, normalize to URL.

    Args:
        endpoint: Optional endpoint from config (host:port or full URL).

    Returns:
        Normalized URL string (with http:// prefix if no scheme), or None
        when neither OLLAMA_HOST nor endpoint is set.
    """
    host = os.getenv("OLLAMA_HOST") or endpoint
    if host and "://" not in host:
        host = f"http://{host}"
    return host


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
    """  # Also raises LLMAuthError / LLMConnectionError via helpers.
    try:
        import google.genai as genai  # pylint: disable=import-error
    except ImportError as exc:
        raise ImportError(
            "google-genai is required to list Gemini models.\n"
            "Install with: pip install 'mcp-coder[langchain]'"
        ) from exc
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
    """  # Also raises LLMAuthError / LLMConnectionError via helpers.
    try:
        import openai  # pylint: disable=import-outside-toplevel
    except ImportError as exc:
        raise ImportError(
            "openai is required to list OpenAI models.\n"
            "Install with: pip install 'mcp-coder[langchain]'"
        ) from exc
    try:
        client = openai.OpenAI(
            api_key=api_key if api_key else None,
            base_url=endpoint if endpoint else None,
            http_client=create_http_client(),
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
    """  # Also raises LLMAuthError / LLMConnectionError via helpers.
    try:
        import anthropic  # pylint: disable=import-outside-toplevel
    except ImportError as exc:
        raise ImportError(
            "anthropic is required to list Anthropic models.\n"
            "Install with: pip install 'mcp-coder[langchain]'"
        ) from exc
    try:
        client = anthropic.Anthropic(
            api_key=api_key if api_key else None,
            http_client=create_http_client(),
        )
        return sorted(m.id for m in client.models.list())
    except ANTHROPIC_AUTH_ERRORS as exc:
        raise_auth_error("Anthropic", "ANTHROPIC_API_KEY", exc)
    except CONNECTION_ERRORS as exc:
        raise_connection_error("Anthropic", "ANTHROPIC_API_KEY", exc)


def list_ollama_models(
    api_key: str | None,
    endpoint: str | None = None,
) -> list[str]:
    """Return sorted model names from the Ollama daemon's /api/tags.

    Args:
        api_key: Optional bearer token for proxy-auth setups (unused by the
            ``ollama`` Python client directly; reserved for symmetry).
        endpoint: Optional Ollama host (host:port or full URL); resolved via
            :func:`_resolve_ollama_host`.

    Returns:
        Sorted list of model name strings (e.g. ``["llama3:latest", "mistral:7b"]``).
        Empty list when the daemon returns no models.

    Raises:
        ImportError: If the ``ollama`` Python client is not installed.
    """  # Also raises LLMConnectionError via helpers.
    del api_key  # not consumed by the ollama Python client directly
    try:
        import ollama  # pylint: disable=import-outside-toplevel,import-error
    except ImportError as exc:
        raise ImportError(
            "ollama is required to list Ollama models.\n"
            "Install with: pip install 'mcp-coder[langchain]'"
        ) from exc
    host = _resolve_ollama_host(endpoint)
    try:
        client = ollama.Client(host=host) if host else ollama.Client()
        data: Any = client.list()
        if isinstance(data, dict):
            models_iter = data.get("models", [])
        else:
            models_iter = getattr(data, "models", [])
        names: list[str] = []
        for m in models_iter:
            if isinstance(m, dict):
                name = m.get("name") or m.get("model")
            else:
                name = getattr(m, "name", None) or getattr(m, "model", None)
            if isinstance(name, str):
                names.append(name)
        return sorted(names)
    except CONNECTION_ERRORS as exc:
        raise_connection_error(
            "Ollama",
            "OLLAMA_API_KEY",
            exc,
            endpoint_hint="endpoint/OLLAMA_HOST if not localhost",
        )
