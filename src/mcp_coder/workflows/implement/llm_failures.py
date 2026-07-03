"""Shared mapping from LLM exceptions to workflow failure reasons/categories.

The autonomous implement/mypy-fix/CI-analysis sites all need to translate the
two LLM exceptions the Claude provider raises — ``LLMTimeoutError`` (inactivity
timeout) and ``McpServersUnavailableError`` (a configured MCP server did not
connect) — into a stable workflow *reason* string and, from there, a
``FailureCategory``/label. Centralising that here keeps the branch logic in one
place so the four sites stay consistent.

Kept import-light on purpose: workflows already depend on ``llm``, so importing
the exception types introduces no new dependency edge or cycle.
"""

from __future__ import annotations

from mcp_coder.llm.interface import LLMTimeoutError
from mcp_coder.llm.providers.claude.claude_code_cli import McpServersUnavailableError

from .constants import FailureCategory

# Reason strings map 1:1 to FailureCategory members (and thus to labels.json IDs).
REASON_TO_CATEGORY: dict[str, FailureCategory] = {
    "timeout": FailureCategory.LLM_TIMEOUT,
    "mcp_unavailable": FailureCategory.MCP_UNAVAILABLE,
}


def llm_failure_reason(exc: BaseException) -> str | None:
    """Map an LLM exception to a workflow failure reason, else None.

    Args:
        exc: The exception raised by an LLM call.

    Returns:
        ``"timeout"`` for :class:`LLMTimeoutError`, ``"mcp_unavailable"`` for
        :class:`McpServersUnavailableError`, or ``None`` for any other
        exception (i.e. not a categorizable LLM failure).
    """
    if isinstance(exc, LLMTimeoutError):
        return "timeout"
    if isinstance(exc, McpServersUnavailableError):
        return "mcp_unavailable"
    return None
