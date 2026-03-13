"""LangChain Google Gemini backend.

Raises ImportError with installation instructions if langchain_google_genai
is not installed.
"""

import os

# pylint: disable=import-error
try:
    from langchain_google_genai import ChatGoogleGenerativeAI
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
    """Create a Gemini chat model without invoking it."""
    effective_api_key = os.getenv("GEMINI_API_KEY") or api_key
    return ChatGoogleGenerativeAI(
        model=model,
        google_api_key=effective_api_key,
        timeout=timeout,
    )
