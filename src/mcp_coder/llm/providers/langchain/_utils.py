"""Shared message conversion helpers for the LangChain provider.

Imported by __init__.py for text-mode message conversion.
"""

from __future__ import annotations

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
