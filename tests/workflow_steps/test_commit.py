"""Tests for workflow_steps commit/push/run_formatters steps."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.workflow_steps.commit import (
    commit_changes,
    push_changes,
    run_formatters,
)


class TestRunFormatters:
    """Test run_formatters function."""

    @patch("mcp_coder.workflow_steps.commit.run_format_code")
    def test_run_formatters_success(self, mock_run_format_code: MagicMock) -> None:
        """Test running formatters successfully."""
        mock_result = MagicMock()
        mock_result.success = True
        mock_run_format_code.return_value = {"black": mock_result, "isort": mock_result}

        result = run_formatters(Path("/test/project"))

        assert result is True
        mock_run_format_code.assert_called_once_with(Path("/test/project"))

    @patch("mcp_coder.workflow_steps.commit.run_format_code")
    def test_run_formatters_failure(self, mock_run_format_code: MagicMock) -> None:
        """Test running formatters with failure."""
        mock_success_result = MagicMock()
        mock_success_result.success = True

        mock_failed_result = MagicMock()
        mock_failed_result.success = False
        mock_failed_result.output = "Black formatting failed"

        mock_run_format_code.return_value = {
            "black": mock_failed_result,
            "isort": mock_success_result,
        }

        result = run_formatters(Path("/test/project"))

        assert result is False

    @patch("mcp_coder.workflow_steps.commit.run_format_code")
    def test_run_formatters_exception(self, mock_run_format_code: MagicMock) -> None:
        """Test running formatters with exception."""
        mock_run_format_code.side_effect = Exception("Formatter error")

        result = run_formatters(Path("/test/project"))

        assert result is False


class TestCommitChanges:
    """Test commit_changes function."""

    @patch("mcp_coder.workflow_steps.commit.commit_all_changes")
    @patch("mcp_coder.workflow_steps.commit.generate_commit_message_with_llm")
    def test_commit_changes_uses_file_when_present(
        self, mock_generate_message: MagicMock, mock_commit: MagicMock, tmp_path: Path
    ) -> None:
        """Test commit_changes uses prepared file instead of LLM."""
        # Create commit message file
        pr_info = tmp_path / "pr_info"
        pr_info.mkdir()
        commit_file = pr_info / ".commit_message.txt"
        commit_file.write_text("feat: prepared message\n\nBody text here.")

        mock_commit.return_value = {
            "success": True,
            "commit_hash": "abc123",
            "error": None,
        }

        result = commit_changes(tmp_path)

        assert result is True
        # LLM should NOT be called
        mock_generate_message.assert_not_called()
        # File should be deleted
        assert not commit_file.exists()
        # Commit should use the prepared message
        mock_commit.assert_called_once()
        call_args = mock_commit.call_args[0]
        assert "feat: prepared message" in call_args[0]

    @patch("mcp_coder.workflow_steps.commit.commit_all_changes")
    @patch("mcp_coder.workflow_steps.commit.generate_commit_message_with_llm")
    def test_commit_changes_falls_back_to_llm_when_no_file(
        self, mock_generate_message: MagicMock, mock_commit: MagicMock, tmp_path: Path
    ) -> None:
        """Test commit_changes falls back to LLM when file doesn't exist."""
        mock_generate_message.return_value = (True, "feat: llm message", None)
        mock_commit.return_value = {
            "success": True,
            "commit_hash": "abc123",
            "error": None,
        }

        result = commit_changes(tmp_path)

        assert result is True
        mock_generate_message.assert_called_once()

    @patch("mcp_coder.workflow_steps.commit.commit_all_changes")
    @patch("mcp_coder.workflow_steps.commit.generate_commit_message_with_llm")
    def test_commit_changes_deletes_empty_file_and_falls_back_to_llm(
        self, mock_generate_message: MagicMock, mock_commit: MagicMock, tmp_path: Path
    ) -> None:
        """Test commit_changes deletes empty file and falls back to LLM."""
        # Create empty commit message file
        pr_info = tmp_path / "pr_info"
        pr_info.mkdir()
        commit_file = pr_info / ".commit_message.txt"
        commit_file.write_text("   \n  ")  # Whitespace only

        mock_generate_message.return_value = (True, "feat: llm message", None)
        mock_commit.return_value = {
            "success": True,
            "commit_hash": "abc123",
            "error": None,
        }

        result = commit_changes(tmp_path)

        assert result is True
        # File should be deleted even though it was empty
        assert not commit_file.exists()
        # LLM should be called as fallback
        mock_generate_message.assert_called_once()

    @patch("mcp_coder.workflow_steps.commit.commit_all_changes")
    @patch("mcp_coder.workflow_steps.commit.generate_commit_message_with_llm")
    def test_commit_changes_success(
        self, mock_generate_message: MagicMock, mock_commit: MagicMock
    ) -> None:
        """Test committing changes successfully."""
        mock_generate_message.return_value = (True, "feat: add new feature", None)
        mock_commit.return_value = {
            "success": True,
            "commit_hash": "abc123",
            "error": None,
        }

        result = commit_changes(Path("/test/project"))

        assert result is True
        mock_generate_message.assert_called_once_with(Path("/test/project"), "claude")
        mock_commit.assert_called_once_with(
            "feat: add new feature", Path("/test/project")
        )

    @patch("mcp_coder.workflow_steps.commit.generate_commit_message_with_llm")
    def test_commit_changes_message_generation_fails(
        self, mock_generate_message: MagicMock
    ) -> None:
        """Test committing changes when message generation fails."""
        mock_generate_message.return_value = (False, None, "LLM error")

        result = commit_changes(Path("/test/project"))

        assert result is False
        mock_generate_message.assert_called_once_with(Path("/test/project"), "claude")

    @patch("mcp_coder.workflow_steps.commit.commit_all_changes")
    @patch("mcp_coder.workflow_steps.commit.generate_commit_message_with_llm")
    def test_commit_changes_commit_fails(
        self, mock_generate_message: MagicMock, mock_commit: MagicMock
    ) -> None:
        """Test committing changes when commit operation fails."""
        mock_generate_message.return_value = (True, "feat: add feature", None)
        mock_commit.return_value = {
            "success": False,
            "commit_hash": None,
            "error": "Git commit failed",
        }

        result = commit_changes(Path("/test/project"))

        assert result is False

    @patch("mcp_coder.workflow_steps.commit.generate_commit_message_with_llm")
    def test_commit_changes_exception(self, mock_generate_message: MagicMock) -> None:
        """Test committing changes with exception."""
        mock_generate_message.side_effect = Exception("Commit error")

        result = commit_changes(Path("/test/project"))

        assert result is False

    @patch("mcp_coder.workflow_steps.commit.commit_all_changes")
    def test_commit_changes_logs_message_on_failure(
        self, mock_commit: MagicMock, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test commit message is logged when commit fails."""
        # Create commit message file
        pr_info = tmp_path / "pr_info"
        pr_info.mkdir()
        commit_file = pr_info / ".commit_message.txt"
        commit_file.write_text("feat: important message")

        mock_commit.return_value = {
            "success": False,
            "commit_hash": None,
            "error": "Git failed",
        }

        result = commit_changes(tmp_path)

        assert result is False
        # Message should be logged so it's not lost
        assert "feat: important message" in caplog.text


class TestPushChanges:
    """Test push_changes function."""

    @patch("mcp_coder.workflow_steps.commit.git_push")
    def test_push_changes_success(self, mock_git_push: MagicMock) -> None:
        """Test pushing changes successfully."""
        mock_git_push.return_value = {"success": True, "error": None}

        result = push_changes(Path("/test/project"))

        assert result is True
        mock_git_push.assert_called_once_with(
            Path("/test/project"), force_with_lease=False
        )

    @patch("mcp_coder.workflow_steps.commit.git_push")
    def test_push_changes_failure(self, mock_git_push: MagicMock) -> None:
        """Test pushing changes with failure."""
        mock_git_push.return_value = {
            "success": False,
            "error": "Remote repository not accessible",
        }

        result = push_changes(Path("/test/project"))

        assert result is False

    @patch("mcp_coder.workflow_steps.commit.git_push")
    def test_push_changes_exception(self, mock_git_push: MagicMock) -> None:
        """Test pushing changes with exception."""
        mock_git_push.side_effect = Exception("Push error")

        result = push_changes(Path("/test/project"))

        assert result is False

    @patch("mcp_coder.workflow_steps.commit.git_push")
    def test_push_changes_with_force_with_lease(self, mock_git_push: MagicMock) -> None:
        """Test pushing changes with force_with_lease=True."""
        mock_git_push.return_value = {"success": True, "error": None}

        result = push_changes(Path("/test/project"), force_with_lease=True)

        assert result is True
        mock_git_push.assert_called_once_with(
            Path("/test/project"), force_with_lease=True
        )

    @patch("mcp_coder.workflow_steps.commit.git_push")
    def test_push_changes_force_with_lease_failure(
        self, mock_git_push: MagicMock
    ) -> None:
        """Test force push with lease when remote has new commits."""
        mock_git_push.return_value = {
            "success": False,
            "error": "failed to push some refs: stale info",
        }

        result = push_changes(Path("/test/project"), force_with_lease=True)

        assert result is False
        mock_git_push.assert_called_once_with(
            Path("/test/project"), force_with_lease=True
        )
