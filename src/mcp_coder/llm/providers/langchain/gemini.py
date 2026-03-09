"""LangChain Google Gemini backend.

Raises ImportError with installation instructions if langchain_google_genai
is not installed.
"""

import os

# pylint: disable=import-error
try:
    from langchain_google_genai import ChatGoogleGenerativeAI

    from ._utils import _ai_message_to_dict, _to_lc_messages
except ImportError as exc:
    raise ImportError(
        "LangChain Gemini backend requires extra dependencies.\n"
        "Install with: pip install 'mcp-coder[langchain]'"
    ) from exc


def ask_gemini(
    question: str,
    model: str,
    api_key: str | None,
    messages: list[dict[str, str]],
    timeout: int = 30,
) -> tuple[str, dict[str, object]]:
    """Call ChatGoogleGenerativeAI. Returns (response_text, raw_response_dict).

    Raises ImportError with install instructions if langchain_google_genai missing.
    """
    effective_api_key = os.getenv("GEMINI_API_KEY") or api_key
    lc_messages = _to_lc_messages(messages + [{"role": "human", "content": question}])

    client = ChatGoogleGenerativeAI(
        model=model,
        google_api_key=effective_api_key,
        timeout=timeout,
    )

    ai_msg = client.invoke(lc_messages)
    raw = _ai_message_to_dict(ai_msg)
    return (str(ai_msg.content), raw)
