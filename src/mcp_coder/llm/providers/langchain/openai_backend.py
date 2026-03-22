"""LangChain OpenAI backend (standard OpenAI and Azure OpenAI).

Raises ImportError with installation instructions if langchain_openai
is not installed.
"""

from __future__ import annotations

import os

# pylint: disable=import-error
try:
    from langchain_openai import AzureChatOpenAI, ChatOpenAI
    from pydantic import SecretStr
except ImportError as exc:
    raise ImportError(
        "LangChain OpenAI backend requires extra dependencies.\n"
        "Install with: pip install 'mcp-coder[langchain]'"
    ) from exc


def create_openai_model(
    model: str,
    api_key: str | None,
    endpoint: str | None = None,
    api_version: str | None = None,
    timeout: int = 30,
) -> ChatOpenAI | AzureChatOpenAI:
    """Create an OpenAI/Azure chat model without invoking it.

    Returns:
        Configured ChatOpenAI or AzureChatOpenAI instance.
    """
    effective_api_key = os.getenv("OPENAI_API_KEY") or api_key
    secret_key = SecretStr(effective_api_key) if effective_api_key else None

    if api_version:
        return AzureChatOpenAI(
            azure_deployment=model,
            azure_endpoint=endpoint,
            api_key=secret_key,
            api_version=api_version,
            timeout=timeout,
        )
    return ChatOpenAI(
        model=model,
        api_key=secret_key,
        base_url=endpoint,
        timeout=timeout,
    )
