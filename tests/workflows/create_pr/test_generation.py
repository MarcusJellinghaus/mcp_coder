"""Tests for create_PR workflow PR generation functionality."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from workflows.create_PR import generate_pr_summary


class TestGeneratePrSummary:
    """Test generate_pr_summary function."""

    @patch("workflows.create_PR.get_branch_diff")
    @patch("workflows.create_PR.get_prompt")
    @patch("workflows.create_PR.ask_llm")
    def test_generate_pr_summary_success(
        self,
        mock_ask_llm: MagicMock,
        mock_get_prompt: MagicMock,
        mock_get_diff: MagicMock,
    ) -> None:
        """Test successful PR summary generation."""
        mock_get_diff.return_value = "diff content here"
        mock_get_prompt.return_value = "PR Summary prompt template"
        mock_ask_llm.return_value = "feat: Add authentication\n\nDetailed description"

        title, body = generate_pr_summary(Path("/test/project"))

        assert title == "feat: Add authentication"
        assert "Detailed description" in body
        mock_get_diff.assert_called_once_with(
            Path("/test/project"), exclude_paths=["pr_info/steps/"]
        )
        mock_get_prompt.assert_called_once()
        mock_ask_llm.assert_called_once()

    @patch("workflows.create_PR.get_branch_diff")
    @patch("workflows.create_PR.get_prompt")
    @patch("workflows.create_PR.ask_llm")
    def test_generate_pr_summary_structured_response(
        self,
        mock_ask_llm: MagicMock,
        mock_get_prompt: MagicMock,
        mock_get_diff: MagicMock,
    ) -> None:
        """Test PR summary generation with structured LLM response."""
        mock_get_diff.return_value = "diff content here"
        mock_get_prompt.return_value = "PR Summary prompt template"
        mock_ask_llm.return_value = """TITLE: feat: Add user management
BODY:
## Summary
Implements comprehensive user management functionality.

## Changes
- User registration and authentication
- Role-based access control
- User profile management"""

        title, body = generate_pr_summary(Path("/test/project"))

        assert title == "feat: Add user management"
        assert "## Summary" in body
        assert "User registration and authentication" in body
        assert "Role-based access control" in body

    @patch("workflows.create_PR.get_branch_diff")
    def test_generate_pr_summary_no_diff(self, mock_get_diff: MagicMock) -> None:
        """Test PR summary generation when no diff available."""
        mock_get_diff.return_value = ""

        title, body = generate_pr_summary(Path("/test/project"))

        assert title == "Pull Request"
        assert body == "Pull Request"

    @patch("workflows.create_PR.get_branch_diff")
    def test_generate_pr_summary_whitespace_diff(
        self, mock_get_diff: MagicMock
    ) -> None:
        """Test PR summary generation when diff is only whitespace."""
        mock_get_diff.return_value = "   \n\n   \t   \n   "

        title, body = generate_pr_summary(Path("/test/project"))

        assert title == "Pull Request"
        assert body == "Pull Request"

    @patch("workflows.create_PR.get_branch_diff")
    @patch("workflows.create_PR.get_prompt")
    @patch("workflows.create_PR.ask_llm")
    def test_generate_pr_summary_llm_failure(
        self,
        mock_ask_llm: MagicMock,
        mock_get_prompt: MagicMock,
        mock_get_diff: MagicMock,
    ) -> None:
        """Test PR summary generation when LLM call fails."""
        mock_get_diff.return_value = "diff content"
        mock_get_prompt.return_value = "prompt template"
        mock_ask_llm.return_value = None  # LLM failure

        # Should exit with code 1 on LLM failure
        with pytest.raises(SystemExit) as exc_info:
            generate_pr_summary(Path("/test/project"))

        assert exc_info.value.code == 1

    @patch("workflows.create_PR.get_branch_diff")
    @patch("workflows.create_PR.get_prompt")
    @patch("workflows.create_PR.ask_llm")
    def test_generate_pr_summary_llm_exception(
        self,
        mock_ask_llm: MagicMock,
        mock_get_prompt: MagicMock,
        mock_get_diff: MagicMock,
    ) -> None:
        """Test PR summary generation when LLM call raises exception."""
        mock_get_diff.return_value = "diff content"
        mock_get_prompt.return_value = "prompt template"
        mock_ask_llm.side_effect = Exception("LLM API error")

        # Should exit with code 1 on LLM exception
        with pytest.raises(SystemExit) as exc_info:
            generate_pr_summary(Path("/test/project"))

        assert exc_info.value.code == 1

    @patch("workflows.create_PR.get_branch_diff")
    @patch("workflows.create_PR.get_prompt")
    @patch("workflows.create_PR.ask_llm")
    def test_generate_pr_summary_empty_llm_response(
        self,
        mock_ask_llm: MagicMock,
        mock_get_prompt: MagicMock,
        mock_get_diff: MagicMock,
    ) -> None:
        """Test PR summary generation when LLM returns empty response."""
        mock_get_diff.return_value = "diff content"
        mock_get_prompt.return_value = "prompt template"
        mock_ask_llm.return_value = ""  # Empty response

        # Should exit with code 1 on empty response
        with pytest.raises(SystemExit) as exc_info:
            generate_pr_summary(Path("/test/project"))

        assert exc_info.value.code == 1

    @patch("workflows.create_PR.get_branch_diff")
    @patch("workflows.create_PR.get_prompt")
    @patch("workflows.create_PR.ask_llm")
    def test_generate_pr_summary_whitespace_llm_response(
        self,
        mock_ask_llm: MagicMock,
        mock_get_prompt: MagicMock,
        mock_get_diff: MagicMock,
    ) -> None:
        """Test PR summary generation when LLM returns only whitespace."""
        mock_get_diff.return_value = "diff content"
        mock_get_prompt.return_value = "prompt template"
        mock_ask_llm.return_value = "   \n\n   \t   \n   "  # Whitespace only

        # Should exit with code 1 on whitespace-only response
        with pytest.raises(SystemExit) as exc_info:
            generate_pr_summary(Path("/test/project"))

        assert exc_info.value.code == 1

    @patch("workflows.create_PR.get_branch_diff")
    @patch("workflows.create_PR._load_prompt_or_exit")
    def test_generate_pr_summary_prompt_failure(
        self,
        mock_load_prompt: MagicMock,
        mock_get_diff: MagicMock,
    ) -> None:
        """Test PR summary generation when prompt loading fails."""
        mock_get_diff.return_value = "diff content"
        mock_load_prompt.side_effect = SystemExit(1)  # Prompt loading exits

        # Should exit with code 1 on prompt failure
        with pytest.raises(SystemExit) as exc_info:
            generate_pr_summary(Path("/test/project"))

        assert exc_info.value.code == 1

    @patch("workflows.create_PR.get_branch_diff")
    def test_generate_pr_summary_git_diff_exception(
        self, mock_get_diff: MagicMock
    ) -> None:
        """Test PR summary generation when git diff raises exception."""
        mock_get_diff.side_effect = Exception("Git error")

        # Should let the exception propagate (no special handling for git errors)
        with pytest.raises(Exception, match="Git error"):
            generate_pr_summary(Path("/test/project"))
