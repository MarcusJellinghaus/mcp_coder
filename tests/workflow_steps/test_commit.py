"""Tests for workflow_steps commit/push/run_formatters steps."""

import logging
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.mcp_tools_py import resolve_steps as real_resolve_steps
from mcp_coder.workflow_steps.commit import (
    FALLBACK_COMMIT_MESSAGE,
    FormatterConfigError,
    check_formatter_config,
    commit_changes,
    push_changes,
    run_formatters,
)

LEGACY_WARNING = "[tool.mcp-coder.implement] format_code is ignored"


def _write_pyproject(project_dir: Path, content: str) -> None:
    (project_dir / "pyproject.toml").write_text(content, encoding="utf-8")


def _raise_value_error(_p: Path) -> list[str]:
    raise ValueError("No formatter declared")


class TestRunFormattersGate:
    """Test the format_code gate and config errors in run_formatters."""

    @patch("mcp_coder.workflow_steps.commit.run_format_code")
    def test_disabled_skips_formatting(
        self, mock_run_format_code: MagicMock, tmp_path: Path
    ) -> None:
        """format_code = false → run_format_code not called, True."""
        _write_pyproject(tmp_path, "[tool.mcp-coder]\nformat_code = false\n")

        assert run_formatters(tmp_path) is True
        mock_run_format_code.assert_not_called()

    @patch("mcp_coder.workflow_steps.commit.run_format_code")
    def test_key_absent_runs_formatting(
        self, mock_run_format_code: MagicMock, tmp_path: Path
    ) -> None:
        """Key absent → run_format_code called."""
        mock_run_format_code.return_value = {}

        assert run_formatters(tmp_path) is True
        mock_run_format_code.assert_called_once_with(tmp_path)

    @patch("mcp_coder.workflow_steps.commit.run_format_code")
    def test_resolve_error_raises_config_error(
        self,
        mock_run_format_code: MagicMock,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """resolve_steps ValueError → FormatterConfigError with its message."""
        monkeypatch.setattr(
            "mcp_coder.workflow_steps.commit.resolve_steps", _raise_value_error
        )

        with pytest.raises(FormatterConfigError, match="No formatter declared"):
            run_formatters(tmp_path)
        mock_run_format_code.assert_not_called()

    @patch("mcp_coder.workflow_steps.commit.run_format_code")
    def test_resolve_error_inside_wrapper_raises_config_error(
        self, mock_run_format_code: MagicMock, tmp_path: Path
    ) -> None:
        """resolve_steps ValueError raised inside run_format_code → config error."""
        mock_run_format_code.side_effect = ValueError("No formatter declared")

        with pytest.raises(FormatterConfigError, match="No formatter declared") as exc:
            run_formatters(tmp_path)
        assert isinstance(exc.value.__cause__, ValueError)

    @patch("mcp_coder.workflow_steps.commit.run_format_code")
    def test_non_bool_format_code_raises_config_error(
        self, mock_run_format_code: MagicMock, tmp_path: Path
    ) -> None:
        """Non-bool format_code → FormatterConfigError."""
        _write_pyproject(tmp_path, '[tool.mcp-coder]\nformat_code = "false"\n')

        with pytest.raises(FormatterConfigError, match="format_code"):
            run_formatters(tmp_path)
        mock_run_format_code.assert_not_called()


class TestCheckFormatterConfig:
    """Test check_formatter_config helper."""

    def test_disabled_returns_none_even_if_resolve_fails(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """format_code = false → None without resolving."""
        _write_pyproject(tmp_path, "[tool.mcp-coder]\nformat_code = false\n")
        monkeypatch.setattr(
            "mcp_coder.workflow_steps.commit.resolve_steps", _raise_value_error
        )

        assert check_formatter_config(tmp_path) is None

    def test_resolves_cleanly_returns_none(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A declared formatter resolves with the real resolve_steps → None."""
        monkeypatch.setattr(
            "mcp_coder.workflow_steps.commit.resolve_steps", real_resolve_steps
        )
        _write_pyproject(tmp_path, "[tool.black]\nline-length = 88\n")

        assert check_formatter_config(tmp_path) is None

    def test_resolve_error_returns_message(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """resolve_steps ValueError → its message."""
        monkeypatch.setattr(
            "mcp_coder.workflow_steps.commit.resolve_steps", _raise_value_error
        )

        assert check_formatter_config(tmp_path) == "No formatter declared"

    def test_non_bool_format_code_returns_message(self, tmp_path: Path) -> None:
        """Non-bool format_code → error message naming the key."""
        _write_pyproject(tmp_path, '[tool.mcp-coder]\nformat_code = "false"\n')

        message = check_formatter_config(tmp_path)

        assert message is not None
        assert "format_code" in message

    def test_legacy_warning_only_when_requested(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Legacy key warning is logged only with warn_legacy_key=True."""
        _write_pyproject(tmp_path, "[tool.mcp-coder.implement]\nformat_code = true\n")

        with caplog.at_level(logging.WARNING):
            check_formatter_config(tmp_path)
        assert LEGACY_WARNING not in caplog.text

        with caplog.at_level(logging.WARNING):
            check_formatter_config(tmp_path, warn_legacy_key=True)
        assert LEGACY_WARNING in caplog.text

    def test_legacy_warning_when_formatting_disabled(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Legacy key warning is logged even when format_code = false."""
        _write_pyproject(
            tmp_path,
            "[tool.mcp-coder]\nformat_code = false\n\n"
            "[tool.mcp-coder.implement]\nformat_code = true\n",
        )

        with caplog.at_level(logging.WARNING):
            assert check_formatter_config(tmp_path, warn_legacy_key=True) is None
        assert LEGACY_WARNING in caplog.text


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
        """A generic exception from run_format_code is not a config error → False."""
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
        mock_generate_message.assert_called_once_with(
            Path("/test/project"),
            "claude",
            mcp_config=None,
            settings_file=None,
        )
        mock_commit.assert_called_once_with(
            "feat: add new feature", Path("/test/project")
        )

    @patch("mcp_coder.workflow_steps.commit.commit_all_changes")
    @patch("mcp_coder.workflow_steps.commit.generate_commit_message_with_llm")
    def test_commit_changes_forwards_session_params(
        self, mock_generate_message: MagicMock, mock_commit: MagicMock
    ) -> None:
        """Test commit_changes forwards session params to message generation."""
        mock_generate_message.return_value = (True, "feat: add new feature", None)
        mock_commit.return_value = {
            "success": True,
            "commit_hash": "abc123",
            "error": None,
        }

        result = commit_changes(
            Path("/test/project"),
            "claude",
            mcp_config="cfg.json",
            settings_file="s.json",
        )

        assert result is True
        mock_generate_message.assert_called_once_with(
            Path("/test/project"),
            "claude",
            mcp_config="cfg.json",
            settings_file="s.json",
        )

    @patch("mcp_coder.workflow_steps.commit.commit_all_changes")
    @patch("mcp_coder.workflow_steps.commit.generate_commit_message_with_llm")
    def test_commit_changes_uses_fallback_when_generation_fails(
        self,
        mock_generate_message: MagicMock,
        mock_commit: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test fallback commit message is used when LLM generation fails."""
        mock_generate_message.return_value = (False, "", "boom")
        mock_commit.return_value = {
            "success": True,
            "commit_hash": "abc123",
            "error": None,
        }

        result = commit_changes(Path("/test/project"))

        assert result is True
        mock_generate_message.assert_called_once_with(
            Path("/test/project"),
            "claude",
            mcp_config=None,
            settings_file=None,
        )
        mock_commit.assert_called_once_with(
            FALLBACK_COMMIT_MESSAGE, Path("/test/project")
        )
        # Error is logged; git history gets only the static message
        assert "boom" in caplog.text

    @patch("mcp_coder.workflow_steps.commit.commit_all_changes")
    @patch("mcp_coder.workflow_steps.commit.generate_commit_message_with_llm")
    def test_commit_changes_clean_tree_flows_through_fallback(
        self, mock_generate_message: MagicMock, mock_commit: MagicMock
    ) -> None:
        """Test clean tree: generation fails, commit no-ops with success."""
        mock_generate_message.return_value = (False, "", "No changes to commit")
        # Clean tree: commit_all_changes no-ops and reports success
        mock_commit.return_value = {
            "success": True,
            "commit_hash": None,
            "error": None,
        }

        result = commit_changes(Path("/test/project"))

        assert result is True
        mock_commit.assert_called_once_with(
            FALLBACK_COMMIT_MESSAGE, Path("/test/project")
        )

    @patch("mcp_coder.workflow_steps.commit.commit_all_changes")
    @patch("mcp_coder.workflow_steps.commit.generate_commit_message_with_llm")
    def test_commit_changes_fallback_commit_failure_returns_false(
        self, mock_generate_message: MagicMock, mock_commit: MagicMock
    ) -> None:
        """Test git-level failure still returns False after fallback message."""
        mock_generate_message.return_value = (False, "", "boom")
        mock_commit.return_value = {
            "success": False,
            "commit_hash": None,
            "error": "Git commit failed",
        }

        result = commit_changes(Path("/test/project"))

        assert result is False

    @patch("mcp_coder.workflow_steps.commit.commit_all_changes")
    @patch("mcp_coder.workflow_steps.commit.generate_commit_message_with_llm")
    def test_commit_changes_no_fallback_when_generation_succeeds(
        self, mock_generate_message: MagicMock, mock_commit: MagicMock
    ) -> None:
        """Test LLM message is used, not the fallback, when generation succeeds."""
        mock_generate_message.return_value = (True, "feat: llm message", None)
        mock_commit.return_value = {
            "success": True,
            "commit_hash": "abc123",
            "error": None,
        }

        result = commit_changes(Path("/test/project"))

        assert result is True
        mock_commit.assert_called_once_with("feat: llm message", Path("/test/project"))

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
