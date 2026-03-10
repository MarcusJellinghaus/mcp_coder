"""Utilities for listing available LLM models per LangChain backend."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from types import ModuleType

# Lazy-load SDK modules; set to None when the SDK is not installed.
# Each list_*_models() function checks its module and raises ImportError
# with install instructions when the SDK is missing.

_genai: ModuleType | None
try:
    import google.genai as _genai  # pylint: disable=import-error
except ImportError:
    _genai = None

_openai_mod: ModuleType | None
try:
    import openai as _openai_mod
except ImportError:
    _openai_mod = None

_anthropic_mod: ModuleType | None
try:
    import anthropic as _anthropic_mod
except ImportError:
    _anthropic_mod = None


def list_gemini_models(api_key: str | None) -> list[str]:
    """Return model names supporting generateContent for the given Gemini API key.

    Returns short names without the 'models/' prefix, matching the format
    expected by ``[llm.langchain] model = "..."`` in config.toml.

    Raises ImportError if google-genai is not installed (part of mcp-coder[langchain]).
    """
    if _genai is None:
        raise ImportError(
            "google-genai is required to list Gemini models.\n"
            "Install with: pip install 'mcp-coder[langchain]'"
        )
    client = _genai.Client(api_key=api_key)
    return [
        m.name.removeprefix("models/")
        for m in client.models.list()
        if m.name is not None and "generateContent" in (m.supported_actions or [])
    ]


def list_openai_models(api_key: str | None, endpoint: str | None = None) -> list[str]:
    """Return model IDs available for the given OpenAI API key.

    Raises ImportError if openai is not installed (part of mcp-coder[langchain]).
    """
    if _openai_mod is None:
        raise ImportError(
            "openai is required to list OpenAI models.\n"
            "Install with: pip install 'mcp-coder[langchain]'"
        )
    kwargs: dict[str, str | None] = {}
    if api_key:
        kwargs["api_key"] = api_key
    if endpoint:
        kwargs["base_url"] = endpoint

    client = _openai_mod.OpenAI(**kwargs)
    return sorted(m.id for m in client.models.list())


def list_anthropic_models(api_key: str | None) -> list[str]:
    """Return model IDs available for the given Anthropic API key.

    Raises ImportError if anthropic is not installed (part of mcp-coder[langchain]).
    """
    if _anthropic_mod is None:
        raise ImportError(
            "anthropic is required to list Anthropic models.\n"
            "Install with: pip install 'mcp-coder[langchain]'"
        )
    kwargs: dict[str, str | None] = {}
    if api_key:
        kwargs["api_key"] = api_key

    client = _anthropic_mod.Anthropic(**kwargs)
    return sorted(m.id for m in client.models.list())
