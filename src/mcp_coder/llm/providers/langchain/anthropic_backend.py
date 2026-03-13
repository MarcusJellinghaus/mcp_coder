"""LangChain Anthropic backend.

Raises ImportError with installation instructions if langchain_anthropic
is not installed.
"""

from __future__ import annotations

import os
from typing import Any

# pylint: disable=import-error
try:
    from langchain_anthropic import ChatAnthropic
    from pydantic import SecretStr
except ImportError as exc:
    raise ImportError(
        "LangChain Anthropic backend requires extra dependencies.\n"
        "Install with: pip install 'mcp-coder[langchain]'"
    ) from exc


def create_anthropic_model(
    model: str,
    api_key: str | None,
    timeout: int = 30,
) -> ChatAnthropic:
    """Create an Anthropic chat model without invoking it."""
    effective_api_key = os.getenv("ANTHROPIC_API_KEY") or api_key
    kwargs: dict[str, Any] = {
        "model_name": model,
        "default_request_timeout": float(timeout),
    }
    if effective_api_key:
        kwargs["anthropic_api_key"] = SecretStr(effective_api_key)
    return ChatAnthropic(**kwargs)
