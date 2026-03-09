"""Utilities for listing available LLM models per LangChain backend."""

from __future__ import annotations

# pylint: disable=import-error
try:
    import google.genai as genai
except ImportError as exc:
    raise ImportError(
        "google-genai is required to list Gemini models.\n"
        "Install with: pip install 'mcp-coder[langchain]'"
    ) from exc


def list_gemini_models(api_key: str | None) -> list[str]:
    """Return model names supporting generateContent for the given Gemini API key.

    Returns short names without the 'models/' prefix, matching the format
    expected by ``[llm.langchain] model = "..."`` in config.toml.

    Raises ImportError if google-genai is not installed (part of mcp-coder[langchain]).
    """
    client = genai.Client(api_key=api_key)
    return [
        m.name.removeprefix("models/")
        for m in client.models.list()
        if m.name is not None and "generateContent" in (m.supported_actions or [])
    ]
