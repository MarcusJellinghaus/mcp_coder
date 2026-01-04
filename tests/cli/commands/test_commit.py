"""Tests for commit command functionality."""

import argparse
import sys
from io import StringIO
from pathlib import Path
from typing import Any
from unittest import mock
from unittest.mock import MagicMock, Mock, patch

import pytest

from mcp_coder.cli.commands.commit import execute_commit_auto, validate_git_repository
from mcp_coder.utils.commit_operations import (
    generate_commit_message_with_llm,
    parse_llm_commit_response,
)


class TestExecuteCommitAuto:
    """Tests for execute_commit_auto function."""

    @patch("mcp_coder.cli.commands.commit.validate_git_repository")
    @patch("mcp_coder.cli.commands.commit.parse_llm_method_from_args")
    @patch("mcp_coder.cli.commands.commit.generate_commit_message_with_llm")
    @patch("mcp_coder.cli.commands.commit.commit_staged_files")
    def test_execute_commit_auto_success(
        self,
        mock_commit: Mock,
        mock_generate: Mock,
        mock_parse_llm: Mock,
        mock_validate: Mock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test successful commit auto execution."""
        # Setup mocks
        mock_validate.return_value = (True, None)
        mock_parse_llm.return_value = ("claude", "api")
        mock_generate.return_value = (True, "feat: add new feature", None)
        mock_commit.return_value = {
            "success": True,
            "commit_hash": "abc1234",
            "error": None,
        }

        args = argparse.Namespace(
            preview=False, llm_method="claude_code_api", project_dir=None
        )

        result = execute_commit_auto(args)

        assert result == 0
        captured = capsys.readouterr()
        captured_out: str = captured.out or ""
        assert "SUCCESS: Commit created: abc1234" in captured_out

        # Verify function calls
        mock_validate.assert_called_once()
        mock_parse_llm.assert_called_once_with("claude_code_api")
        mock_generate.assert_called_once_with(
            Path.cwd(), "claude", "api", execution_dir=mock.ANY
        )
        mock_commit.assert_called_once_with("feat: add new feature", Path.cwd())

    @patch("mcp_coder.cli.commands.commit.validate_git_repository")
    @patch("mcp_coder.cli.commands.commit.parse_llm_method_from_args")
    @patch("mcp_coder.cli.commands.commit.generate_commit_message_with_llm")
    @patch("mcp_coder.cli.commands.commit.commit_staged_files")
    @patch("builtins.input")
    def test_execute_commit_auto_with_preview_confirmed(
        self,
        mock_input: Mock,
        mock_commit: Mock,
        mock_generate: Mock,
        mock_parse_llm: Mock,
        mock_validate: Mock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test commit auto with preview mode - user confirms."""
        # Setup mocks
        mock_validate.return_value = (True, None)
        mock_parse_llm.return_value = ("claude", "api")
        mock_generate.return_value = (True, "feat: add new feature", None)
        mock_commit.return_value = {
            "success": True,
            "commit_hash": "abc1234",
            "error": None,
        }
        mock_input.return_value = "y"

        args = argparse.Namespace(
            preview=True, llm_method="claude_code_api", project_dir=None
        )

        result = execute_commit_auto(args)

        assert result == 0
        captured = capsys.readouterr()
        captured_out: str = captured.out or ""
        assert "Generated commit message:" in captured_out
        assert "feat: add new feature" in captured_out
        assert "SUCCESS: Commit created: abc1234" in captured_out

        # Verify input was called
        mock_input.assert_called_once_with("\nProceed with commit? (Y/n): ")

    @patch("mcp_coder.cli.commands.commit.validate_git_repository")
    @patch("mcp_coder.cli.commands.commit.parse_llm_method_from_args")
    @patch("mcp_coder.cli.commands.commit.generate_commit_message_with_llm")
    @patch("mcp_coder.cli.commands.commit.commit_staged_files")
    @patch("builtins.input")
    def test_execute_commit_auto_preview_empty_input_proceeds(
        self,
        mock_input: Mock,
        mock_commit: Mock,
        mock_generate: Mock,
        mock_parse_llm: Mock,
        mock_validate: Mock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test commit auto with preview mode - empty input proceeds as default."""
        # Setup mocks
        mock_validate.return_value = (True, None)
        mock_parse_llm.return_value = ("claude", "api")
        mock_generate.return_value = (True, "feat: add new feature", None)
        mock_commit.return_value = {
            "success": True,
            "commit_hash": "abc1234",
            "error": None,
        }
        mock_input.return_value = ""  # Empty input (just pressed Enter)

        args = argparse.Namespace(
            preview=True, llm_method="claude_code_api", project_dir=None
        )

        result = execute_commit_auto(args)

        assert result == 0
        captured = capsys.readouterr()
        captured_out: str = captured.out or ""
        assert "Generated commit message:" in captured_out
        assert "SUCCESS: Commit created: abc1234" in captured_out
        # Should NOT see "Commit cancelled"
        assert "Commit cancelled" not in captured_out

    @patch("mcp_coder.cli.commands.commit.validate_git_repository")
    @patch("mcp_coder.cli.commands.commit.parse_llm_method_from_args")
    @patch("mcp_coder.cli.commands.commit.generate_commit_message_with_llm")
    @patch("builtins.input")
    def test_execute_commit_auto_with_preview_cancelled(
        self,
        mock_input: Mock,
        mock_generate: Mock,
        mock_parse_llm: Mock,
        mock_validate: Mock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test commit auto with preview mode - user cancels."""
        # Setup mocks
        mock_validate.return_value = (True, None)
        mock_parse_llm.return_value = ("claude", "api")
        mock_generate.return_value = (True, "feat: add new feature", None)
        mock_input.return_value = "n"

        args = argparse.Namespace(
            preview=True, llm_method="claude_code_api", project_dir=None
        )

        result = execute_commit_auto(args)

        assert result == 0
        captured = capsys.readouterr()
        captured_out: str = captured.out or ""
        assert "Generated commit message:" in captured_out
        assert "Commit cancelled." in captured_out

    @patch("mcp_coder.cli.commands.commit.validate_git_repository")
    @patch("mcp_coder.cli.commands.commit.parse_llm_method_from_args")
    @patch("mcp_coder.cli.commands.commit.generate_commit_message_with_llm")
    @patch("mcp_coder.cli.commands.commit.commit_staged_files")
    @patch("builtins.input")
    def test_execute_commit_auto_preview_various_cancel_inputs(
        self,
        mock_input: Mock,
        mock_commit: Mock,
        mock_generate: Mock,
        mock_parse_llm: Mock,
        mock_validate: Mock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test commit auto with preview mode - various cancel inputs."""
        # Setup mocks
        mock_validate.return_value = (True, None)
        mock_parse_llm.return_value = ("claude", "api")
        mock_generate.return_value = (True, "feat: add new feature", None)
        mock_commit.return_value = {
            "success": True,
            "commit_hash": "abc1234",
            "error": None,
        }

        args = argparse.Namespace(
            preview=True, llm_method="claude_code_api", project_dir=None
        )

        # Test various ways to cancel
        cancel_inputs = ["n", "N", "no", "No", "NO", "nope", "Nope"]
        for cancel_input in cancel_inputs:
            mock_input.return_value = cancel_input
            result = execute_commit_auto(args)
            assert result == 0, f"Failed to cancel with input: {cancel_input}"

        # Test various ways to proceed (default behavior)
        proceed_inputs = [
            "",
            "y",
            "Y",
            "yes",
            "Yes",
            "YES",
            "yeah",
            "yep",
            "sure",
            "ok",
        ]
        for proceed_input in proceed_inputs:
            mock_input.return_value = proceed_input
            result = execute_commit_auto(args)
            assert result == 0, f"Failed to proceed with input: '{proceed_input}'"
            # Should have proceeded to commit
            captured = capsys.readouterr()
            captured_out: str = captured.out or ""
            if proceed_input != "":  # Empty string test might not show success message
                continue
            # For empty string (default), should proceed
            mock_input.return_value = ""
            result = execute_commit_auto(args)
            assert result == 0

    @patch("mcp_coder.cli.commands.commit.validate_git_repository")
    def test_execute_commit_auto_not_git_repo(
        self, mock_validate: Mock, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test commit auto in non-git directory."""
        mock_validate.return_value = (False, "Not a git repository")

        args = argparse.Namespace(
            preview=False, llm_method="claude_code_api", project_dir=None
        )

        result = execute_commit_auto(args)

        assert result == 1
        captured = capsys.readouterr()
        captured_err: str = captured.err or ""
        assert "Error: Not a git repository" in captured_err

    @patch("mcp_coder.cli.commands.commit.validate_git_repository")
    @patch("mcp_coder.cli.commands.commit.parse_llm_method_from_args")
    @patch("mcp_coder.cli.commands.commit.generate_commit_message_with_llm")
    def test_execute_commit_auto_no_changes(
        self,
        mock_generate: Mock,
        mock_parse_llm: Mock,
        mock_validate: Mock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test commit auto with no staged changes."""
        mock_validate.return_value = (True, None)
        mock_parse_llm.return_value = ("claude", "api")
        mock_generate.return_value = (
            False,
            "",
            "No changes to commit. Ensure you have modified, added, or deleted files before running commit auto.",
        )

        args = argparse.Namespace(
            preview=False, llm_method="claude_code_api", project_dir=None
        )

        result = execute_commit_auto(args)

        assert result == 2
        captured = capsys.readouterr()
        captured_err: str = captured.err or ""
        assert "Error: No changes to commit" in captured_err


class TestPreviewModeLogic:
    """Tests specifically for preview mode user input logic."""

    @patch("mcp_coder.cli.commands.commit.validate_git_repository")
    @patch("mcp_coder.cli.commands.commit.parse_llm_method_from_args")
    @patch("mcp_coder.cli.commands.commit.generate_commit_message_with_llm")
    @patch("mcp_coder.cli.commands.commit.commit_staged_files")
    @patch("builtins.input")
    def test_preview_mode_cancel_variations(
        self,
        mock_input: Mock,
        mock_commit: Mock,
        mock_generate: Mock,
        mock_parse_llm: Mock,
        mock_validate: Mock,
    ) -> None:
        """Test various ways to cancel in preview mode."""
        mock_validate.return_value = (True, None)
        mock_parse_llm.return_value = ("claude", "api")
        mock_generate.return_value = (True, "feat: test", None)
        args = argparse.Namespace(
            preview=True, llm_method="claude_code_api", project_dir=None
        )

        cancel_inputs = ["n", "N", "no", "No", "NO", "nope", "never", "nah"]
        for cancel_input in cancel_inputs:
            mock_input.return_value = cancel_input
            result = execute_commit_auto(args)
            assert result == 0  # Cancelled successfully
            # Should not call commit
            mock_commit.assert_not_called()
            mock_commit.reset_mock()

    @patch("mcp_coder.cli.commands.commit.validate_git_repository")
    @patch("mcp_coder.cli.commands.commit.parse_llm_method_from_args")
    @patch("mcp_coder.cli.commands.commit.generate_commit_message_with_llm")
    @patch("mcp_coder.cli.commands.commit.commit_staged_files")
    @patch("builtins.input")
    def test_preview_mode_proceed_variations(
        self,
        mock_input: Mock,
        mock_commit: Mock,
        mock_generate: Mock,
        mock_parse_llm: Mock,
        mock_validate: Mock,
    ) -> None:
        """Test various ways to proceed in preview mode."""
        mock_validate.return_value = (True, None)
        mock_parse_llm.return_value = ("claude", "api")
        mock_generate.return_value = (True, "feat: test", None)
        mock_commit.return_value = {
            "success": True,
            "commit_hash": "abc123",
            "error": None,
        }
        args = argparse.Namespace(
            preview=True, llm_method="claude_code_api", project_dir=None
        )

        proceed_inputs = [
            "",
            "y",
            "Y",
            "yes",
            "Yes",
            "YES",
            "yeah",
            "yep",
            "sure",
            "ok",
            "anything",
        ]
        for proceed_input in proceed_inputs:
            mock_input.return_value = proceed_input
            result = execute_commit_auto(args)
            assert result == 0  # Success
            # Should call commit
            mock_commit.assert_called_once_with("feat: test", Path.cwd())
            mock_commit.reset_mock()


class TestGenerateCommitMessageWithLLM:
    """Tests for generate_commit_message_with_llm function."""

    @patch("mcp_coder.utils.commit_operations.stage_all_changes")
    @patch("mcp_coder.utils.commit_operations.get_git_diff_for_commit")
    @patch("mcp_coder.utils.commit_operations.get_prompt")
    @patch("mcp_coder.utils.commit_operations.ask_llm")
    def test_generate_commit_message_with_llm_success(
        self,
        mock_ask_llm: Mock,
        mock_get_prompt: Mock,
        mock_get_diff: Mock,
        mock_stage: Mock,
    ) -> None:
        """Test successful LLM commit message generation."""
        # Setup mocks
        mock_stage.return_value = True
        mock_get_diff.return_value = "diff --git a/file.py b/file.py\n+new line"
        mock_get_prompt.return_value = "Generate commit message"
        mock_ask_llm.return_value = "feat: add new feature"

        project_dir = Path("/test/repo")

        success, message, error = generate_commit_message_with_llm(project_dir)

        assert success is True
        assert message == "feat: add new feature"
        assert error is None

        # Verify calls
        mock_stage.assert_called_once_with(project_dir)
        mock_get_diff.assert_called_once_with(project_dir)
        mock_ask_llm.assert_called_once()

    @patch("mcp_coder.utils.commit_operations.stage_all_changes")
    def test_generate_commit_message_with_llm_stage_failure(
        self, mock_stage: Mock
    ) -> None:
        """Test LLM generation with staging failure."""
        mock_stage.return_value = False

        project_dir = Path("/test/repo")

        success, message, error = generate_commit_message_with_llm(project_dir)

        assert success is False
        assert message == ""
        error_str: str = error or ""
        assert "Failed to stage changes in repository" in error_str
        assert "write permissions" in error_str

    @patch("mcp_coder.utils.commit_operations.stage_all_changes")
    @patch("mcp_coder.utils.commit_operations.get_git_diff_for_commit")
    def test_generate_commit_message_with_llm_no_changes(
        self, mock_get_diff: Mock, mock_stage: Mock
    ) -> None:
        """Test LLM generation with no changes."""
        mock_stage.return_value = True
        mock_get_diff.return_value = ""

        project_dir = Path("/test/repo")

        success, message, error = generate_commit_message_with_llm(project_dir)

        assert success is False
        assert message == ""
        error_str: str = error or ""
        assert "No changes to commit" in error_str
        assert "modified, added, or deleted files" in error_str

    @patch("mcp_coder.utils.commit_operations.stage_all_changes")
    @patch("mcp_coder.utils.commit_operations.get_git_diff_for_commit")
    @patch("mcp_coder.utils.commit_operations.get_prompt")
    @patch("mcp_coder.utils.commit_operations.ask_llm")
    def test_generate_commit_message_with_llm_failure(
        self,
        mock_ask_llm: Mock,
        mock_get_prompt: Mock,
        mock_get_diff: Mock,
        mock_stage: Mock,
    ) -> None:
        """Test LLM failure handling."""
        # Setup mocks
        mock_stage.return_value = True
        mock_get_diff.return_value = "diff --git a/file.py b/file.py\n+new line"
        mock_get_prompt.return_value = "Generate commit message"
        mock_ask_llm.side_effect = Exception("LLM API error")

        project_dir = Path("/test/repo")

        success, message, error = generate_commit_message_with_llm(project_dir)

        assert success is False
        assert message == ""
        error_str: str = error or ""
        assert "LLM communication failed" in error_str
        assert "internet connection" in error_str


class TestParseLLMCommitResponse:
    """Tests for parse_llm_commit_response function."""

    def test_parse_llm_commit_response_single_line(self) -> None:
        """Test parsing single line LLM response."""
        response = "feat: add new feature"

        summary, body = parse_llm_commit_response(response)

        assert summary == "feat: add new feature"
        assert body is None

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

    def test_parse_llm_commit_response_empty(self) -> None:
        """Test parsing empty LLM response."""
        response = ""

        summary, body = parse_llm_commit_response(response)

        assert summary == ""
        assert body is None

    def test_parse_llm_commit_response_whitespace_only(self) -> None:
        """Test parsing whitespace-only LLM response."""
        response = "   \n  \t  \n  "

        summary, body = parse_llm_commit_response(response)

        assert summary == ""
        assert body is None


class TestValidateGitRepository:
    """Tests for validate_git_repository function."""

    @patch("mcp_coder.cli.commands.commit.is_git_repository")
    @patch("mcp_coder.cli.commands.commit.get_git_diff_for_commit")
    @patch("mcp_coder.cli.commands.commit.stage_all_changes")
    def test_validate_git_repository_valid(
        self, mock_stage: Mock, mock_get_diff: Mock, mock_is_git: Mock
    ) -> None:
        """Test git repository validation success."""
        mock_is_git.return_value = True
        mock_get_diff.return_value = "diff --git a/file.py b/file.py\n+new line"

        project_dir = Path("/test/repo")

        success, error = validate_git_repository(project_dir)

        assert success is True
        assert error is None

    @patch("mcp_coder.cli.commands.commit.is_git_repository")
    def test_validate_git_repository_invalid(self, mock_is_git: Mock) -> None:
        """Test git repository validation failure."""
        mock_is_git.return_value = False

        project_dir = Path("/test/not_repo")

        success, error = validate_git_repository(project_dir)

        assert success is False
        assert error == "Not a git repository"

    @patch("mcp_coder.cli.commands.commit.is_git_repository")
    @patch("mcp_coder.cli.commands.commit.get_git_diff_for_commit")
    @patch("mcp_coder.cli.commands.commit.stage_all_changes")
    def test_validate_git_repository_no_changes(
        self, mock_stage: Mock, mock_get_diff: Mock, mock_is_git: Mock
    ) -> None:
        """Test validation with no changes."""
        mock_is_git.return_value = True
        mock_get_diff.return_value = ""
        mock_stage.return_value = False

        project_dir = Path("/test/repo")

        success, error = validate_git_repository(project_dir)

        assert success is False
        assert error == "No changes to commit"


class TestGenerateCommitMessageWithLLMExtended:
    """Additional tests for the improved generate_commit_message_with_llm function."""

    @patch("mcp_coder.utils.commit_operations.stage_all_changes")
    def test_stage_exception_handling(self, mock_stage: Mock) -> None:
        """Test staging operation exception handling."""
        mock_stage.side_effect = Exception("Permission denied")

        project_dir = Path("/test/repo")
        success, message, error = generate_commit_message_with_llm(project_dir)

        assert success is False
        assert message == ""
        error_str: str = error or ""
        assert "Error staging changes" in error_str
        assert "Permission denied" in error_str
        assert "git repository is accessible" in error_str

    @patch("mcp_coder.utils.commit_operations.stage_all_changes")
    @patch("mcp_coder.utils.commit_operations.get_git_diff_for_commit")
    def test_git_diff_none_handling(
        self, mock_get_diff: Mock, mock_stage: Mock
    ) -> None:
        """Test git diff returning None."""
        mock_stage.return_value = True
        mock_get_diff.return_value = None

        project_dir = Path("/test/repo")
        success, message, error = generate_commit_message_with_llm(project_dir)

        assert success is False
        assert message == ""
        error_str: str = error or ""
        assert "Failed to retrieve git diff" in error_str
        assert "invalid state" in error_str

    @patch("mcp_coder.utils.commit_operations.stage_all_changes")
    @patch("mcp_coder.utils.commit_operations.get_git_diff_for_commit")
    @patch("mcp_coder.utils.commit_operations.get_prompt")
    def test_prompt_file_not_found(
        self, mock_get_prompt: Mock, mock_get_diff: Mock, mock_stage: Mock
    ) -> None:
        """Test prompt file not found error."""
        mock_stage.return_value = True
        mock_get_diff.return_value = "some changes"
        mock_get_prompt.side_effect = FileNotFoundError("prompts.md not found")

        project_dir = Path("/test/repo")
        success, message, error = generate_commit_message_with_llm(project_dir)

        assert success is False
        assert message == ""
        error_str: str = error or ""
        assert "Commit prompt template not found" in error_str
        assert "prompts.md not found" in error_str

    @patch("mcp_coder.utils.commit_operations.stage_all_changes")
    @patch("mcp_coder.utils.commit_operations.get_git_diff_for_commit")
    @patch("mcp_coder.utils.commit_operations.get_prompt")
    @patch("mcp_coder.utils.commit_operations.ask_llm")
    def test_empty_llm_response(
        self,
        mock_ask_llm: Mock,
        mock_get_prompt: Mock,
        mock_get_diff: Mock,
        mock_stage: Mock,
    ) -> None:
        """Test empty LLM response handling."""
        mock_stage.return_value = True
        mock_get_diff.return_value = "some changes"
        mock_get_prompt.return_value = "prompt text"
        mock_ask_llm.return_value = ""

        project_dir = Path("/test/repo")
        success, message, error = generate_commit_message_with_llm(project_dir)

        assert success is False
        assert message == ""
        error_str: str = error or ""
        assert "LLM returned empty or null response" in error_str
        assert "AI service may be unavailable" in error_str

    @patch("mcp_coder.utils.commit_operations.stage_all_changes")
    @patch("mcp_coder.utils.commit_operations.get_git_diff_for_commit")
    @patch("mcp_coder.utils.commit_operations.get_prompt")
    @patch("mcp_coder.utils.commit_operations.ask_llm")
    @patch("mcp_coder.utils.commit_operations.parse_llm_commit_response")
    def test_empty_parsed_commit_message(
        self,
        mock_parse: Mock,
        mock_ask_llm: Mock,
        mock_get_prompt: Mock,
        mock_get_diff: Mock,
        mock_stage: Mock,
    ) -> None:
        """Test empty parsed commit message handling."""
        mock_stage.return_value = True
        mock_get_diff.return_value = "some changes"
        mock_get_prompt.return_value = "prompt text"
        mock_ask_llm.return_value = "some response"
        mock_parse.return_value = ("", None)

        project_dir = Path("/test/repo")
        success, message, error = generate_commit_message_with_llm(project_dir)

        assert success is False
        assert message == ""
        error_str: str = error or ""
        assert "LLM generated an empty commit message" in error_str
        assert "AI may not have understood" in error_str

    @patch("mcp_coder.utils.commit_operations.stage_all_changes")
    @patch("mcp_coder.utils.commit_operations.get_git_diff_for_commit")
    @patch("mcp_coder.utils.commit_operations.get_prompt")
    @patch("mcp_coder.utils.commit_operations.ask_llm")
    @patch("mcp_coder.utils.commit_operations.parse_llm_commit_response")
    def test_invalid_commit_message_format(
        self,
        mock_parse: Mock,
        mock_ask_llm: Mock,
        mock_get_prompt: Mock,
        mock_get_diff: Mock,
        mock_stage: Mock,
    ) -> None:
        """Test invalid commit message format handling."""
        mock_stage.return_value = True
        mock_get_diff.return_value = "some changes"
        mock_get_prompt.return_value = "prompt text"
        mock_ask_llm.return_value = "some response"
        # Simulate a commit message that starts with empty line (invalid)
        mock_parse.return_value = ("\n\nActual content here", None)

        project_dir = Path("/test/repo")
        success, message, error = generate_commit_message_with_llm(project_dir)

        assert success is False
        assert message == ""
        error_str: str = error or ""
        assert "LLM generated a commit message with empty first line" in error_str
        assert "invalid for git commits" in error_str


class TestCommitAutoExecutionDir:
    """Tests for execution_dir handling in commit auto command."""

    @patch("mcp_coder.cli.commands.commit.validate_git_repository")
    @patch("mcp_coder.cli.commands.commit.parse_llm_method_from_args")
    @patch("mcp_coder.cli.commands.commit.generate_commit_message_with_llm")
    @patch("mcp_coder.cli.commands.commit.commit_staged_files")
    def test_default_execution_dir_uses_cwd(
        self,
        mock_commit: Mock,
        mock_generate: Mock,
        mock_parse_llm: Mock,
        mock_validate: Mock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test default execution_dir should use current working directory."""
        # Setup mocks
        mock_validate.return_value = (True, None)
        mock_parse_llm.return_value = ("claude", "api")
        mock_generate.return_value = (True, "feat: add new feature", None)
        mock_commit.return_value = {
            "success": True,
            "commit_hash": "abc1234",
            "error": None,
        }

        args = argparse.Namespace(
            preview=False,
            llm_method="claude_code_api",
            project_dir=None,
            execution_dir=None,  # No explicit execution_dir
        )

        result = execute_commit_auto(args)

        assert result == 0
        # Verify generate_commit_message_with_llm was called
        # Note: The actual execution_dir handling will be added to the function
        mock_generate.assert_called_once()

    @patch("mcp_coder.cli.commands.commit.validate_git_repository")
    @patch("mcp_coder.cli.commands.commit.parse_llm_method_from_args")
    @patch("mcp_coder.cli.commands.commit.generate_commit_message_with_llm")
    @patch("mcp_coder.cli.commands.commit.commit_staged_files")
    def test_explicit_execution_dir_validated(
        self,
        mock_commit: Mock,
        mock_generate: Mock,
        mock_parse_llm: Mock,
        mock_validate: Mock,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test explicit execution_dir should be validated and used."""
        # Setup mocks
        mock_validate.return_value = (True, None)
        mock_parse_llm.return_value = ("claude", "api")
        mock_generate.return_value = (True, "feat: add new feature", None)
        mock_commit.return_value = {
            "success": True,
            "commit_hash": "abc1234",
            "error": None,
        }

        # Create a valid temporary directory
        execution_dir = tmp_path / "exec_dir"
        execution_dir.mkdir()

        args = argparse.Namespace(
            preview=False,
            llm_method="claude_code_api",
            project_dir=None,
            execution_dir=str(execution_dir),
        )

        result = execute_commit_auto(args)

        assert result == 0
        captured = capsys.readouterr()
        captured_out: str = captured.out or ""
        assert "SUCCESS: Commit created: abc1234" in captured_out

    @patch("mcp_coder.cli.commands.commit.validate_git_repository")
    def test_invalid_execution_dir_returns_error(
        self,
        mock_validate: Mock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test invalid execution_dir should return error code 1."""
        mock_validate.return_value = (True, None)

        args = argparse.Namespace(
            preview=False,
            llm_method="claude_code_api",
            project_dir=None,
            execution_dir="/nonexistent/invalid/path",
        )

        result = execute_commit_auto(args)

        assert result == 1
        captured = capsys.readouterr()
        assert "Error" in captured.err
        assert "execution directory" in captured.err.lower()

    @patch("mcp_coder.cli.commands.commit.validate_git_repository")
    @patch("mcp_coder.cli.commands.commit.parse_llm_method_from_args")
    @patch("mcp_coder.cli.commands.commit.generate_commit_message_with_llm")
    @patch("mcp_coder.cli.commands.commit.commit_staged_files")
    @patch("builtins.input")
    def test_execution_dir_with_preview_mode(
        self,
        mock_input: Mock,
        mock_commit: Mock,
        mock_generate: Mock,
        mock_parse_llm: Mock,
        mock_validate: Mock,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test execution_dir works with preview mode (no conflicts)."""
        # Setup mocks
        mock_validate.return_value = (True, None)
        mock_parse_llm.return_value = ("claude", "api")
        mock_generate.return_value = (True, "feat: add new feature", None)
        mock_commit.return_value = {
            "success": True,
            "commit_hash": "abc1234",
            "error": None,
        }
        mock_input.return_value = "y"

        # Create a valid temporary directory
        execution_dir = tmp_path / "exec_dir"
        execution_dir.mkdir()

        args = argparse.Namespace(
            preview=True,
            llm_method="claude_code_api",
            project_dir=None,
            execution_dir=str(execution_dir),
        )

        result = execute_commit_auto(args)

        assert result == 0
        captured = capsys.readouterr()
        captured_out: str = captured.out or ""
        assert "Generated commit message:" in captured_out
        assert "SUCCESS: Commit created: abc1234" in captured_out
