from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.workflows.implement.task_processing import check_and_fix_mypy
from tests.workflows.implement.test_task_processing import _make_llm_response


class TestCheckAndFixMypy:
    """Test check_and_fix_mypy function."""

    @patch("mcp_coder.workflows.implement.task_processing._run_mypy_check")
    def test_check_and_fix_mypy_no_errors(self, mock_mypy_check: MagicMock) -> None:
        """Test mypy check when no errors found."""
        mock_mypy_check.return_value = None  # No errors

        result = check_and_fix_mypy(Path("/test/project"), 1, "claude")

        assert result is True
        mock_mypy_check.assert_called_once_with(Path("/test/project"))

    @patch("mcp_coder.workflows.implement.task_processing.store_session")
    @patch("mcp_coder.workflows.implement.task_processing.prompt_llm")
    @patch("mcp_coder.workflows.implement.task_processing.get_prompt")
    @patch("mcp_coder.workflows.implement.task_processing._run_mypy_check")
    def test_check_and_fix_mypy_fixes_errors(
        self,
        mock_mypy_check: MagicMock,
        mock_get_prompt: MagicMock,
        mock_prompt_llm: MagicMock,
        mock_store_session: MagicMock,
    ) -> None:
        """Test mypy check fixes errors successfully."""
        # First call returns errors, second call returns None (fixed)
        mock_mypy_check.side_effect = ["mypy error output", None]
        mock_get_prompt.return_value = "Fix mypy errors: [mypy_output]"
        mock_prompt_llm.return_value = _make_llm_response("Fixed the errors")

        result = check_and_fix_mypy(Path("/test/project"), 1, "claude")

        assert result is True
        assert mock_mypy_check.call_count == 2
        mock_get_prompt.assert_called_once()
        mock_prompt_llm.assert_called_once()
        # Verify store_session called with correct step_name
        mock_store_session.assert_called_once()
        call_kwargs = mock_store_session.call_args
        assert call_kwargs.kwargs.get("step_name") == "step_1_mypy_1" or (
            len(call_kwargs.args) >= 4 and call_kwargs.args[3] == "step_1_mypy_1"
        )
        assert "implement_sessions" in (
            call_kwargs.kwargs.get("store_path", "")
            or (call_kwargs.args[2] if len(call_kwargs.args) >= 3 else "")
        )

    @patch("mcp_coder.workflows.implement.task_processing.store_session")
    @patch("mcp_coder.workflows.implement.task_processing.prompt_llm")
    @patch("mcp_coder.workflows.implement.task_processing.get_prompt")
    @patch("mcp_coder.workflows.implement.task_processing._run_mypy_check")
    def test_check_and_fix_mypy_max_attempts(
        self,
        mock_mypy_check: MagicMock,
        mock_get_prompt: MagicMock,
        mock_prompt_llm: MagicMock,
        mock_store_session: MagicMock,
    ) -> None:
        """Test mypy check stops after max identical attempts."""
        # Always return same error (identical outputs)
        mock_mypy_check.return_value = "same mypy error"
        mock_get_prompt.return_value = "Fix mypy errors: [mypy_output]"
        mock_prompt_llm.return_value = _make_llm_response("Attempted fix")

        result = check_and_fix_mypy(Path("/test/project"), 1, "claude")

        assert result is False
        # Should attempt fixes until max identical attempts reached
        assert mock_prompt_llm.call_count == 3  # max_identical_attempts
        # store_session should be called once per attempt
        assert mock_store_session.call_count == 3

    @patch("mcp_coder.workflows.implement.task_processing._run_mypy_check")
    def test_check_and_fix_mypy_exception(self, mock_mypy_check: MagicMock) -> None:
        """Test mypy check handles exceptions."""
        mock_mypy_check.side_effect = Exception("Mypy error")

        result = check_and_fix_mypy(Path("/test/project"), 1, "claude")

        assert result is False

    @patch("mcp_coder.workflows.implement.task_processing.prompt_llm")
    @patch("mcp_coder.workflows.implement.task_processing.get_prompt")
    @patch("mcp_coder.workflows.implement.task_processing._run_mypy_check")
    def test_check_and_fix_mypy_timeout_propagates(
        self,
        mock_mypy_check: MagicMock,
        mock_get_prompt: MagicMock,
        mock_prompt_llm: MagicMock,
    ) -> None:
        """Fixes the pre-existing hole: a fix-up LLMTimeoutError must propagate.

        Previously the broad handler swallowed it into a False result, hiding the
        timeout from the caller. It must now reach the caller for categorization.
        """
        from mcp_coder.llm.interface import LLMTimeoutError

        mock_mypy_check.return_value = "mypy error output"
        mock_get_prompt.return_value = "Fix mypy errors: [mypy_output]"
        mock_prompt_llm.side_effect = LLMTimeoutError("timed out")

        with pytest.raises(LLMTimeoutError):
            check_and_fix_mypy(Path("/test/project"), 1, "claude")

    @patch("mcp_coder.workflows.implement.task_processing.prompt_llm")
    @patch("mcp_coder.workflows.implement.task_processing.get_prompt")
    @patch("mcp_coder.workflows.implement.task_processing._run_mypy_check")
    def test_check_and_fix_mypy_mcp_unavailable_propagates(
        self,
        mock_mypy_check: MagicMock,
        mock_get_prompt: MagicMock,
        mock_prompt_llm: MagicMock,
    ) -> None:
        """A fix-up McpServersUnavailableError must propagate, not become False."""
        from mcp_coder.llm.providers.claude.claude_code_cli import (
            McpServersUnavailableError,
        )

        mock_mypy_check.return_value = "mypy error output"
        mock_get_prompt.return_value = "Fix mypy errors: [mypy_output]"
        mock_prompt_llm.side_effect = McpServersUnavailableError(
            "MCP servers unavailable",
            {"mcp-tools-py": "failed"},
        )

        with pytest.raises(McpServersUnavailableError):
            check_and_fix_mypy(Path("/test/project"), 1, "claude")
