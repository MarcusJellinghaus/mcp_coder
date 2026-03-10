"""LangChain OpenAI backend (standard OpenAI and Azure OpenAI).

Raises ImportError with installation instructions if langchain_openai
is not installed.
"""

from __future__ import annotations

import os

from ._models import list_openai_models  # noqa: E402

# pylint: disable=import-error
try:
    from langchain_openai import AzureChatOpenAI, ChatOpenAI
    from pydantic import SecretStr

    from ._utils import _ai_message_to_dict, _to_lc_messages
except ImportError as exc:
    raise ImportError(
        "LangChain OpenAI backend requires extra dependencies.\n"
        "Install with: pip install 'mcp-coder[langchain]'"
    ) from exc


def ask_openai(
    question: str,
    model: str,
    api_key: str | None,
    endpoint: str | None,
    api_version: str | None,
    messages: list[dict[str, str]],
    timeout: int = 30,
) -> tuple[str, dict[str, object]]:
    """Call ChatOpenAI, or AzureChatOpenAI when api_version is set.

    Returns (response_text, raw_response_dict).
    Raises ImportError with install instructions if langchain_openai missing.
    """
    effective_api_key = os.getenv("OPENAI_API_KEY") or api_key
    lc_messages = _to_lc_messages(messages + [{"role": "human", "content": question}])
    secret_key = SecretStr(effective_api_key) if effective_api_key else None

    client: AzureChatOpenAI | ChatOpenAI
    if api_version:
        client = AzureChatOpenAI(
            azure_deployment=model,
            azure_endpoint=endpoint,
            api_key=secret_key,
            api_version=api_version,
            timeout=timeout,
        )
    else:
        client = ChatOpenAI(
            model=model,
            api_key=secret_key,
            base_url=endpoint,
            timeout=timeout,
        )

    try:
        ai_msg = client.invoke(lc_messages)
    except Exception as exc:  # pylint: disable=broad-except
        exc_str = str(exc)
        if "404" in exc_str or "not_found" in exc_str.lower():
            hint = f"Model {model!r} not found for this OpenAI API key."
            try:
                available = list_openai_models(effective_api_key, endpoint)
                hint += "\n\nAvailable models:\n" + "\n".join(
                    f"  - {m}" for m in available
                )
            except Exception:  # pylint: disable=broad-except
                pass
            raise ValueError(hint) from exc
        raise

    raw = _ai_message_to_dict(ai_msg)
    return (str(ai_msg.content), raw)
