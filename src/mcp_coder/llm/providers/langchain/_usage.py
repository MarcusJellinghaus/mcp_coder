"""Usage extraction and summing helpers for the LangChain provider.

This module lives outside ``__init__.py`` to avoid circular-import risk between
``langchain/__init__.py`` and ``agent.py``.
"""

from __future__ import annotations

from typing import Any

from mcp_coder.llm.types import UsageInfo


def _extract_usage(ai_msg: Any) -> UsageInfo:
    """Extract a ``UsageInfo``-shaped dict from a LangChain AIMessage's ``usage_metadata``.

    Maps LangChain's ``usage_metadata`` structure (with nested ``input_token_details``)
    onto the provider-agnostic ``UsageInfo`` TypedDict fields.

    Args:
        ai_msg: A LangChain ``AIMessage``/``AIMessageChunk`` (or any object with
            an optional ``usage_metadata`` attribute).

    Returns:
        A ``UsageInfo`` dict containing only the fields that were present in
        the message's metadata. Returns ``{}`` if no usage data is available.
    """
    meta = getattr(ai_msg, "usage_metadata", None) or {}
    details = meta.get("input_token_details") or {}
    usage: UsageInfo = {}
    if "input_tokens" in meta:
        usage["input_tokens"] = meta["input_tokens"]
    if "output_tokens" in meta:
        usage["output_tokens"] = meta["output_tokens"]
    if "cache_read" in details:
        usage["cache_read_input_tokens"] = details["cache_read"]
    if "cache_creation" in details:
        usage["cache_creation_input_tokens"] = details["cache_creation"]
    return usage


def _sum_usage(a: UsageInfo, b: UsageInfo) -> UsageInfo:
    """Sum two ``UsageInfo`` dicts field-by-field.

    Always returns all 4 keys (zero-default). Symmetric contract — display layer
    gates on ``cache_read > 0``.

    Args:
        a: First usage dict.
        b: Second usage dict.

    Returns:
        A ``UsageInfo`` dict containing the per-field sum of both inputs.
    """
    return UsageInfo(
        input_tokens=a.get("input_tokens", 0) + b.get("input_tokens", 0),
        output_tokens=a.get("output_tokens", 0) + b.get("output_tokens", 0),
        cache_read_input_tokens=(
            a.get("cache_read_input_tokens", 0) + b.get("cache_read_input_tokens", 0)
        ),
        cache_creation_input_tokens=(
            a.get("cache_creation_input_tokens", 0)
            + b.get("cache_creation_input_tokens", 0)
        ),
    )
