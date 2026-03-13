"""LangChain Google Gemini backend.

Raises ImportError with installation instructions if langchain_google_genai
is not installed.
"""

import os
from typing import Any

from ._models import list_gemini_models  # noqa: E402

# pylint: disable=import-error
try:
    from langchain_google_genai import ChatGoogleGenerativeAI

    from ._utils import _ai_message_to_dict, _to_lc_messages
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


def ask_gemini(
    question: str,
    model: str,
    api_key: str | None,
    messages: list[dict[str, Any]],
    timeout: int = 30,
) -> tuple[str, dict[str, object]]:
    """Call ChatGoogleGenerativeAI. Returns (response_text, raw_response_dict).

    Raises ImportError with install instructions if langchain_google_genai missing.
    """
    lc_messages = _to_lc_messages(messages + [{"role": "human", "content": question}])
    client = create_gemini_model(model=model, api_key=api_key, timeout=timeout)

    try:
        ai_msg = client.invoke(lc_messages)
    except Exception as exc:  # pylint: disable=broad-except
        if "NOT_FOUND" in str(exc):
            hint = f"Model {model!r} not found for this Gemini API key."
            try:
                available = list_gemini_models(os.getenv("GEMINI_API_KEY") or api_key)
                hint += "\n\nAvailable models:\n" + "\n".join(
                    f"  - {m}" for m in available
                )
            except Exception:  # pylint: disable=broad-except
                pass
            raise ValueError(hint) from exc
        raise

    raw = _ai_message_to_dict(ai_msg)
    return (str(ai_msg.content), raw)
