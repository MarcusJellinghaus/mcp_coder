"""LangChain Google Gemini backend.

Raises ImportError with installation instructions if langchain_google_genai
is not installed.
"""

from __future__ import annotations

import os
from typing import Any

# pylint: disable=import-error
try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    from pydantic import SecretStr
except ImportError as exc:
    raise ImportError(
        "LangChain Gemini backend requires extra dependencies.\n"
        "Install with: pip install 'mcp-coder[langchain]'"
    ) from exc


def create_gemini_model(
    model: str,
    api_key: str | None,
    timeout: int = 30,
) -> ChatGoogleGenerativeAI:
    """Create a Gemini chat model without invoking it.

    Returns:
        Configured ChatGoogleGenerativeAI instance.
    """
    effective_api_key = os.getenv("GEMINI_API_KEY") or api_key
    kwargs: dict[str, Any] = {
        "model": model,
        "timeout": timeout,
    }
    if effective_api_key:
        kwargs["google_api_key"] = SecretStr(effective_api_key)
    return ChatGoogleGenerativeAI(**kwargs)
