"""Tests for commit command functionality."""

import argparse
import logging
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from mcp_coder.cli.commands.commit import (
    _push_after_commit,
    execute_commit_auto,
    validate_git_repository,
)
from mcp_coder.cli.main import create_parser


class TestCommitAutoParserNoMcpConfig:
    """Tests that --mcp-config is NOT accepted by commit auto."""

    def test_commit_auto_no_mcp_config_arg(self) -> None:
        """--mcp-config should not be accepted by commit auto parser."""
        parser = create_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["commit", "auto", "--mcp-config", "some_config.json"])

    def test_commit_auto_accepts_llm_method(self) -> None:
        """--llm-method should still be accepted by commit auto."""
        parser = create_parser()
        args = parser.parse_args(["commit", "auto", "--llm-method", "langchain"])
        assert args.llm_method == "langchain"


class TestExecuteCommitAutoResolveTuple:
    """Tests that commit auto properly destructures resolve_llm_method tuple."""

    @patch("mcp_coder.cli.commands.commit.validate_git_repository")
    @patch("mcp_coder.cli.commands.commit.resolve_llm_method")
    @patch("mcp_coder.cli.commands.commit.parse_llm_method_from_args")
    @patch("mcp_coder.cli.commands.commit.generate_commit_message_with_llm")
    @patch("mcp_coder.cli.commands.commit.commit_staged_files")
    def test_resolve_llm_method_tuple_destructured(
        self,
        mock_commit: Mock,
        mock_generate: Mock,
        mock_parse_llm: Mock,
        mock_resolve: Mock,
        mock_validate: Mock,
    ) -> None:
        """resolve_llm_method returns (provider, source) tuple; only provider is used."""
        mock_validate.return_value = (True, None)
        mock_resolve.return_value = ("langchain", "config default_provider")
        mock_parse_llm.return_value = "langchain"
        mock_generate.return_value = (True, "feat: test", None)
        mock_commit.return_value = {
            "success": True,
            "commit_hash": "abc1234",
            "error": None,
        }

        args = argparse.Namespace(preview=False, llm_method=None, project_dir=None)

        result = execute_commit_auto(args)

        assert result == 0
        mock_resolve.assert_called_once_with(None)
        # parse_llm_method_from_args should receive the provider string, not the tuple
        mock_parse_llm.assert_called_once_with("langchain")


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
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test successful commit auto execution."""
        # Setup mocks
        mock_validate.return_value = (True, None)
        mock_parse_llm.return_value = "claude"
        mock_generate.return_value = (True, "feat: add new feature", None)
        mock_commit.return_value = {
            "success": True,
            "commit_hash": "abc1234",
            "error": None,
        }

        args = argparse.Namespace(preview=False, llm_method="claude", project_dir=None)

        with caplog.at_level(logging.DEBUG):
            result = execute_commit_auto(args)

        assert result == 0
        assert "SUCCESS: Commit created: abc1234" in caplog.text

        # Verify function calls
        mock_validate.assert_called_once()
        mock_parse_llm.assert_called_once_with("claude")
        mock_generate.assert_called_once_with(Path.cwd(), "claude")
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
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test commit auto with preview mode - user confirms."""
        # Setup mocks
        mock_validate.return_value = (True, None)
        mock_parse_llm.return_value = "claude"
        mock_generate.return_value = (True, "feat: add new feature", None)
        mock_commit.return_value = {
            "success": True,
            "commit_hash": "abc1234",
            "error": None,
        }
        mock_input.return_value = "y"

        args = argparse.Namespace(preview=True, llm_method="claude", project_dir=None)

        with caplog.at_level(logging.DEBUG):
            result = execute_commit_auto(args)

        assert result == 0
        captured = capsys.readouterr()
        captured_out: str = captured.out or ""
        # Preview display still uses print()
        assert "Generated commit message:" in captured_out
        assert "feat: add new feature" in captured_out
        # Success message now goes through logging
        assert "SUCCESS: Commit created: abc1234" in caplog.text

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
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test commit auto with preview mode - empty input proceeds as default."""
        # Setup mocks
        mock_validate.return_value = (True, None)
        mock_parse_llm.return_value = "claude"
        mock_generate.return_value = (True, "feat: add new feature", None)
        mock_commit.return_value = {
            "success": True,
            "commit_hash": "abc1234",
            "error": None,
        }
        mock_input.return_value = ""  # Empty input (just pressed Enter)

        args = argparse.Namespace(preview=True, llm_method="claude", project_dir=None)

        with caplog.at_level(logging.DEBUG):
            result = execute_commit_auto(args)

        assert result == 0
        captured = capsys.readouterr()
        captured_out: str = captured.out or ""
        assert "Generated commit message:" in captured_out
        assert "SUCCESS: Commit created: abc1234" in caplog.text
        # Should NOT see "Commit cancelled"
        assert "Commit cancelled" not in caplog.text

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
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test commit auto with preview mode - user cancels."""
        # Setup mocks
        mock_validate.return_value = (True, None)
        mock_parse_llm.return_value = "claude"
        mock_generate.return_value = (True, "feat: add new feature", None)
        mock_input.return_value = "n"

        args = argparse.Namespace(preview=True, llm_method="claude", project_dir=None)

        with caplog.at_level(logging.DEBUG):
            result = execute_commit_auto(args)

        assert result == 0
        captured = capsys.readouterr()
        captured_out: str = captured.out or ""
        assert "Generated commit message:" in captured_out
        assert "Commit cancelled." in caplog.text

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
        mock_parse_llm.return_value = "claude"
        mock_generate.return_value = (True, "feat: add new feature", None)
        mock_commit.return_value = {
            "success": True,
            "commit_hash": "abc1234",
            "error": None,
        }

        args = argparse.Namespace(preview=True, llm_method="claude", project_dir=None)

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
            _ = captured.out or ""
            if proceed_input != "":  # Empty string test might not show success message
                continue
            # For empty string (default), should proceed
            mock_input.return_value = ""
            result = execute_commit_auto(args)
            assert result == 0

    @patch("mcp_coder.cli.commands.commit.validate_git_repository")
    def test_execute_commit_auto_not_git_repo(
        self, mock_validate: Mock, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test commit auto in non-git directory."""
        mock_validate.return_value = (False, "Not a git repository")

        args = argparse.Namespace(preview=False, llm_method="claude", project_dir=None)

        with caplog.at_level(logging.DEBUG):
            result = execute_commit_auto(args)

        assert result == 1
        assert "Not a git repository" in caplog.text

    @patch("mcp_coder.cli.commands.commit.validate_git_repository")
    @patch("mcp_coder.cli.commands.commit.parse_llm_method_from_args")
    @patch("mcp_coder.cli.commands.commit.generate_commit_message_with_llm")
    def test_execute_commit_auto_no_changes(
        self,
        mock_generate: Mock,
        mock_parse_llm: Mock,
        mock_validate: Mock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test commit auto with no staged changes."""
        mock_validate.return_value = (True, None)
        mock_parse_llm.return_value = "claude"
        mock_generate.return_value = (
            False,
            "",
            "No changes to commit. Ensure you have modified, added, or deleted files before running commit auto.",
        )

        args = argparse.Namespace(preview=False, llm_method="claude", project_dir=None)

        with caplog.at_level(logging.DEBUG):
            result = execute_commit_auto(args)

        assert result == 2
        assert "No changes to commit" in caplog.text


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
        mock_parse_llm.return_value = "claude"
        mock_generate.return_value = (True, "feat: test", None)
        args = argparse.Namespace(preview=True, llm_method="claude", project_dir=None)

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
        mock_parse_llm.return_value = "claude"
        mock_generate.return_value = (True, "feat: test", None)
        mock_commit.return_value = {
            "success": True,
            "commit_hash": "abc123",
            "error": None,
        }
        args = argparse.Namespace(preview=True, llm_method="claude", project_dir=None)

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


class TestCommitAutoClaudeCwd:
    """Tests for Claude working directory handling in commit auto command."""

    @patch("mcp_coder.cli.commands.commit.validate_git_repository")
    @patch("mcp_coder.cli.commands.commit.parse_llm_method_from_args")
    @patch("mcp_coder.cli.commands.commit.generate_commit_message_with_llm")
    @patch("mcp_coder.cli.commands.commit.commit_staged_files")
    def test_no_project_dir_uses_cwd(
        self,
        mock_commit: Mock,
        mock_generate: Mock,
        mock_parse_llm: Mock,
        mock_validate: Mock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """With no --project-dir the current working directory is used."""
        # Setup mocks
        mock_validate.return_value = (True, None)
        mock_parse_llm.return_value = "claude"
        mock_generate.return_value = (True, "feat: add new feature", None)
        mock_commit.return_value = {
            "success": True,
            "commit_hash": "abc1234",
            "error": None,
        }

        args = argparse.Namespace(
            preview=False,
            llm_method="claude",
            project_dir=None,
        )

        result = execute_commit_auto(args)

        assert result == 0
        mock_generate.assert_called_once()

    @patch("mcp_coder.cli.commands.commit.validate_git_repository")
    @patch("mcp_coder.cli.commands.commit.parse_llm_method_from_args")
    @patch("mcp_coder.cli.commands.commit.generate_commit_message_with_llm")
    @patch("mcp_coder.cli.commands.commit.commit_staged_files")
    @patch("builtins.input")
    def test_claude_cwd_with_preview_mode(
        self,
        mock_input: Mock,
        mock_commit: Mock,
        mock_generate: Mock,
        mock_parse_llm: Mock,
        mock_validate: Mock,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Resolving the Claude cwd works with preview mode (no conflicts)."""
        # Setup mocks
        mock_validate.return_value = (True, None)
        mock_parse_llm.return_value = "claude"
        mock_generate.return_value = (True, "feat: add new feature", None)
        mock_commit.return_value = {
            "success": True,
            "commit_hash": "abc1234",
            "error": None,
        }
        mock_input.return_value = "y"

        project_dir = tmp_path / "repo"
        project_dir.mkdir()

        args = argparse.Namespace(
            preview=True,
            llm_method="claude",
            project_dir=str(project_dir),
        )

        with caplog.at_level(logging.DEBUG):
            result = execute_commit_auto(args)

        assert result == 0
        captured = capsys.readouterr()
        captured_out: str = captured.out or ""
        assert "Generated commit message:" in captured_out
        assert "SUCCESS: Commit created: abc1234" in caplog.text

    @patch("mcp_coder.cli.commands.commit.validate_git_repository")
    @patch("mcp_coder.cli.commands.commit.parse_llm_method_from_args")
    @patch("mcp_coder.cli.commands.commit.generate_commit_message_with_llm")
    @patch("mcp_coder.cli.commands.commit.commit_staged_files")
    def test_claude_cwd_is_project_dir(
        self,
        mock_commit: Mock,
        mock_generate: Mock,
        mock_parse_llm: Mock,
        mock_validate: Mock,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        """Claude's working directory is project_dir, not the shell's cwd."""
        mock_validate.return_value = (True, None)
        mock_parse_llm.return_value = "claude"
        mock_generate.return_value = (True, "feat: add new feature", None)
        mock_commit.return_value = {
            "success": True,
            "commit_hash": "abc1234",
            "error": None,
        }

        project_dir = tmp_path / "repo"
        project_dir.mkdir()
        elsewhere = tmp_path / "elsewhere"
        elsewhere.mkdir()

        args = argparse.Namespace(
            preview=False,
            llm_method="claude",
            project_dir=str(project_dir),
        )

        # Stand outside the project directory before resolving.
        monkeypatch.chdir(elsewhere)

        result = execute_commit_auto(args)

        assert result == 0
        assert mock_generate.call_args[0][0] == project_dir.resolve()
        assert mock_generate.call_args[0][0] != Path.cwd()


MODULE = "mcp_coder.cli.commands.commit"


class TestPushAfterCommit:
    """Tests for _push_after_commit helper function."""

    @patch(f"{MODULE}.get_current_branch_name", return_value="feature/foo")
    @patch(f"{MODULE}.get_default_branch_name", return_value="main")
    @patch(f"{MODULE}.has_remote_tracking_branch", return_value=True)
    @patch(f"{MODULE}.git_push", return_value={"success": True})
    def test_push_success_with_tracking_branch(
        self,
        mock_git_push: Mock,
        mock_has_tracking: Mock,
        mock_default: Mock,
        mock_current: Mock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Push succeeds when tracking branch exists and git_push succeeds."""
        with caplog.at_level(logging.INFO):
            result = _push_after_commit(Path("/test/repo"))

        assert result == 0
        assert "Pushed to origin/" in caplog.text
        mock_git_push.assert_called_once_with(Path("/test/repo"))

    @patch(f"{MODULE}.get_current_branch_name", return_value="feature/bar")
    @patch(f"{MODULE}.get_default_branch_name", return_value="main")
    @patch(f"{MODULE}.has_remote_tracking_branch", return_value=False)
    @patch(f"{MODULE}.push_branch", return_value=True)
    def test_push_success_new_branch(
        self,
        mock_push_branch: Mock,
        mock_has_tracking: Mock,
        mock_default: Mock,
        mock_current: Mock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Push succeeds for new branch without tracking, sets upstream."""
        with caplog.at_level(logging.INFO):
            result = _push_after_commit(Path("/test/repo"))

        assert result == 0
        mock_push_branch.assert_called_once_with(
            "feature/bar", Path("/test/repo"), set_upstream=True
        )
        assert "Pushed to origin/" in caplog.text

    @patch(f"{MODULE}.get_current_branch_name", return_value="main")
    @patch(f"{MODULE}.get_default_branch_name", return_value="main")
    def test_push_refused_on_default_branch(
        self,
        mock_default: Mock,
        mock_current: Mock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Push is refused when on the default branch."""
        with caplog.at_level(logging.ERROR):
            result = _push_after_commit(Path("/test/repo"))

        assert result == 2
        assert "protected branch" in caplog.text

    @patch(f"{MODULE}.get_current_branch_name", return_value="main")
    @patch(f"{MODULE}.get_default_branch_name", return_value=None)
    def test_push_refused_fallback_main(
        self,
        mock_default: Mock,
        mock_current: Mock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Push is refused on 'main' when default branch detection returns None."""
        with caplog.at_level(logging.ERROR):
            result = _push_after_commit(Path("/test/repo"))

        assert result == 2

    @patch(f"{MODULE}.get_current_branch_name", return_value="master")
    @patch(f"{MODULE}.get_default_branch_name", return_value=None)
    def test_push_refused_fallback_master(
        self,
        mock_default: Mock,
        mock_current: Mock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Push is refused on 'master' when default branch detection returns None."""
        with caplog.at_level(logging.ERROR):
            result = _push_after_commit(Path("/test/repo"))

        assert result == 2

    @patch(f"{MODULE}.get_current_branch_name", return_value="feature/foo")
    @patch(f"{MODULE}.get_default_branch_name", return_value="main")
    @patch(f"{MODULE}.has_remote_tracking_branch", return_value=True)
    @patch(
        f"{MODULE}.git_push",
        return_value={"success": False, "error": "rejected"},
    )
    def test_push_failure_with_tracking(
        self,
        mock_git_push: Mock,
        mock_has_tracking: Mock,
        mock_default: Mock,
        mock_current: Mock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Push fails when git_push returns failure."""
        with caplog.at_level(logging.ERROR):
            result = _push_after_commit(Path("/test/repo"))

        assert result == 2
        assert "Failed to push" in caplog.text

    @patch(f"{MODULE}.get_current_branch_name", return_value="feature/bar")
    @patch(f"{MODULE}.get_default_branch_name", return_value="main")
    @patch(f"{MODULE}.has_remote_tracking_branch", return_value=False)
    @patch(f"{MODULE}.push_branch", return_value=False)
    def test_push_failure_new_branch(
        self,
        mock_push_branch: Mock,
        mock_has_tracking: Mock,
        mock_default: Mock,
        mock_current: Mock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Push fails when push_branch returns False."""
        with caplog.at_level(logging.ERROR):
            result = _push_after_commit(Path("/test/repo"))

        assert result == 2
        assert "Failed to push" in caplog.text

    @patch(f"{MODULE}.get_current_branch_name", return_value=None)
    def test_push_refused_on_detached_head(
        self,
        mock_current: Mock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Push is refused when not on a branch (detached HEAD)."""
        with caplog.at_level(logging.ERROR):
            result = _push_after_commit(Path("/test/repo"))

        assert result == 2
        assert "not on a branch" in caplog.text


class TestCommitAutoPush:
    """Tests for --push integration in execute_commit_auto."""

    @patch(f"{MODULE}.validate_git_repository", return_value=(True, None))
    @patch(f"{MODULE}.resolve_llm_method", return_value=("claude", "cli"))
    @patch(f"{MODULE}.parse_llm_method_from_args", return_value="claude")
    @patch(
        f"{MODULE}.generate_commit_message_with_llm",
        return_value=(True, "feat: test", None),
    )
    @patch(
        f"{MODULE}.commit_staged_files",
        return_value={"success": True, "commit_hash": "abc123", "error": None},
    )
    @patch(f"{MODULE}._push_after_commit", return_value=0)
    def test_commit_auto_push_called_on_success(
        self,
        mock_push: Mock,
        mock_commit: Mock,
        mock_generate: Mock,
        mock_parse: Mock,
        mock_resolve: Mock,
        mock_validate: Mock,
    ) -> None:
        """Push is called after successful commit when --push is set."""
        # "/repo" need not exist: resolve_claude_cwd does not validate it
        args = argparse.Namespace(
            preview=False, llm_method="claude", project_dir="/repo", push=True
        )
        result = execute_commit_auto(args)

        assert result == 0
        # resolve_claude_cwd resolves project_dir before the push
        mock_push.assert_called_once_with(Path("/repo").resolve())

    @patch(f"{MODULE}.validate_git_repository", return_value=(True, None))
    @patch(f"{MODULE}.resolve_llm_method", return_value=("claude", "cli"))
    @patch(f"{MODULE}.parse_llm_method_from_args", return_value="claude")
    @patch(
        f"{MODULE}.generate_commit_message_with_llm",
        return_value=(True, "feat: test", None),
    )
    @patch(
        f"{MODULE}.commit_staged_files",
        return_value={"success": True, "commit_hash": "abc123", "error": None},
    )
    @patch(f"{MODULE}._push_after_commit", return_value=2)
    def test_commit_auto_push_failure_returns_2(
        self,
        mock_push: Mock,
        mock_commit: Mock,
        mock_generate: Mock,
        mock_parse: Mock,
        mock_resolve: Mock,
        mock_validate: Mock,
    ) -> None:
        """Push failure propagates its exit code."""
        # "/repo" need not exist: resolve_claude_cwd does not validate it
        args = argparse.Namespace(
            preview=False, llm_method="claude", project_dir="/repo", push=True
        )
        result = execute_commit_auto(args)

        assert result == 2

    @patch(f"{MODULE}.validate_git_repository", return_value=(True, None))
    @patch(f"{MODULE}.resolve_llm_method", return_value=("claude", "cli"))
    @patch(f"{MODULE}.parse_llm_method_from_args", return_value="claude")
    @patch(
        f"{MODULE}.generate_commit_message_with_llm",
        return_value=(True, "feat: test", None),
    )
    @patch(
        f"{MODULE}.commit_staged_files",
        return_value={"success": True, "commit_hash": "abc123", "error": None},
    )
    @patch(f"{MODULE}._push_after_commit")
    def test_commit_auto_no_push_flag(
        self,
        mock_push: Mock,
        mock_commit: Mock,
        mock_generate: Mock,
        mock_parse: Mock,
        mock_resolve: Mock,
        mock_validate: Mock,
    ) -> None:
        """Push is NOT called when --push is False."""
        # "/repo" need not exist: resolve_claude_cwd does not validate it
        args = argparse.Namespace(
            preview=False, llm_method="claude", project_dir="/repo", push=False
        )
        result = execute_commit_auto(args)

        assert result == 0
        mock_push.assert_not_called()

    @patch(f"{MODULE}.validate_git_repository", return_value=(True, None))
    @patch(f"{MODULE}.resolve_llm_method", return_value=("claude", "cli"))
    @patch(f"{MODULE}.parse_llm_method_from_args", return_value="claude")
    @patch(
        f"{MODULE}.generate_commit_message_with_llm",
        return_value=(False, "", "LLM error"),
    )
    @patch(f"{MODULE}._push_after_commit")
    def test_commit_auto_push_not_called_on_commit_failure(
        self,
        mock_push: Mock,
        mock_generate: Mock,
        mock_parse: Mock,
        mock_resolve: Mock,
        mock_validate: Mock,
    ) -> None:
        """Push is NOT called when commit generation fails."""
        # "/repo" need not exist: resolve_claude_cwd does not validate it
        args = argparse.Namespace(
            preview=False, llm_method="claude", project_dir="/repo", push=True
        )
        result = execute_commit_auto(args)

        assert result == 2
        mock_push.assert_not_called()
