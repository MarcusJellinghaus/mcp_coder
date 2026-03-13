"""Shared message conversion helpers for LangChain backends.

Both openai.py and gemini.py import from this module.
langchain_core.messages is imported here so backend modules never need
to import from langchain_core directly.
"""

import logging
from typing import Any

# pylint: disable=import-error
try:
    from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
except ImportError as exc:
    raise ImportError(
        "LangChain core is required for message conversion.\n"
        "Install with: pip install 'mcp-coder[langchain]'"
    ) from exc

logger = logging.getLogger(__name__)


def _to_lc_messages(messages: list[dict[str, Any]]) -> list[BaseMessage]:
    """Convert plain role/content dicts to LangChain message objects."""
    result: list[BaseMessage] = []
    for m in messages:
        role = m["role"]
        if role == "human":
            result.append(HumanMessage(content=m["content"]))
        elif role == "ai":
            result.append(AIMessage(content=m["content"]))
        else:
            logger.warning("Unexpected message role %r, treating as human", role)
            result.append(HumanMessage(content=m["content"]))
    return result


def _ai_message_to_dict(msg: AIMessage) -> dict[str, object]:
    """Convert AIMessage to a serialisable dict (no pydantic dependency)."""
    return {
        "content": msg.content,
        "response_metadata": getattr(msg, "response_metadata", {}),
        "usage_metadata": getattr(msg, "usage_metadata", None),
        "id": getattr(msg, "id", None),
    }
