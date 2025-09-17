"""Tests for commit command functionality."""

import argparse
import sys
from io import StringIO
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from src.mcp_coder.cli.commands.commit import (
    execute_commit_auto,
    generate_commit_message_with_llm,
    parse_llm_commit_response,
    validate_git_repository,
)


class TestExecuteCommitAuto:
    """Tests for execute_commit_auto function."""

    @patch("src.mcp_coder.cli.commands.commit.validate_git_repository")
    @patch("src.mcp_coder.cli.commands.commit.generate_commit_message_with_llm")
    @patch("src.mcp_coder.cli.commands.commit.commit_staged_files")
    def test_execute_commit_auto_success(
        self, mock_commit, mock_generate, mock_validate, capsys
    ):
        """Test successful commit auto execution."""
        # Setup mocks
        mock_validate.return_value = (True, None)
        mock_generate.return_value = (True, "feat: add new feature", None)
        mock_commit.return_value = {
            "success": True,
            "commit_hash": "abc1234",
            "error": None,
        }

        args = argparse.Namespace(preview=False)

        result = execute_commit_auto(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "✅ Commit created: abc1234" in captured.out

        # Verify function calls
        mock_validate.assert_called_once()
        mock_generate.assert_called_once()
        mock_commit.assert_called_once_with("feat: add new feature", Path.cwd())

    @patch("src.mcp_coder.cli.commands.commit.validate_git_repository")
    @patch("src.mcp_coder.cli.commands.commit.generate_commit_message_with_llm")
    @patch("src.mcp_coder.cli.commands.commit.commit_staged_files")
    @patch("builtins.input")
    def test_execute_commit_auto_with_preview_confirmed(
        self, mock_input, mock_commit, mock_generate, mock_validate, capsys
    ):
        """Test commit auto with preview mode - user confirms."""
        # Setup mocks
        mock_validate.return_value = (True, None)
        mock_generate.return_value = (True, "feat: add new feature", None)
        mock_commit.return_value = {
            "success": True,
            "commit_hash": "abc1234",
            "error": None,
        }
        mock_input.return_value = "y"

        args = argparse.Namespace(preview=True)

        result = execute_commit_auto(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "Generated commit message:" in captured.out
        assert "feat: add new feature" in captured.out
        assert "✅ Commit created: abc1234" in captured.out

        # Verify input was called
        mock_input.assert_called_once_with("\nProceed with commit? (y/N): ")

    @patch("src.mcp_coder.cli.commands.commit.validate_git_repository")
    @patch("src.mcp_coder.cli.commands.commit.generate_commit_message_with_llm")
    @patch("builtins.input")
    def test_execute_commit_auto_with_preview_cancelled(
        self, mock_input, mock_generate, mock_validate, capsys
    ):
        """Test commit auto with preview mode - user cancels."""
        # Setup mocks
        mock_validate.return_value = (True, None)
        mock_generate.return_value = (True, "feat: add new feature", None)
        mock_input.return_value = "n"

        args = argparse.Namespace(preview=True)

        result = execute_commit_auto(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "Generated commit message:" in captured.out
        assert "Commit cancelled." in captured.out

    @patch("src.mcp_coder.cli.commands.commit.validate_git_repository")
    def test_execute_commit_auto_not_git_repo(self, mock_validate, capsys):
        """Test commit auto in non-git directory."""
        mock_validate.return_value = (False, "Not a git repository")

        args = argparse.Namespace(preview=False)

        result = execute_commit_auto(args)

        assert result == 1
        captured = capsys.readouterr()
        assert "Error: Not a git repository" in captured.err

    @patch("src.mcp_coder.cli.commands.commit.validate_git_repository")
    @patch("src.mcp_coder.cli.commands.commit.generate_commit_message_with_llm")
    def test_execute_commit_auto_no_changes(self, mock_generate, mock_validate, capsys):
        """Test commit auto with no staged changes."""
        mock_validate.return_value = (True, None)
        mock_generate.return_value = (False, "", "No changes to commit")

        args = argparse.Namespace(preview=False)

        result = execute_commit_auto(args)

        assert result == 2
        captured = capsys.readouterr()
        assert "Error: No changes to commit" in captured.err


class TestGenerateCommitMessageWithLLM:
    """Tests for generate_commit_message_with_llm function."""

    @patch("src.mcp_coder.cli.commands.commit.stage_all_changes")
    @patch("src.mcp_coder.cli.commands.commit.get_git_diff_for_commit")
    @patch("src.mcp_coder.cli.commands.commit.get_prompt")
    @patch("src.mcp_coder.cli.commands.commit.ask_llm")
    def test_generate_commit_message_with_llm_success(
        self, mock_ask_llm, mock_get_prompt, mock_get_diff, mock_stage
    ):
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

    @patch("src.mcp_coder.cli.commands.commit.stage_all_changes")
    def test_generate_commit_message_with_llm_stage_failure(self, mock_stage):
        """Test LLM generation with staging failure."""
        mock_stage.return_value = False

        project_dir = Path("/test/repo")

        success, message, error = generate_commit_message_with_llm(project_dir)

        assert success is False
        assert message == ""
        assert "Failed to stage changes" in error

    @patch("src.mcp_coder.cli.commands.commit.stage_all_changes")
    @patch("src.mcp_coder.cli.commands.commit.get_git_diff_for_commit")
    def test_generate_commit_message_with_llm_no_changes(
        self, mock_get_diff, mock_stage
    ):
        """Test LLM generation with no changes."""
        mock_stage.return_value = True
        mock_get_diff.return_value = ""

        project_dir = Path("/test/repo")

        success, message, error = generate_commit_message_with_llm(project_dir)

        assert success is False
        assert message == ""
        assert "No changes to commit" in error

    @patch("src.mcp_coder.cli.commands.commit.stage_all_changes")
    @patch("src.mcp_coder.cli.commands.commit.get_git_diff_for_commit")
    @patch("src.mcp_coder.cli.commands.commit.get_prompt")
    @patch("src.mcp_coder.cli.commands.commit.ask_llm")
    def test_generate_commit_message_with_llm_failure(
        self, mock_ask_llm, mock_get_prompt, mock_get_diff, mock_stage
    ):
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
        assert "LLM communication failed" in error


class TestParseLLMCommitResponse:
    """Tests for parse_llm_commit_response function."""

    def test_parse_llm_commit_response_single_line(self):
        """Test parsing single line LLM response."""
        response = "feat: add new feature"

        summary, body = parse_llm_commit_response(response)

        assert summary == "feat: add new feature"
        assert body is None

    def test_parse_llm_commit_response_multi_line(self):
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

    def test_parse_llm_commit_response_empty(self):
        """Test parsing empty LLM response."""
        response = ""

        summary, body = parse_llm_commit_response(response)

        assert summary == ""
        assert body is None

    def test_parse_llm_commit_response_whitespace_only(self):
        """Test parsing whitespace-only LLM response."""
        response = "   \n  \t  \n  "

        summary, body = parse_llm_commit_response(response)

        assert summary == ""
        assert body is None


class TestValidateGitRepository:
    """Tests for validate_git_repository function."""

    @patch("src.mcp_coder.cli.commands.commit.is_git_repository")
    @patch("src.mcp_coder.cli.commands.commit.get_git_diff_for_commit")
    @patch("src.mcp_coder.cli.commands.commit.stage_all_changes")
    def test_validate_git_repository_valid(
        self, mock_stage, mock_get_diff, mock_is_git
    ):
        """Test git repository validation success."""
        mock_is_git.return_value = True
        mock_get_diff.return_value = "diff --git a/file.py b/file.py\n+new line"

        project_dir = Path("/test/repo")

        success, error = validate_git_repository(project_dir)

        assert success is True
        assert error is None

    @patch("src.mcp_coder.cli.commands.commit.is_git_repository")
    def test_validate_git_repository_invalid(self, mock_is_git):
        """Test git repository validation failure."""
        mock_is_git.return_value = False

        project_dir = Path("/test/not_repo")

        success, error = validate_git_repository(project_dir)

        assert success is False
        assert error == "Not a git repository"

    @patch("src.mcp_coder.cli.commands.commit.is_git_repository")
    @patch("src.mcp_coder.cli.commands.commit.get_git_diff_for_commit")
    @patch("src.mcp_coder.cli.commands.commit.stage_all_changes")
    def test_validate_git_repository_no_changes(
        self, mock_stage, mock_get_diff, mock_is_git
    ):
        """Test validation with no changes."""
        mock_is_git.return_value = True
        mock_get_diff.return_value = ""
        mock_stage.return_value = False

        project_dir = Path("/test/repo")

        success, error = validate_git_repository(project_dir)

        assert success is False
        assert error == "No changes to commit"
