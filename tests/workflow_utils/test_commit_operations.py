"""Tests for commit operations utilities."""

import logging
from pathlib import Path
from typing import Any
from unittest.mock import Mock, patch

import pytest

from mcp_coder.llm.providers.claude.claude_code_api import ClaudeAPIError
from mcp_coder.workflow_utils.commit_operations import (
    generate_commit_message_with_llm,
    parse_llm_commit_response,
    strip_claude_footers,
)


class TestGenerateCommitMessageWithLLM:
    """Tests for generate_commit_message_with_llm function."""

    @patch("mcp_coder.workflow_utils.commit_operations.prepare_llm_environment")
    @patch("mcp_coder.workflow_utils.commit_operations.stage_all_changes")
    @patch("mcp_coder.workflow_utils.commit_operations.get_git_diff_for_commit")
    @patch("mcp_coder.prompt_manager.get_prompt")
    @patch("mcp_coder.workflow_utils.commit_operations.ask_llm")
    def test_generate_commit_message_success(
        self,
        mock_ask_llm: Mock,
        mock_get_prompt: Mock,
        mock_get_diff: Mock,
        mock_stage: Mock,
        mock_prepare_env: Mock,
    ) -> None:
        """Test successful LLM commit message generation."""
        # Setup mocks
        mock_prepare_env.return_value = {"MCP_CODER_PROJECT_DIR": "/test/repo"}
        mock_stage.return_value = True
        mock_get_diff.return_value = "diff --git a/file.py b/file.py\n+new line"
        mock_get_prompt.return_value = "Generate commit message"
        mock_ask_llm.return_value = "feat: add new feature\n\n🤖 Generated with [Claude Code](https://claude.com/claude-code)\n\nCo-Authored-By: Claude <noreply@anthropic.com>"

        project_dir = Path("/test/repo")

        success, message, error = generate_commit_message_with_llm(
            project_dir, "claude", "api"
        )

        assert success is True
        assert message == "feat: add new feature"
        assert error is None

        # Verify calls
        mock_prepare_env.assert_called_once_with(project_dir)
        mock_stage.assert_called_once_with(project_dir)
        mock_get_diff.assert_called_once_with(project_dir)
        mock_ask_llm.assert_called_once()
        # Verify env_vars was passed to ask_llm
        call_kwargs = mock_ask_llm.call_args[1]
        assert call_kwargs["env_vars"] == {"MCP_CODER_PROJECT_DIR": "/test/repo"}

    @patch("mcp_coder.workflow_utils.commit_operations.prepare_llm_environment")
    @patch("mcp_coder.workflow_utils.commit_operations.stage_all_changes")
    @patch("mcp_coder.workflow_utils.commit_operations.get_git_diff_for_commit")
    @patch("mcp_coder.prompt_manager.get_prompt")
    @patch("mcp_coder.workflow_utils.commit_operations.ask_llm")
    def test_generate_commit_message_with_custom_provider_method(
        self,
        mock_ask_llm: Mock,
        mock_get_prompt: Mock,
        mock_get_diff: Mock,
        mock_stage: Mock,
        mock_prepare_env: Mock,
    ) -> None:
        """Test LLM commit message generation with custom provider and method."""
        # Setup mocks
        mock_prepare_env.return_value = {"MCP_CODER_PROJECT_DIR": "/test/repo"}
        mock_stage.return_value = True
        mock_get_diff.return_value = "diff --git a/file.py b/file.py\n+new line"
        mock_get_prompt.return_value = "Generate commit message"
        mock_ask_llm.return_value = "feat: add new feature\n\n🤖 Generated with [Claude Code](https://claude.com/claude-code)\n\nCo-Authored-By: Claude <noreply@anthropic.com>"

        project_dir = Path("/test/repo")

        success, message, error = generate_commit_message_with_llm(
            project_dir, provider="claude", method="cli"
        )

        assert success is True
        assert message == "feat: add new feature"
        assert error is None

        # Verify ask_llm was called with correct provider and method
        mock_ask_llm.assert_called_once()
        call_args = mock_ask_llm.call_args
        assert call_args[1]["provider"] == "claude"
        assert call_args[1]["method"] == "cli"

    @patch("mcp_coder.workflow_utils.commit_operations.prepare_llm_environment")
    @patch("mcp_coder.workflow_utils.commit_operations.stage_all_changes")
    def test_generate_commit_message_stage_failure(
        self, mock_stage: Mock, mock_prepare_env: Mock
    ) -> None:
        """Test LLM generation with staging failure."""
        mock_prepare_env.return_value = {"MCP_CODER_PROJECT_DIR": "/test/repo"}
        mock_stage.return_value = False

        project_dir = Path("/test/repo")

        success, message, error = generate_commit_message_with_llm(
            project_dir, "claude", "api"
        )

        assert success is False
        assert message == ""
        error_str: str = error or ""
        assert "Failed to stage changes in repository" in error_str
        assert "write permissions" in error_str

    @patch("mcp_coder.workflow_utils.commit_operations.prepare_llm_environment")
    @patch("mcp_coder.workflow_utils.commit_operations.stage_all_changes")
    def test_generate_commit_message_stage_exception(
        self, mock_stage: Mock, mock_prepare_env: Mock
    ) -> None:
        """Test staging operation exception handling."""
        mock_prepare_env.return_value = {"MCP_CODER_PROJECT_DIR": "/test/repo"}
        mock_stage.side_effect = Exception("Permission denied")

        project_dir = Path("/test/repo")
        success, message, error = generate_commit_message_with_llm(
            project_dir, "claude", "api"
        )

        assert success is False
        assert message == ""
        error_str: str = error or ""
        assert "Error staging changes" in error_str
        assert "Permission denied" in error_str
        assert "git repository is accessible" in error_str

    @patch("mcp_coder.workflow_utils.commit_operations.prepare_llm_environment")
    @patch("mcp_coder.workflow_utils.commit_operations.stage_all_changes")
    @patch("mcp_coder.workflow_utils.commit_operations.get_git_diff_for_commit")
    def test_generate_commit_message_no_changes(
        self, mock_get_diff: Mock, mock_stage: Mock, mock_prepare_env: Mock
    ) -> None:
        """Test LLM generation with no changes."""
        mock_prepare_env.return_value = {"MCP_CODER_PROJECT_DIR": "/test/repo"}
        mock_stage.return_value = True
        mock_get_diff.return_value = ""

        project_dir = Path("/test/repo")

        success, message, error = generate_commit_message_with_llm(
            project_dir, "claude", "api"
        )

        assert success is False
        assert message == ""
        error_str: str = error or ""
        assert "No changes to commit" in error_str
        assert "modified, added, or deleted files" in error_str

    @patch("mcp_coder.workflow_utils.commit_operations.prepare_llm_environment")
    @patch("mcp_coder.workflow_utils.commit_operations.stage_all_changes")
    @patch("mcp_coder.workflow_utils.commit_operations.get_git_diff_for_commit")
    def test_generate_commit_message_git_diff_none(
        self, mock_get_diff: Mock, mock_stage: Mock, mock_prepare_env: Mock
    ) -> None:
        """Test git diff returning None."""
        mock_prepare_env.return_value = {"MCP_CODER_PROJECT_DIR": "/test/repo"}
        mock_stage.return_value = True
        mock_get_diff.return_value = None

        project_dir = Path("/test/repo")
        success, message, error = generate_commit_message_with_llm(
            project_dir, "claude", "api"
        )

        assert success is False
        assert message == ""
        error_str: str = error or ""
        assert "Failed to retrieve git diff" in error_str
        assert "invalid state" in error_str

    @patch("mcp_coder.workflow_utils.commit_operations.prepare_llm_environment")
    @patch("mcp_coder.workflow_utils.commit_operations.stage_all_changes")
    @patch("mcp_coder.workflow_utils.commit_operations.get_git_diff_for_commit")
    def test_generate_commit_message_git_diff_exception(
        self, mock_get_diff: Mock, mock_stage: Mock, mock_prepare_env: Mock
    ) -> None:
        """Test git diff operation exception handling."""
        mock_prepare_env.return_value = {"MCP_CODER_PROJECT_DIR": "/test/repo"}
        mock_stage.return_value = True
        mock_get_diff.side_effect = Exception("Git command failed")

        project_dir = Path("/test/repo")
        success, message, error = generate_commit_message_with_llm(
            project_dir, "claude", "api"
        )

        assert success is False
        assert message == ""
        error_str: str = error or ""
        assert "Error retrieving git diff" in error_str
        assert "Git command failed" in error_str

    @patch("mcp_coder.workflow_utils.commit_operations.prepare_llm_environment")
    @patch("mcp_coder.workflow_utils.commit_operations.stage_all_changes")
    @patch("mcp_coder.workflow_utils.commit_operations.get_git_diff_for_commit")
    @patch("mcp_coder.prompt_manager.get_prompt")
    def test_generate_commit_message_prompt_file_not_found(
        self,
        mock_get_prompt: Mock,
        mock_get_diff: Mock,
        mock_stage: Mock,
        mock_prepare_env: Mock,
    ) -> None:
        """Test prompt file not found error."""
        mock_prepare_env.return_value = {"MCP_CODER_PROJECT_DIR": "/test/repo"}
        mock_stage.return_value = True
        mock_get_diff.return_value = "some changes"
        mock_get_prompt.side_effect = FileNotFoundError("prompts.md not found")

        project_dir = Path("/test/repo")
        success, message, error = generate_commit_message_with_llm(
            project_dir, "claude", "api"
        )

        assert success is False
        assert message == ""
        error_str: str = error or ""
        assert "Commit prompt template not found" in error_str
        assert "prompts.md not found" in error_str

    @patch("mcp_coder.workflow_utils.commit_operations.prepare_llm_environment")
    @patch("mcp_coder.workflow_utils.commit_operations.stage_all_changes")
    @patch("mcp_coder.workflow_utils.commit_operations.get_git_diff_for_commit")
    @patch("mcp_coder.prompt_manager.get_prompt")
    def test_generate_commit_message_prompt_exception(
        self,
        mock_get_prompt: Mock,
        mock_get_diff: Mock,
        mock_stage: Mock,
        mock_prepare_env: Mock,
    ) -> None:
        """Test prompt loading exception handling."""
        mock_prepare_env.return_value = {"MCP_CODER_PROJECT_DIR": "/test/repo"}
        mock_stage.return_value = True
        mock_get_diff.return_value = "some changes"
        mock_get_prompt.side_effect = Exception("Permission denied")

        project_dir = Path("/test/repo")
        success, message, error = generate_commit_message_with_llm(
            project_dir, "claude", "api"
        )

        assert success is False
        assert message == ""
        error_str: str = error or ""
        assert "Failed to load commit prompt template" in error_str
        assert "Permission denied" in error_str

    @patch("mcp_coder.workflow_utils.commit_operations.prepare_llm_environment")
    @patch("mcp_coder.workflow_utils.commit_operations.stage_all_changes")
    @patch("mcp_coder.workflow_utils.commit_operations.get_git_diff_for_commit")
    @patch("mcp_coder.prompt_manager.get_prompt")
    @patch("mcp_coder.workflow_utils.commit_operations.ask_llm")
    def test_generate_commit_message_empty_llm_response(
        self,
        mock_ask_llm: Mock,
        mock_get_prompt: Mock,
        mock_get_diff: Mock,
        mock_stage: Mock,
        mock_prepare_env: Mock,
    ) -> None:
        """Test empty LLM response handling."""
        mock_prepare_env.return_value = {"MCP_CODER_PROJECT_DIR": "/test/repo"}
        mock_stage.return_value = True
        mock_get_diff.return_value = "some changes"
        mock_get_prompt.return_value = "prompt text"
        mock_ask_llm.return_value = ""

        project_dir = Path("/test/repo")
        success, message, error = generate_commit_message_with_llm(
            project_dir, "claude", "api"
        )

        assert success is False
        assert message == ""
        error_str: str = error or ""
        assert "LLM returned empty or null response" in error_str
        assert "AI service may be unavailable" in error_str

    @patch("mcp_coder.workflow_utils.commit_operations.prepare_llm_environment")
    @patch("mcp_coder.workflow_utils.commit_operations.stage_all_changes")
    @patch("mcp_coder.workflow_utils.commit_operations.get_git_diff_for_commit")
    @patch("mcp_coder.prompt_manager.get_prompt")
    @patch("mcp_coder.workflow_utils.commit_operations.ask_llm")
    def test_generate_commit_message_claude_api_error(
        self,
        mock_ask_llm: Mock,
        mock_get_prompt: Mock,
        mock_get_diff: Mock,
        mock_stage: Mock,
        mock_prepare_env: Mock,
    ) -> None:
        """Test Claude API error handling."""
        mock_prepare_env.return_value = {"MCP_CODER_PROJECT_DIR": "/test/repo"}
        mock_stage.return_value = True
        mock_get_diff.return_value = "some changes"
        mock_get_prompt.return_value = "prompt text"
        mock_ask_llm.side_effect = ClaudeAPIError("API rate limit exceeded")

        project_dir = Path("/test/repo")
        success, message, error = generate_commit_message_with_llm(
            project_dir, "claude", "api"
        )

        assert success is False
        assert message == ""
        error_str: str = error or ""
        assert "API rate limit exceeded" in error_str

    @patch("mcp_coder.workflow_utils.commit_operations.prepare_llm_environment")
    @patch("mcp_coder.workflow_utils.commit_operations.stage_all_changes")
    @patch("mcp_coder.workflow_utils.commit_operations.get_git_diff_for_commit")
    @patch("mcp_coder.prompt_manager.get_prompt")
    @patch("mcp_coder.workflow_utils.commit_operations.ask_llm")
    def test_generate_commit_message_llm_exception(
        self,
        mock_ask_llm: Mock,
        mock_get_prompt: Mock,
        mock_get_diff: Mock,
        mock_stage: Mock,
        mock_prepare_env: Mock,
    ) -> None:
        """Test LLM communication exception handling."""
        mock_prepare_env.return_value = {"MCP_CODER_PROJECT_DIR": "/test/repo"}
        mock_stage.return_value = True
        mock_get_diff.return_value = "some changes"
        mock_get_prompt.return_value = "prompt text"
        mock_ask_llm.side_effect = Exception("Network error")

        project_dir = Path("/test/repo")
        success, message, error = generate_commit_message_with_llm(
            project_dir, "claude", "api"
        )

        assert success is False
        assert message == ""
        error_str: str = error or ""
        assert "LLM communication failed" in error_str
        assert "Network error" in error_str
        assert "internet connection" in error_str

    @patch("mcp_coder.workflow_utils.commit_operations.prepare_llm_environment")
    @patch("mcp_coder.workflow_utils.commit_operations.stage_all_changes")
    @patch("mcp_coder.workflow_utils.commit_operations.get_git_diff_for_commit")
    @patch("mcp_coder.prompt_manager.get_prompt")
    @patch("mcp_coder.workflow_utils.commit_operations.ask_llm")
    @patch("mcp_coder.workflow_utils.commit_operations.parse_llm_commit_response")
    def test_generate_commit_message_empty_parsed_message(
        self,
        mock_parse_response: Mock,
        mock_ask_llm: Mock,
        mock_get_prompt: Mock,
        mock_get_diff: Mock,
        mock_stage: Mock,
        mock_prepare_env: Mock,
    ) -> None:
        """Test empty parsed commit message handling."""
        mock_prepare_env.return_value = {"MCP_CODER_PROJECT_DIR": "/test/repo"}
        mock_stage.return_value = True
        mock_get_diff.return_value = "some changes"
        mock_get_prompt.return_value = "prompt text"
        mock_ask_llm.return_value = "some response"
        mock_parse_response.return_value = ("", None)

        project_dir = Path("/test/repo")
        success, message, error = generate_commit_message_with_llm(
            project_dir, "claude", "api"
        )

        assert success is False
        assert message == ""
        error_str: str = error or ""
        assert "LLM generated an empty commit message" in error_str
        assert "AI may not have understood" in error_str

    @patch("mcp_coder.workflow_utils.commit_operations.prepare_llm_environment")
    @patch("mcp_coder.workflow_utils.commit_operations.stage_all_changes")
    @patch("mcp_coder.workflow_utils.commit_operations.get_git_diff_for_commit")
    @patch("mcp_coder.prompt_manager.get_prompt")
    @patch("mcp_coder.workflow_utils.commit_operations.ask_llm")
    @patch("mcp_coder.workflow_utils.commit_operations.parse_llm_commit_response")
    def test_generate_commit_message_empty_first_line(
        self,
        mock_parse_response: Mock,
        mock_ask_llm: Mock,
        mock_get_prompt: Mock,
        mock_get_diff: Mock,
        mock_stage: Mock,
        mock_prepare_env: Mock,
    ) -> None:
        """Test invalid commit message format handling."""
        mock_prepare_env.return_value = {"MCP_CODER_PROJECT_DIR": "/test/repo"}
        mock_stage.return_value = True
        mock_get_diff.return_value = "some changes"
        mock_get_prompt.return_value = "prompt text"
        mock_ask_llm.return_value = "some response"
        # Simulate a commit message that starts with empty line (invalid)
        mock_parse_response.return_value = ("\n\nActual content here", None)

        project_dir = Path("/test/repo")
        success, message, error = generate_commit_message_with_llm(
            project_dir, "claude", "api"
        )

        assert success is False
        assert message == ""
        error_str: str = error or ""
        assert "LLM generated a commit message with empty first line" in error_str
        assert "invalid for git commits" in error_str

    @patch("mcp_coder.workflow_utils.commit_operations.prepare_llm_environment")
    @patch("mcp_coder.workflow_utils.commit_operations.stage_all_changes")
    @patch("mcp_coder.workflow_utils.commit_operations.get_git_diff_for_commit")
    @patch("mcp_coder.prompt_manager.get_prompt")
    @patch("mcp_coder.workflow_utils.commit_operations.ask_llm")
    @patch("mcp_coder.workflow_utils.commit_operations.parse_llm_commit_response")
    def test_generate_commit_message_parsing_exception(
        self,
        mock_parse_response: Mock,
        mock_ask_llm: Mock,
        mock_get_prompt: Mock,
        mock_get_diff: Mock,
        mock_stage: Mock,
        mock_prepare_env: Mock,
    ) -> None:
        """Test parsing exception handling."""
        mock_prepare_env.return_value = {"MCP_CODER_PROJECT_DIR": "/test/repo"}
        mock_stage.return_value = True
        mock_get_diff.return_value = "some changes"
        mock_get_prompt.return_value = "prompt text"
        mock_ask_llm.return_value = "some response"
        mock_parse_response.side_effect = Exception("Parsing error")

        project_dir = Path("/test/repo")
        success, message, error = generate_commit_message_with_llm(
            project_dir, "claude", "api"
        )

        assert success is False
        assert message == ""
        error_str: str = error or ""
        assert "Error parsing LLM response" in error_str
        assert "Parsing error" in error_str
        assert "unexpected format" in error_str

    @patch("mcp_coder.workflow_utils.commit_operations.prepare_llm_environment")
    @patch("mcp_coder.workflow_utils.commit_operations.stage_all_changes")
    @patch("mcp_coder.workflow_utils.commit_operations.get_git_diff_for_commit")
    @patch("mcp_coder.prompt_manager.get_prompt")
    @patch("mcp_coder.workflow_utils.commit_operations.ask_llm")
    def test_generate_commit_message_large_diff_warning(
        self,
        mock_ask_llm: Mock,
        mock_get_prompt: Mock,
        mock_get_diff: Mock,
        mock_stage: Mock,
        mock_prepare_env: Mock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test warning for very large git diff."""
        mock_prepare_env.return_value = {"MCP_CODER_PROJECT_DIR": "/test/repo"}
        mock_stage.return_value = True
        # Create a very large diff (>100KB)
        large_diff = "diff --git a/file.py b/file.py\n" + "+" + "x" * 100000
        mock_get_diff.return_value = large_diff
        mock_get_prompt.return_value = "prompt text"
        mock_ask_llm.return_value = "feat: add feature"

        project_dir = Path("/test/repo")

        with caplog.at_level(logging.WARNING):
            success, message, error = generate_commit_message_with_llm(
                project_dir, "claude", "api"
            )

        assert success is True
        assert message == "feat: add feature"
        assert error is None

        # Check that warning was logged for large diff
        warning_messages = [
            record.message for record in caplog.records if record.levelname == "WARNING"
        ]
        assert any("Git diff is very large" in msg for msg in warning_messages)

    @patch("mcp_coder.workflow_utils.commit_operations.prepare_llm_environment")
    @patch("mcp_coder.workflow_utils.commit_operations.stage_all_changes")
    @patch("mcp_coder.workflow_utils.commit_operations.get_git_diff_for_commit")
    @patch("mcp_coder.prompt_manager.get_prompt")
    @patch("mcp_coder.workflow_utils.commit_operations.ask_llm")
    def test_generate_commit_message_long_summary_warning(
        self,
        mock_ask_llm: Mock,
        mock_get_prompt: Mock,
        mock_get_diff: Mock,
        mock_stage: Mock,
        mock_prepare_env: Mock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test warning for very long commit summary."""
        mock_prepare_env.return_value = {"MCP_CODER_PROJECT_DIR": "/test/repo"}
        mock_stage.return_value = True
        mock_get_diff.return_value = "some changes"
        mock_get_prompt.return_value = "prompt text"
        # Create a very long commit message (>100 chars)
        long_message = "feat: " + "x" * 200
        mock_ask_llm.return_value = long_message

        project_dir = Path("/test/repo")

        with caplog.at_level(logging.WARNING):
            success, message, error = generate_commit_message_with_llm(
                project_dir, "claude", "api"
            )

        assert success is True
        assert message == long_message
        assert error is None

        # Check that warning was logged for long summary
        warning_messages = [
            record.message for record in caplog.records if record.levelname == "WARNING"
        ]
        assert any(
            "Generated commit summary is very long" in msg for msg in warning_messages
        )


class TestParseLLMCommitResponse:
    """Tests for parse_llm_commit_response function."""

    def test_parse_llm_commit_response_single_line(self) -> None:
        """Test parsing single line LLM response."""
        response = "feat: add new feature"

        summary, body = parse_llm_commit_response(response)

        assert summary == "feat: add new feature"
        assert body is None


class TestStripClaudeFooters:
    """Tests for strip_claude_footers function."""

    # Basic functionality tests
    def test_strip_no_footers_present(self) -> None:
        """Test message with no footers remains unchanged."""
        message = "feat: clean commit message"

        expected = "feat: clean commit message"

        result = strip_claude_footers(message)
        assert result == expected

    def test_strip_robot_emoji_footer_only(self) -> None:
        """Test stripping message with only robot emoji footer."""
        message = """fix: bug fix

🤖 Generated with [Claude Code](https://claude.com/claude-code)"""

        expected = "fix: bug fix"

        result = strip_claude_footers(message)
        assert result == expected

    def test_strip_coauthored_footer_only(self) -> None:
        """Test stripping message with only Co-Authored footer."""
        message = """docs: update readme

Co-Authored-By: Claude <noreply@anthropic.com>"""

        expected = "docs: update readme"

        result = strip_claude_footers(message)
        assert result == expected

    def test_strip_both_footers_present(self) -> None:
        """Test stripping message with both footers present."""
        message = """feat: add new feature

Some commit body text

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"""

        expected = """feat: add new feature

Some commit body text"""

        result = strip_claude_footers(message)
        assert result == expected

    # Edge cases
    def test_strip_empty_message(self) -> None:
        """Test empty message remains unchanged."""
        message = ""

        expected = ""

        result = strip_claude_footers(message)
        assert result == expected

    def test_strip_footers_only_whitespace(self) -> None:
        """Test handling input with only whitespace."""
        message = "   \n\t  \n  "

        expected = ""

        result = strip_claude_footers(message)
        assert result == expected

    def test_strip_footers_whitespace_variations(self) -> None:
        """Test handling footers with various whitespace."""
        message = """feat: whitespace test

   🤖 Generated with [Claude Code](https://claude.com/claude-code)   

   Co-Authored-By: Claude <noreply@anthropic.com>   
   """

        expected = "feat: whitespace test"

        result = strip_claude_footers(message)
        assert result == expected

    def test_strip_trailing_blank_lines(self) -> None:
        """Test stripping footers with trailing blank lines."""
        message = """feat: feature with trailing blanks



🤖 Generated with [Claude Code](https://claude.com/claude-code)


"""

        expected = "feat: feature with trailing blanks"

        result = strip_claude_footers(message)
        assert result == expected

    def test_strip_footers_mixed_with_blank_lines(self) -> None:
        """Test footers mixed with various blank lines."""
        message = """feat: mixed blank lines

Some body content


🤖 Generated with [Claude Code](https://claude.com/claude-code)


Co-Authored-By: Claude <noreply@anthropic.com>


"""

        expected = """feat: mixed blank lines

Some body content"""

        result = strip_claude_footers(message)
        assert result == expected

    def test_strip_footers_multiple_occurrences(self) -> None:
        """Test handling multiple occurrences of footer patterns."""
        message = """feat: multiple footers

🤖 Generated with [Claude Code](https://claude.com/claude-code)
Some content here
Co-Authored-By: Claude <noreply@anthropic.com>
More content
🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"""

        # Only removes footers from the end, preserves content in middle
        expected = """feat: multiple footers

🤖 Generated with [Claude Code](https://claude.com/claude-code)
Some content here
Co-Authored-By: Claude <noreply@anthropic.com>
More content"""

        result = strip_claude_footers(message)
        assert result == expected

    def test_strip_footers_case_sensitive(self) -> None:
        """Test that footer matching is case sensitive."""
        message = """feat: case test

co-authored-by: claude <noreply@anthropic.com>
🤖 generated with [claude code](https://claude.com/claude-code)"""

        # Robot emoji line is removed (starts with 🤖), but co-authored line remains (wrong case)
        expected = """feat: case test

co-authored-by: claude <noreply@anthropic.com>"""

        result = strip_claude_footers(message)
        assert result == expected

    # Content preservation tests
    def test_preserve_legitimate_content(self) -> None:
        """Test preservation of legitimate content that mentions footers."""
        message = """feat: add 🤖 emoji support

This commit adds robot emoji support.
The Co-Authored-By feature is also mentioned.

🤖 Generated with [Claude Code](https://claude.com/claude-code)"""

        expected = """feat: add 🤖 emoji support

This commit adds robot emoji support.
The Co-Authored-By feature is also mentioned."""

        result = strip_claude_footers(message)
        assert result == expected

    def test_strip_footers_preserve_multiline_body(self) -> None:
        """Test preservation of multi-line body content."""
        message = """feat: complex commit

This is the first paragraph of the body.

This is the second paragraph with more details.
It spans multiple lines and should be preserved.

And a third paragraph here.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"""

        expected = """feat: complex commit

This is the first paragraph of the body.

This is the second paragraph with more details.
It spans multiple lines and should be preserved.

And a third paragraph here."""

        result = strip_claude_footers(message)
        assert result == expected

    def test_parse_llm_commit_response_multi_line(self) -> None:
        """Test parsing multi-line LLM response."""
        response = """feat: add new feature

This adds a new authentication feature
with proper error handling."""

        summary, body = parse_llm_commit_response(response)

        assert (
            summary
            == "feat: add new feature\n\nThis adds a new authentication feature\nwith proper error handling."
        )
        assert (
            body
            == "This adds a new authentication feature\nwith proper error handling."
        )

    def test_parse_llm_commit_response_multi_line_with_extra_spacing(self) -> None:
        """Test parsing multi-line LLM response with extra spacing."""
        response = """   feat: add new feature   

   This adds a new authentication feature   
   with proper error handling.   
   
   Additional details here.   """

        summary, body = parse_llm_commit_response(response)

        expected_summary = "feat: add new feature\n\nThis adds a new authentication feature\nwith proper error handling.\n\nAdditional details here."
        expected_body = "This adds a new authentication feature\nwith proper error handling.\n\nAdditional details here."

        assert summary == expected_summary
        assert body == expected_body

    def test_parse_llm_commit_response_empty(self) -> None:
        """Test parsing empty LLM response."""
        response = ""

        summary, body = parse_llm_commit_response(response)

        assert summary == ""
        assert body is None

    def test_parse_llm_commit_response_none(self) -> None:
        """Test parsing None LLM response."""
        response = None

        summary, body = parse_llm_commit_response(response)

        assert summary == ""
        assert body is None

    def test_parse_llm_commit_response_whitespace_only(self) -> None:
        """Test parsing whitespace-only LLM response."""
        response = "   \n  \t  \n  "

        summary, body = parse_llm_commit_response(response)

        assert summary == ""
        assert body is None

    def test_parse_llm_commit_response_single_line_with_whitespace(self) -> None:
        """Test parsing single line with surrounding whitespace."""
        response = "   feat: add new feature   "

        summary, body = parse_llm_commit_response(response)

        assert summary == "feat: add new feature"
        assert body is None

    def test_parse_llm_commit_response_empty_lines_between_content(self) -> None:
        """Test parsing response with empty lines between content."""
        response = """feat: add new feature


This is the body content


More body content here"""

        summary, body = parse_llm_commit_response(response)

        expected_summary = "feat: add new feature\n\nThis is the body content\n\nMore body content here"
        expected_body = "This is the body content\n\nMore body content here"

        assert summary == expected_summary
        assert body == expected_body

    def test_parse_llm_commit_response_only_empty_lines_after_summary(self) -> None:
        """Test parsing response with only empty lines after summary."""
        response = """feat: add new feature




"""

        summary, body = parse_llm_commit_response(response)

        assert summary == "feat: add new feature"
        assert body is None
