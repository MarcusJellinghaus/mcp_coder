"""Tests for the rebase CLI command handler and parser wiring."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from mcp_coder.cli.commands.rebase import _resolve_rebase_settings, execute_rebase
from mcp_coder.cli.main import create_parser
from mcp_coder.workflows.rebase import RebaseRunResult
from mcp_coder.workflows.rebase_permissions import REBASE_LLM_PERMISSIONS


class TestRebaseParser:
    """Test the rebase subparser wiring."""

    def test_base_branch_flag(self) -> None:
        """--base-branch is parsed onto command == 'rebase'."""
        args = create_parser().parse_args(["rebase", "--base-branch", "main"])
        assert args.command == "rebase"
        assert args.base_branch == "main"

    def test_base_branch_defaults_to_none(self) -> None:
        """base_branch defaults to None when not supplied."""
        args = create_parser().parse_args(["rebase"])
        assert args.command == "rebase"
        assert args.base_branch is None


class TestResolveRebaseSettings:
    """Test _resolve_rebase_settings."""

    def test_default_returns_none(self) -> None:
        """With no explicit --settings, defer to rebase_settings_file's default."""
        assert _resolve_rebase_settings(None, None) is None

    def test_explicit_settings_delegates_to_resolver(self) -> None:
        """An explicit --settings path delegates to resolve_claude_settings_path."""
        with patch(
            "mcp_coder.cli.commands.rebase.resolve_claude_settings_path",
            return_value="/resolved/settings.json",
        ) as mock_resolve:
            result = _resolve_rebase_settings("x.json", "/test/project")

        assert result == "/resolved/settings.json"
        mock_resolve.assert_called_once_with("x.json", project_dir="/test/project")


class TestExecuteRebase:
    """Test execute_rebase CLI command handler."""

    def _make_args(self) -> MagicMock:
        args = MagicMock()
        args.project_dir = "/test/project"
        args.llm_method = "claude"
        args.mcp_config = None
        args.settings = None
        args.base_branch = "main"
        return args

    @patch(
        "mcp_coder.workflows.rebase.run_rebase_workflow",
        return_value=RebaseRunResult(2, "force-push rejected", push_rejected=True),
    )
    @patch("mcp_coder.cli.commands.rebase.resolve_mcp_config_path")
    @patch("mcp_coder.cli.commands.rebase.parse_llm_method_from_args")
    @patch("mcp_coder.cli.commands.rebase.resolve_llm_method")
    @patch("mcp_coder.cli.commands.rebase.resolve_claude_cwd")
    @patch("mcp_coder.cli.commands.rebase.resolve_project_dir")
    def test_execute_rebase_passes_args_and_returns_exit_code(
        self,
        mock_project: MagicMock,
        mock_exec: MagicMock,
        mock_resolve_llm: MagicMock,
        mock_parse_llm: MagicMock,
        mock_mcp: MagicMock,
        mock_workflow: MagicMock,
    ) -> None:
        """Without --settings the workflow gets a temp file removed afterwards."""
        project_dir = Path("/test/project")
        mock_project.return_value = project_dir
        mock_exec.return_value = project_dir
        mock_resolve_llm.return_value = ("claude", "cli argument")
        mock_parse_llm.return_value = "claude"
        mock_mcp.return_value = None
        seen: dict[str, object] = {}

        def _capture(*args: object) -> RebaseRunResult:
            settings_path = Path(str(args[4]))
            seen["path"] = settings_path
            with settings_path.open(encoding="utf-8") as handle:
                seen["contents"] = json.load(handle)
            return RebaseRunResult(2, "force-push rejected", push_rejected=True)

        mock_workflow.side_effect = _capture

        result = execute_rebase(self._make_args())

        assert result == 2
        mock_workflow.assert_called_once()
        call_args = mock_workflow.call_args.args
        assert call_args[:4] == (project_dir, "claude", "main", None)
        assert seen["contents"] == REBASE_LLM_PERMISSIONS
        settings_path = seen["path"]
        assert isinstance(settings_path, Path)
        assert not settings_path.exists()

    @patch(
        "mcp_coder.workflows.rebase.run_rebase_workflow",
        return_value=RebaseRunResult(0, "success"),
    )
    @patch(
        "mcp_coder.cli.commands.rebase.resolve_claude_settings_path",
        return_value="/resolved/settings.json",
    )
    @patch("mcp_coder.cli.commands.rebase.resolve_mcp_config_path")
    @patch("mcp_coder.cli.commands.rebase.parse_llm_method_from_args")
    @patch("mcp_coder.cli.commands.rebase.resolve_llm_method")
    @patch("mcp_coder.cli.commands.rebase.resolve_claude_cwd")
    @patch("mcp_coder.cli.commands.rebase.resolve_project_dir")
    def test_explicit_settings_passed_through(
        self,
        mock_project: MagicMock,
        mock_exec: MagicMock,
        mock_resolve_llm: MagicMock,
        mock_parse_llm: MagicMock,
        mock_mcp: MagicMock,
        mock_resolve_settings: MagicMock,
        mock_workflow: MagicMock,
    ) -> None:
        """With --settings the resolved path is handed to the workflow as-is."""
        project_dir = Path("/test/project")
        mock_project.return_value = project_dir
        mock_exec.return_value = project_dir
        mock_resolve_llm.return_value = ("claude", "cli argument")
        mock_parse_llm.return_value = "claude"
        mock_mcp.return_value = None
        args = self._make_args()
        args.settings = "x.json"

        result = execute_rebase(args)

        assert result == 0
        mock_resolve_settings.assert_called_once_with(
            "x.json", project_dir="/test/project"
        )
        mock_workflow.assert_called_once_with(
            project_dir, "claude", "main", None, "/resolved/settings.json"
        )

    @patch("mcp_coder.cli.commands.rebase.resolve_project_dir")
    def test_invalid_project_dir_returns_two(
        self,
        mock_project: MagicMock,
    ) -> None:
        """A ValueError from directory resolution returns exit code 2 (error)."""
        mock_project.side_effect = ValueError("Directory does not exist")

        result = execute_rebase(self._make_args())

        assert result == 2

    @patch("mcp_coder.cli.commands.rebase.resolve_claude_cwd")
    @patch("mcp_coder.cli.commands.rebase.resolve_project_dir")
    def test_unexpected_exception_boundary_returns_two(
        self,
        mock_project: MagicMock,
        mock_exec: MagicMock,
    ) -> None:
        """The top-level exception boundary returns exit code 2 (error)."""
        mock_project.return_value = Path("/test/project")
        mock_exec.side_effect = RuntimeError("unexpected crash")

        result = execute_rebase(self._make_args())

        assert result == 2
