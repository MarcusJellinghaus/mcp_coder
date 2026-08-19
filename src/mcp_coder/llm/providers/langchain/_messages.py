"""Shared message assembly/serialization helpers for the LangChain provider.

This module is deliberately *neutral*: it imports nothing from its own package.
``langchain/__init__.py`` lazy-imports ``.agent`` to break an import cycle, so
helpers used by both modules cannot live in ``__init__.py`` — they live here
instead, where neither side can reintroduce the cycle.

All ``langchain_core`` imports are deferred inside the functions (matching the
style in ``__init__.py`` / ``agent.py``) so importing the package still works
when langchain is not installed.
"""

from __future__ import annotations

from itertools import dropwhile
from typing import Any, cast


def assemble_messages(
    system_messages: list[Any] | None,
    history: list[dict[str, Any]],
    question: str,
) -> list[Any]:
    """Assemble the outgoing message list: systems, then history, then question.

    Every ``"system"`` entry is dropped from ``history`` — not just leading ones.
    Loaded history may have been written by older code that persisted the
    prepended system messages; leaving them in would place non-leading system
    messages into the outgoing list, which single-system providers reject and
    which :func:`serialize_messages` would not strip on the way back out.

    Args:
        system_messages: Fresh system messages to place first, or ``None``.
        history: Prior conversation as stored dicts, each ``{"type", "data"}``.
        question: The new user question, appended as a ``HumanMessage``.

    Returns:
        A list of LangChain ``BaseMessage`` objects: the system messages, the
        rehydrated (system-free) history, then the new ``HumanMessage``.
    """
    from langchain_core.messages import HumanMessage, messages_from_dict

    result: list[Any] = list(system_messages or [])
    prior = [entry for entry in history if entry.get("type") != "system"]
    result.extend(messages_from_dict(prior))
    result.append(HumanMessage(content=question))
    return result


def serialize_messages(messages: list[Any]) -> list[dict[str, Any]]:
    """Serialize messages for storage, dropping leading system messages.

    Only *leading* system messages are stripped: this helper is handed lists
    that this code just assembled, where the prepended systems are always at the
    front. It is otherwise shape-agnostic — it dumps whatever list it is given.

    Args:
        messages: LangChain ``BaseMessage`` objects (anything exposing
            ``model_dump()`` or, for older message classes, ``dict()``).

    Returns:
        A list of ``{"type": str, "data": dict}`` entries, the shape
        ``messages_from_dict()`` and ``store_langchain_history()`` expect.
    """
    from langchain_core.messages import SystemMessage

    serialized: list[dict[str, Any]] = []
    for msg in dropwhile(lambda m: isinstance(m, SystemMessage), messages):
        if hasattr(msg, "model_dump"):
            dump = cast(dict[str, Any], msg.model_dump())
        else:
            dump = cast(dict[str, Any], msg.dict())
        msg_type = dump.pop("type", "unknown")
        serialized.append({"type": msg_type, "data": dump})
    return serialized
