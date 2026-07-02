"""Shared 404 / model-not-found diagnostics for the LangChain provider.

These helpers de-duplicate the previously copy-pasted 404 handling across
``_ask_text`` and ``_ask_text_stream`` in the package ``__init__``: the
detection predicate (:func:`_is_404_error`) and the user-facing hint
(:func:`_format_404_hint`) each now live in one place.
"""

from __future__ import annotations

import os


def _get_model_suggestions(config: dict[str, str | None]) -> str:
    """Try to list available models for the configured backend.

    Args:
        config: LangChain configuration dict with backend and api_key.

    Returns:
        Formatted string of available models, or empty string if none found.
    """
    backend = config.get("backend")
    api_key = config.get("api_key")
    endpoint = config.get("endpoint")

    from ._models import (
        list_anthropic_models,
        list_gemini_models,
        list_ollama_models,
        list_openai_models,
    )

    models: list[str] = []
    if backend == "openai":
        models = list_openai_models(os.getenv("OPENAI_API_KEY") or api_key, endpoint)
    elif backend == "gemini":
        models = list_gemini_models(os.getenv("GEMINI_API_KEY") or api_key)
    elif backend == "anthropic":
        models = list_anthropic_models(os.getenv("ANTHROPIC_API_KEY") or api_key)
    elif backend == "ollama":
        models = list_ollama_models(os.getenv("OLLAMA_API_KEY") or api_key, endpoint)

    if models:
        return "\n\nAvailable models:\n" + "\n".join(f"  - {m}" for m in models)
    return ""


def _is_404_error(exc: Exception) -> bool:
    """Return True when an exception looks like a 404 / model-not-found.

    Single source of truth for the detection predicate, shared by _ask_text
    and _ask_text_stream (previously copy-pasted inline in both).

    Args:
        exc: The exception raised by the chat model call.

    Returns:
        True if the exception message looks like a 404 / model-not-found.
    """
    low = str(exc).lower()
    return "404" in low or "not_found" in low or "not found" in low


def _format_404_hint(config: dict[str, str | None]) -> str:
    """Build the user-facing hint for a 404 / model-not-found response.

    For the openai backend with a custom endpoint the likely cause is a wrong
    base URL, so return a base-URL hint and skip the model-listing round-trip.
    Otherwise (non-openai backends such as ollama, or Azure with api_version)
    fall back to 'model not found' plus best-effort suggestions.

    Args:
        config: LangChain configuration dict.

    Returns:
        The user-facing hint message for a 404 / model-not-found response.
    """
    model = config.get("model", "")
    if (
        config.get("backend") == "openai"
        and config.get("endpoint")
        and not config.get("api_version")
    ):
        return (
            f"Model {model!r} not found. If using a custom server, check your "
            "base URL (e.g. …/v1); mcp-coder appends /chat/completions."
        )
    hint = f"Model {model!r} not found."
    try:
        hint += _get_model_suggestions(config)
    except Exception:  # pylint: disable=broad-except
        pass
    return hint
