"""LangChain Anthropic backend.

Raises ImportError with installation instructions if langchain_anthropic
is not installed.
"""

from __future__ import annotations

import os

from ._models import list_anthropic_models  # noqa: E402

# pylint: disable=import-error
try:
    from langchain_anthropic import ChatAnthropic
    from pydantic import SecretStr

    from ._utils import _ai_message_to_dict, _to_lc_messages
except ImportError as exc:
    raise ImportError(
        "LangChain Anthropic backend requires extra dependencies.\n"
        "Install with: pip install 'mcp-coder[langchain]'"
    ) from exc


def ask_anthropic(
    question: str,
    model: str,
    api_key: str | None,
    messages: list[dict[str, str]],
    timeout: int = 30,
) -> tuple[str, dict[str, object]]:
    """Call ChatAnthropic. Returns (response_text, raw_response_dict).

    Raises ImportError with install instructions if langchain_anthropic missing.
    """
    effective_api_key = os.getenv("ANTHROPIC_API_KEY") or api_key
    lc_messages = _to_lc_messages(messages + [{"role": "human", "content": question}])
    kwargs: dict[str, object] = {
        "model_name": model,
        "default_request_timeout": float(timeout),
    }
    if effective_api_key:
        kwargs["anthropic_api_key"] = SecretStr(effective_api_key)

    client = ChatAnthropic(**kwargs)  # type: ignore[arg-type]

    try:
        ai_msg = client.invoke(lc_messages)
    except Exception as exc:  # pylint: disable=broad-except
        exc_str = str(exc)
        if "404" in exc_str or "not_found" in exc_str.lower():
            hint = f"Model {model!r} not found for this Anthropic API key."
            try:
                available = list_anthropic_models(effective_api_key)
                hint += "\n\nAvailable models:\n" + "\n".join(
                    f"  - {m}" for m in available
                )
            except Exception:  # pylint: disable=broad-except
                pass
            raise ValueError(hint) from exc
        raise

    raw = _ai_message_to_dict(ai_msg)
    return (str(ai_msg.content), raw)
