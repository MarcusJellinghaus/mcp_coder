"""LangChain Ollama backend.

Raises ImportError with installation instructions if langchain_ollama
is not installed.
"""

from __future__ import annotations

import os
from typing import Any

from ._models import _resolve_ollama_host

# pylint: disable=import-error
try:
    from langchain_ollama import ChatOllama
except ImportError as exc:
    raise ImportError(
        "LangChain Ollama backend requires extra dependencies.\n"
        "Install with: pip install 'mcp-coder[langchain]'"
    ) from exc


def create_ollama_model(
    model: str,
    api_key: str | None,
    endpoint: str | None = None,
    timeout: int = 30,
) -> ChatOllama:
    """Create a ChatOllama chat model without invoking it.

    Returns:
        Configured ChatOllama instance.
    """
    effective_api_key = os.getenv("OLLAMA_API_KEY") or api_key
    kwargs: dict[str, Any] = {
        "model": model,
        "timeout": float(timeout),
    }
    base_url = _resolve_ollama_host(endpoint)
    if base_url:
        kwargs["base_url"] = base_url
    if effective_api_key:
        kwargs["client_kwargs"] = {
            "headers": {"Authorization": f"Bearer {effective_api_key}"}
        }
    return ChatOllama(**kwargs)
