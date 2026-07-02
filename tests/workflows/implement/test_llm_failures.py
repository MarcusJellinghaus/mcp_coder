"""Tests for the shared LLM-exception → workflow-failure-reason helper."""

from mcp_coder.llm.interface import LLMTimeoutError
from mcp_coder.llm.providers.claude.claude_code_cli import McpServersUnavailableError
from mcp_coder.workflows.implement.constants import FailureCategory
from mcp_coder.workflows.implement.llm_failures import (
    REASON_TO_CATEGORY,
    llm_failure_reason,
)


class TestLlmFailureReason:
    """Tests for llm_failure_reason()."""

    def test_timeout_maps_to_timeout_reason(self) -> None:
        """LLMTimeoutError maps to the "timeout" reason."""
        assert llm_failure_reason(LLMTimeoutError("timed out")) == "timeout"

    def test_mcp_unavailable_maps_to_mcp_unavailable_reason(self) -> None:
        """McpServersUnavailableError maps to the "mcp_unavailable" reason."""
        assert (
            llm_failure_reason(McpServersUnavailableError("no mcp"))
            == "mcp_unavailable"
        )

    def test_unrelated_exception_maps_to_none(self) -> None:
        """An unrelated exception maps to None (not an LLM failure)."""
        assert llm_failure_reason(ValueError("boom")) is None


class TestReasonToCategory:
    """Tests for the REASON_TO_CATEGORY mapping."""

    def test_timeout_maps_to_llm_timeout_category(self) -> None:
        """ "timeout" maps to FailureCategory.LLM_TIMEOUT."""
        assert REASON_TO_CATEGORY["timeout"] == FailureCategory.LLM_TIMEOUT

    def test_mcp_unavailable_maps_to_mcp_unavailable_category(self) -> None:
        """ "mcp_unavailable" maps to FailureCategory.MCP_UNAVAILABLE."""
        assert REASON_TO_CATEGORY["mcp_unavailable"] == FailureCategory.MCP_UNAVAILABLE

    def test_every_reason_has_a_category(self) -> None:
        """Every reason llm_failure_reason can return has a category mapping."""
        assert set(REASON_TO_CATEGORY) == {"timeout", "mcp_unavailable"}
