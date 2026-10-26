"""Tests for commit operations utilities."""

import logging
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from mcp_coder.llm.providers.claude.errors import ClaudeAPIError
from mcp_coder.workflow_utils.commit_operations import (
    generate_commit_message_with_llm,
    parse_llm_commit_response,
)


class TestGenerateCommitMessageWithLLM:
    """Tests for generate_commit_message_with_llm function."""

    @patch("mcp_coder.workflow_utils.commit_operations.prepare_llm_environment")
    @patch("mcp_coder.workflow_utils.commit_operations.stage_all_changes")
    @patch("mcp_coder.workflow_utils.commit_operations.get_git_diff_for_commit")
    @patch("mcp_coder.prompt_manager.get_prompt")
    @patch("mcp_coder.workflow_utils.commit_operations.prompt_llm")
    def test_generate_commit_message_success(
        self,
        mock_prompt_llm: Mock,
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
        mock_prompt_llm.return_value = {
            "text": "feat: add new feature\n\n🤖 Generated with [Claude Code](https://claude.com/claude-code)\n\nCo-Authored-By: Claude <noreply@anthropic.com>",
            "session_id": None,
            "provider": "claude",
            "version": None,
            "timestamp": None,
            "raw_response": None,
        }

        project_dir = Path("/test/repo")

        success, message, error = generate_commit_message_with_llm(
            project_dir, "claude"
        )

        assert success is True
        assert message == "feat: add new feature"
        assert error is None

        # Verify calls
        mock_prepare_env.assert_called_once_with(project_dir)
        mock_stage.assert_called_once_with(project_dir)
        mock_get_diff.assert_called_once_with(project_dir)
        mock_prompt_llm.assert_called_once()
        # Verify env_vars was passed to prompt_llm
        call_kwargs = mock_prompt_llm.call_args[1]
        assert call_kwargs["env_vars"] == {"MCP_CODER_PROJECT_DIR": "/test/repo"}

    @patch("mcp_coder.workflow_utils.commit_operations.prepare_llm_environment")
    @patch("mcp_coder.workflow_utils.commit_operations.stage_all_changes")
    @patch("mcp_coder.workflow_utils.commit_operations.get_git_diff_for_commit")
    @patch("mcp_coder.prompt_manager.get_prompt")
    @patch("mcp_coder.workflow_utils.commit_operations.prompt_llm")
    def test_generate_commit_message_with_custom_provider(
        self,
        mock_prompt_llm: Mock,
        mock_get_prompt: Mock,
        mock_get_diff: Mock,
        mock_stage: Mock,
        mock_prepare_env: Mock,
    ) -> None:
        """Test LLM commit message generation with custom provider."""
        # Setup mocks
        mock_prepare_env.return_value = {"MCP_CODER_PROJECT_DIR": "/test/repo"}
        mock_stage.return_value = True
        mock_get_diff.return_value = "diff --git a/file.py b/file.py\n+new line"
        mock_get_prompt.return_value = "Generate commit message"
        mock_prompt_llm.return_value = {
            "text": "feat: add new feature\n\n🤖 Generated with [Claude Code](https://claude.com/claude-code)\n\nCo-Authored-By: Claude <noreply@anthropic.com>",
            "session_id": None,
            "provider": "claude",
            "version": None,
            "timestamp": None,
            "raw_response": None,
        }

        project_dir = Path("/test/repo")

        success, message, error = generate_commit_message_with_llm(
            project_dir, provider="claude"
        )

        assert success is True
        assert message == "feat: add new feature"
        assert error is None

        # Verify prompt_llm was called with correct provider
        mock_prompt_llm.assert_called_once()
        call_args = mock_prompt_llm.call_args
        assert call_args[1]["provider"] == "claude"

    @patch("mcp_coder.workflow_utils.commit_operations.prepare_llm_environment")
    @patch("mcp_coder.workflow_utils.commit_operations.stage_all_changes")
    @patch("mcp_coder.workflow_utils.commit_operations.get_git_diff_for_commit")
    @patch("mcp_coder.prompt_manager.get_prompt")
    @patch("mcp_coder.workflow_utils.commit_operations.prompt_llm")
    def test_generate_commit_message_forwards_session_params(
        self,
        mock_prompt_llm: Mock,
        mock_get_prompt: Mock,
        mock_get_diff: Mock,
        mock_stage: Mock,
        mock_prepare_env: Mock,
    ) -> None:
        """Test mcp_config/settings_file/project_dir are forwarded to prompt_llm."""
        mock_prepare_env.return_value = {"MCP_CODER_PROJECT_DIR": "/test/repo"}
        mock_stage.return_value = True
        mock_get_diff.return_value = "diff --git a/file.py b/file.py\n+new line"
        mock_get_prompt.return_value = "Generate commit message"
        mock_prompt_llm.return_value = {
            "text": "feat: add new feature",
            "session_id": None,
            "provider": "claude",
            "version": None,
            "timestamp": None,
            "raw_response": None,
        }

        project_dir = Path("/test/repo")

        success, message, error = generate_commit_message_with_llm(
            project_dir,
            "claude",
            mcp_config="cfg.json",
            settings_file="s.json",
        )

        assert success is True
        assert message == "feat: add new feature"
        assert error is None

        mock_prompt_llm.assert_called_once()
        call_kwargs = mock_prompt_llm.call_args.kwargs
        assert call_kwargs["project_dir"] == str(project_dir)
        assert call_kwargs["mcp_config"] == "cfg.json"
        assert call_kwargs["settings_file"] == "s.json"

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
            project_dir, "claude"
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
            project_dir, "claude"
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
            project_dir, "claude"
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
            project_dir, "claude"
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
            project_dir, "claude"
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
            project_dir, "claude"
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
            project_dir, "claude"
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
    @patch("mcp_coder.workflow_utils.commit_operations.prompt_llm")
    def test_generate_commit_message_empty_llm_response(
        self,
        mock_prompt_llm: Mock,
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
        mock_prompt_llm.return_value = {
            "text": "",
            "session_id": None,
            "provider": "claude",
            "version": None,
            "timestamp": None,
            "raw_response": None,
        }

        project_dir = Path("/test/repo")
        success, message, error = generate_commit_message_with_llm(
            project_dir, "claude"
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
    @patch("mcp_coder.workflow_utils.commit_operations.prompt_llm")
    def test_generate_commit_message_claude_api_error(
        self,
        mock_prompt_llm: Mock,
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
        mock_prompt_llm.side_effect = ClaudeAPIError("API rate limit exceeded")

        project_dir = Path("/test/repo")
        success, message, error = generate_commit_message_with_llm(
            project_dir, "claude"
        )

        assert success is False
        assert message == ""
        error_str: str = error or ""
        assert "API rate limit exceeded" in error_str

    @patch("mcp_coder.workflow_utils.commit_operations.prepare_llm_environment")
    @patch("mcp_coder.workflow_utils.commit_operations.stage_all_changes")
    @patch("mcp_coder.workflow_utils.commit_operations.get_git_diff_for_commit")
    @patch("mcp_coder.prompt_manager.get_prompt")
    @patch("mcp_coder.workflow_utils.commit_operations.prompt_llm")
    def test_generate_commit_message_llm_exception(
        self,
        mock_prompt_llm: Mock,
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
        mock_prompt_llm.side_effect = Exception("Network error")

        project_dir = Path("/test/repo")
        success, message, error = generate_commit_message_with_llm(
            project_dir, "claude"
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
    @patch("mcp_coder.workflow_utils.commit_operations.prompt_llm")
    @patch("mcp_coder.workflow_utils.commit_operations.parse_llm_commit_response")
    def test_generate_commit_message_empty_parsed_message(
        self,
        mock_parse_response: Mock,
        mock_prompt_llm: Mock,
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
        mock_prompt_llm.return_value = {
            "text": "some response",
            "session_id": None,
            "provider": "claude",
            "version": None,
            "timestamp": None,
            "raw_response": None,
        }
        mock_parse_response.return_value = ("", None)

        project_dir = Path("/test/repo")
        success, message, error = generate_commit_message_with_llm(
            project_dir, "claude"
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
    @patch("mcp_coder.workflow_utils.commit_operations.prompt_llm")
    @patch("mcp_coder.workflow_utils.commit_operations.parse_llm_commit_response")
    def test_generate_commit_message_empty_first_line(
        self,
        mock_parse_response: Mock,
        mock_prompt_llm: Mock,
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
        mock_prompt_llm.return_value = {
            "text": "some response",
            "session_id": None,
            "provider": "claude",
            "version": None,
            "timestamp": None,
            "raw_response": None,
        }
        # Simulate a commit message that starts with empty line (invalid)
        mock_parse_response.return_value = ("\n\nActual content here", None)

        project_dir = Path("/test/repo")
        success, message, error = generate_commit_message_with_llm(
            project_dir, "claude"
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
    @patch("mcp_coder.workflow_utils.commit_operations.prompt_llm")
    @patch("mcp_coder.workflow_utils.commit_operations.parse_llm_commit_response")
    def test_generate_commit_message_parsing_exception(
        self,
        mock_parse_response: Mock,
        mock_prompt_llm: Mock,
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
        mock_prompt_llm.return_value = {
            "text": "some response",
            "session_id": None,
            "provider": "claude",
            "version": None,
            "timestamp": None,
            "raw_response": None,
        }
        mock_parse_response.side_effect = Exception("Parsing error")

        project_dir = Path("/test/repo")
        success, message, error = generate_commit_message_with_llm(
            project_dir, "claude"
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
    @patch("mcp_coder.workflow_utils.commit_operations.prompt_llm")
    def test_generate_commit_message_large_diff_warning(
        self,
        mock_prompt_llm: Mock,
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
        mock_prompt_llm.return_value = {
            "text": "feat: add feature",
            "session_id": None,
            "provider": "claude",
            "version": None,
            "timestamp": None,
            "raw_response": None,
        }

        project_dir = Path("/test/repo")

        with caplog.at_level(logging.WARNING):
            success, message, error = generate_commit_message_with_llm(
                project_dir, "claude"
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
    @patch("mcp_coder.workflow_utils.commit_operations.prompt_llm")
    def test_generate_commit_message_long_summary_warning(
        self,
        mock_prompt_llm: Mock,
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
        mock_prompt_llm.return_value = {
            "text": long_message,
            "session_id": None,
            "provider": "claude",
            "version": None,
            "timestamp": None,
            "raw_response": None,
        }

        project_dir = Path("/test/repo")

        with caplog.at_level(logging.WARNING):
            success, message, error = generate_commit_message_with_llm(
                project_dir, "claude"
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
