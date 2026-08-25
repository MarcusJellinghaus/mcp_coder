"""LangChain OpenAI backend (standard OpenAI and Azure OpenAI).

Raises ImportError with installation instructions if langchain_openai
is not installed.
"""

from __future__ import annotations

import os

from ._http import close_http_clients, create_async_http_client, create_http_client

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
    base_url: str | None = None,
    api_version: str | None = None,
    timeout: int = 30,
) -> ChatOpenAI | AzureChatOpenAI:
    """Create an OpenAI/Azure chat model without invoking it.

    Returns:
        Configured ChatOpenAI or AzureChatOpenAI instance.
    """
    effective_api_key = os.getenv("OPENAI_API_KEY") or api_key
    secret_key = SecretStr(effective_api_key) if effective_api_key else None

    http_client = create_http_client()
    async_http_client = create_async_http_client()

    # Both clients exist before the constructor runs, so a constructor that
    # raises leaves nobody holding them. On success the returned model owns
    # them and they must stay open.
    chat_model: ChatOpenAI | AzureChatOpenAI | None = None
    try:
        if api_version:
            chat_model = AzureChatOpenAI(
                azure_deployment=model,
                azure_endpoint=base_url,
                api_key=secret_key,
                api_version=api_version,
                timeout=timeout,
                http_client=http_client,
                http_async_client=async_http_client,
            )
        else:
            chat_model = ChatOpenAI(
                model=model,
                api_key=secret_key,
                base_url=base_url,
                timeout=timeout,
                http_client=http_client,
                http_async_client=async_http_client,
            )
        return chat_model
    finally:
        if chat_model is None:
            close_http_clients(http_client, async_http_client)
