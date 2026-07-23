"""Tests for the rebase CLI command handler and parser wiring."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from mcp_coder.cli.commands.rebase import _resolve_rebase_settings, execute_rebase
from mcp_coder.cli.main import create_parser
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

    def test_default_materializes_temp_permissions_file(self) -> None:
        """With no explicit --settings, write a temp JSON file matching the constant."""
        path = _resolve_rebase_settings(None, None)

        settings_path = Path(path)
        assert settings_path.exists()
        assert settings_path.suffix == ".json"

        with settings_path.open(encoding="utf-8") as handle:
            contents = json.load(handle)
        assert contents == REBASE_LLM_PERMISSIONS

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
        args.execution_dir = None
        args.llm_method = "claude"
        args.mcp_config = None
        args.settings = None
        args.base_branch = "main"
        return args

    @patch("mcp_coder.workflows.rebase.run_rebase_workflow", return_value=2)
    @patch("mcp_coder.cli.commands.rebase._resolve_rebase_settings")
    @patch("mcp_coder.cli.commands.rebase.resolve_mcp_config_path")
    @patch("mcp_coder.cli.commands.rebase.parse_llm_method_from_args")
    @patch("mcp_coder.cli.commands.rebase.resolve_llm_method")
    @patch("mcp_coder.cli.commands.rebase.resolve_execution_dir")
    @patch("mcp_coder.cli.commands.rebase.resolve_project_dir")
    def test_execute_rebase_passes_args_and_returns_exit_code(
        self,
        mock_project: MagicMock,
        mock_exec: MagicMock,
        mock_resolve_llm: MagicMock,
        mock_parse_llm: MagicMock,
        mock_mcp: MagicMock,
        mock_settings: MagicMock,
        mock_workflow: MagicMock,
    ) -> None:
        """execute_rebase wires resolved args into run_rebase_workflow."""
        project_dir = Path("/test/project")
        execution_dir = Path("/exec/dir")
        mock_project.return_value = project_dir
        mock_exec.return_value = execution_dir
        mock_resolve_llm.return_value = ("claude", "cli argument")
        mock_parse_llm.return_value = "claude"
        mock_mcp.return_value = None
        mock_settings.return_value = "/tmp/rebase-settings.json"

        result = execute_rebase(self._make_args())

        assert result == 2
        mock_workflow.assert_called_once_with(
            project_dir,
            "claude",
            "main",
            None,
            "/tmp/rebase-settings.json",
            execution_dir,
        )

    @patch("mcp_coder.cli.commands.rebase.resolve_execution_dir")
    @patch("mcp_coder.cli.commands.rebase.resolve_project_dir")
    def test_invalid_execution_dir_returns_two(
        self,
        mock_project: MagicMock,
        mock_exec: MagicMock,
    ) -> None:
        """A ValueError from directory resolution returns exit code 2 (error)."""
        mock_project.return_value = Path("/test/project")
        mock_exec.side_effect = ValueError("Directory does not exist")

        result = execute_rebase(self._make_args())

        assert result == 2

    @patch("mcp_coder.cli.commands.rebase.resolve_execution_dir")
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
