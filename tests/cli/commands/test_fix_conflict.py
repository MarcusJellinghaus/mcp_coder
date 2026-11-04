"""Tests for the fix-conflict CLI command handler."""

import logging
from collections.abc import Iterator
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.cli.commands.fix_conflict import execute_fix_conflict

_CLI = "mcp_coder.cli.commands.fix_conflict"


def _make_args() -> MagicMock:
    args = MagicMock()
    args.project_dir = "/test/project"
    args.llm_method = None
    args.mcp_config = None
    args.settings = None
    return args


@pytest.fixture(autouse=True, name="mock_auto_merge")
def fixture_mock_auto_merge() -> Iterator[MagicMock]:
    """Resolve auto_merge to False without reading git or config."""
    with patch(
        "mcp_coder.cli.commands.fix_conflict.resolve_auto_merge", return_value=False
    ) as mock_resolve:
        yield mock_resolve


@pytest.fixture(autouse=True)
def _llm_resolvers() -> Iterator[MagicMock]:
    """Stub LLM method / MCP config resolution; yields the mcp-config mock."""
    with (
        patch(f"{_CLI}.resolve_llm_method", return_value=("claude", "default")),
        patch(f"{_CLI}.parse_llm_method_from_args", return_value="claude"),
        patch(
            f"{_CLI}.resolve_mcp_config_path", return_value="/abs/.mcp.json"
        ) as mock_mcp,
    ):
        yield mock_mcp


class TestExecuteFixConflict:
    """Tests for execute_fix_conflict."""

    @patch("mcp_coder.workflows.fix_conflict.core.run_fix_conflict_workflow")
    @patch(f"{_CLI}.enable_crash_logging")
    @patch(f"{_CLI}.log_command_startup")
    @patch(f"{_CLI}.resolve_project_dir")
    def test_no_settings_passes_none_without_auto_detect(
        self,
        mock_resolve_dir: MagicMock,
        _mock_log_startup: MagicMock,
        _mock_crash_logging: MagicMock,
        mock_workflow: MagicMock,
        tmp_path: Path,
        _llm_resolvers: MagicMock,
    ) -> None:
        """Without --settings, None is passed even if settings.local.json exists."""
        (tmp_path / ".claude").mkdir()
        (tmp_path / ".claude" / "settings.local.json").write_text("{}")
        mock_resolve_dir.return_value = tmp_path
        mock_workflow.return_value = 0
        args = _make_args()
        args.project_dir = str(tmp_path)
        args.mcp_config = ".mcp.json"

        result = execute_fix_conflict(args)

        assert result == 0
        _llm_resolvers.assert_called_once_with(".mcp.json", project_dir=str(tmp_path))
        mock_workflow.assert_called_once_with(
            tmp_path, "claude", "/abs/.mcp.json", None, auto_merge=False
        )

    @patch("mcp_coder.workflows.fix_conflict.core.run_fix_conflict_workflow")
    @patch(f"{_CLI}.resolve_claude_settings_path", return_value="/abs/x.json")
    @patch(f"{_CLI}.enable_crash_logging")
    @patch(f"{_CLI}.log_command_startup")
    @patch(f"{_CLI}.resolve_project_dir")
    def test_explicit_settings_are_resolved_and_passed(
        self,
        mock_resolve_dir: MagicMock,
        _mock_log_startup: MagicMock,
        _mock_crash_logging: MagicMock,
        mock_settings: MagicMock,
        mock_workflow: MagicMock,
    ) -> None:
        """An explicit --settings path is resolved and passed to the workflow."""
        project_dir = Path("/test/project")
        mock_resolve_dir.return_value = project_dir
        mock_workflow.return_value = 0
        args = _make_args()
        args.settings = "x.json"

        result = execute_fix_conflict(args)

        assert result == 0
        mock_settings.assert_called_once_with("x.json", project_dir="/test/project")
        mock_workflow.assert_called_once_with(
            project_dir, "claude", "/abs/.mcp.json", "/abs/x.json", auto_merge=False
        )

    @pytest.mark.parametrize("auto_merge", [True, False])
    @patch("mcp_coder.workflows.fix_conflict.core.run_fix_conflict_workflow")
    @patch("mcp_coder.cli.commands.fix_conflict.enable_crash_logging")
    @patch("mcp_coder.cli.commands.fix_conflict.log_command_startup")
    @patch("mcp_coder.cli.commands.fix_conflict.resolve_project_dir")
    def test_success_path(
        self,
        mock_resolve_dir: MagicMock,
        mock_log_startup: MagicMock,
        mock_crash_logging: MagicMock,
        mock_workflow: MagicMock,
        auto_merge: bool,
        mock_auto_merge: MagicMock,
    ) -> None:
        """Resolves project dir and auto_merge, returns the workflow's exit code."""
        project_dir = Path("/test/project")
        mock_resolve_dir.return_value = project_dir
        mock_workflow.return_value = 0
        mock_auto_merge.return_value = auto_merge
        args = _make_args()

        result = execute_fix_conflict(args)

        assert result == 0
        mock_resolve_dir.assert_called_once_with("/test/project")
        mock_log_startup.assert_called_once_with("fix-conflict", project_dir)
        mock_crash_logging.assert_called_once_with(project_dir, "fix-conflict")
        mock_auto_merge.assert_called_once_with(args, project_dir)
        mock_workflow.assert_called_once_with(
            project_dir, "claude", "/abs/.mcp.json", None, auto_merge=auto_merge
        )

    @patch("mcp_coder.workflows.fix_conflict.core.run_fix_conflict_workflow")
    @patch("mcp_coder.cli.commands.fix_conflict.enable_crash_logging")
    @patch("mcp_coder.cli.commands.fix_conflict.log_command_startup")
    @patch("mcp_coder.cli.commands.fix_conflict.resolve_project_dir")
    def test_workflow_failure_returns_one(
        self,
        mock_resolve_dir: MagicMock,
        mock_log_startup: MagicMock,
        mock_crash_logging: MagicMock,
        mock_workflow: MagicMock,
    ) -> None:
        """A non-zero workflow result is passed through."""
        project_dir = Path("/test/project")
        mock_resolve_dir.return_value = project_dir
        mock_workflow.return_value = 1

        result = execute_fix_conflict(_make_args())

        assert result == 1

    @patch("mcp_coder.cli.commands.fix_conflict.resolve_project_dir")
    def test_invalid_project_dir_returns_one(
        self,
        mock_resolve_dir: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """A ValueError from directory resolution returns exit code 1."""
        mock_resolve_dir.side_effect = ValueError("Directory does not exist")

        with caplog.at_level(logging.DEBUG):
            result = execute_fix_conflict(_make_args())

        assert result == 1
        assert "Directory does not exist" in caplog.text

    @patch("mcp_coder.workflows.fix_conflict.core.run_fix_conflict_workflow")
    @patch("mcp_coder.cli.commands.fix_conflict.enable_crash_logging")
    @patch("mcp_coder.cli.commands.fix_conflict.log_command_startup")
    @patch("mcp_coder.cli.commands.fix_conflict.resolve_project_dir")
    def test_keyboard_interrupt_returns_one(
        self,
        mock_resolve_dir: MagicMock,
        mock_log_startup: MagicMock,
        mock_crash_logging: MagicMock,
        mock_workflow: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """KeyboardInterrupt is handled gracefully and returns 1."""
        mock_resolve_dir.return_value = Path("/test/project")
        mock_workflow.side_effect = KeyboardInterrupt()

        with caplog.at_level(logging.DEBUG):
            result = execute_fix_conflict(_make_args())

        assert result == 1
        assert "Operation cancelled by user." in caplog.text

    @patch("mcp_coder.workflows.fix_conflict.core.run_fix_conflict_workflow")
    @patch("mcp_coder.cli.commands.fix_conflict.enable_crash_logging")
    @patch("mcp_coder.cli.commands.fix_conflict.log_command_startup")
    @patch("mcp_coder.cli.commands.fix_conflict.resolve_project_dir")
    def test_unexpected_exception_returns_one(
        self,
        mock_resolve_dir: MagicMock,
        mock_log_startup: MagicMock,
        mock_crash_logging: MagicMock,
        mock_workflow: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """An unexpected exception is logged with exc_info and returns 1."""
        mock_resolve_dir.return_value = Path("/test/project")
        mock_workflow.side_effect = RuntimeError("boom")

        with caplog.at_level(logging.DEBUG):
            result = execute_fix_conflict(_make_args())

        assert result == 1
        assert "boom" in caplog.text


class TestFixConflictCliIntegration:
    """Smoke tests for CLI parser registration."""

    def test_fix_conflict_command_registered(self) -> None:
        """fix-conflict command is registered in the CLI parser."""
        from mcp_coder.cli.main import create_parser

        parser = create_parser()
        args = parser.parse_args(["fix-conflict"])

        assert args.command == "fix-conflict"

    def test_fix_conflict_command_accepts_llm_args(self) -> None:
        """fix-conflict accepts --llm-method, --mcp-config and --settings."""
        from mcp_coder.cli.main import create_parser

        parser = create_parser()
        args = parser.parse_args(
            [
                "fix-conflict",
                "--llm-method",
                "claude",
                "--mcp-config",
                ".mcp.json",
                "--settings",
                "s.json",
            ]
        )

        assert args.project_dir is None
        assert args.llm_method == "claude"
        assert args.mcp_config == ".mcp.json"
        assert args.settings == "s.json"
