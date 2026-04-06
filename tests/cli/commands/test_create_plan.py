"""Tests for create-plan CLI command handler."""

from pathlib import Path
from unittest import mock
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.cli.commands.create_plan import execute_create_plan


class TestExecuteCreatePlan:
    """Test execute_create_plan CLI command handler."""

    @pytest.fixture
    def mock_args(self) -> MagicMock:
        """Create mock command line arguments."""
        args = MagicMock()
        args.issue_number = 123
        args.project_dir = "/test/project"
        args.llm_method = "claude"
        args.mcp_config = None  # Set to None instead of leaving as MagicMock
        args.execution_dir = None  # Add execution_dir attribute
        args.update_issue_labels = None  # Add update_issue_labels attribute
        args.post_issue_comments = None  # Add post_issue_comments attribute
        return args

    @patch("mcp_coder.workflows.create_plan.run_create_plan_workflow")
    @patch("mcp_coder.cli.commands.create_plan.resolve_issue_interaction_flags")
    @patch("mcp_coder.cli.commands.create_plan.parse_llm_method_from_args")
    @patch("mcp_coder.cli.commands.create_plan.resolve_llm_method")
    @patch("mcp_coder.cli.commands.create_plan.resolve_execution_dir")
    @patch("mcp_coder.cli.commands.create_plan.resolve_project_dir")
    def test_execute_create_plan_success(
        self,
        mock_resolve: MagicMock,
        mock_resolve_exec: MagicMock,
        mock_resolve_llm: MagicMock,
        mock_parse: MagicMock,
        mock_resolve_flags: MagicMock,
        mock_workflow: MagicMock,
        mock_args: MagicMock,
    ) -> None:
        """Test successful create-plan command execution."""
        test_project_dir = Path("/test/project")
        test_execution_dir = str(Path.cwd())

        # Configure mocks
        mock_resolve.return_value = test_project_dir
        mock_resolve_exec.return_value = test_execution_dir
        mock_resolve_llm.return_value = ("claude", "cli argument")
        mock_parse.return_value = "claude"
        mock_resolve_flags.return_value = (False, False)
        mock_workflow.return_value = 0

        # Execute
        result = execute_create_plan(mock_args)

        # Assert
        assert result == 0
        mock_resolve.assert_called_once_with("/test/project")
        mock_resolve_exec.assert_called_once_with(None)
        mock_parse.assert_called_once_with("claude")
        mock_resolve_flags.assert_called_once_with(mock_args, test_project_dir)
        mock_workflow.assert_called_once_with(
            123,
            test_project_dir,
            "claude",
            mock_args.mcp_config,
            test_execution_dir,
            False,
            False,
        )

    @patch("mcp_coder.workflows.create_plan.run_create_plan_workflow", return_value=1)
    @patch(
        "mcp_coder.cli.commands.create_plan.resolve_issue_interaction_flags",
        return_value=(False, False),
    )
    @patch(
        "mcp_coder.cli.commands.create_plan.parse_llm_method_from_args",
        return_value="claude",
    )
    @patch(
        "mcp_coder.cli.commands.create_plan.resolve_llm_method",
        return_value=("claude", "cli argument"),
    )
    @patch("mcp_coder.cli.commands.create_plan.resolve_execution_dir")
    @patch("mcp_coder.cli.commands.create_plan.resolve_project_dir")
    def test_execute_create_plan_error_handling(
        self,
        mock_resolve: MagicMock,
        mock_resolve_exec: MagicMock,
        mock_resolve_llm: MagicMock,
        mock_parse: MagicMock,
        mock_resolve_flags: MagicMock,
        mock_workflow: MagicMock,
        mock_args: MagicMock,
    ) -> None:
        """Test error handling for workflow failures and exceptions."""
        test_project_dir = Path("/test/project")
        test_execution_dir = str(Path.cwd())

        mock_resolve.return_value = test_project_dir
        mock_resolve_exec.return_value = test_execution_dir

        result = execute_create_plan(mock_args)
        assert result == 1


class TestCreatePlanExecutionDir:
    """Tests for execution_dir handling in create-plan command."""

    @patch("mcp_coder.cli.commands.create_plan.resolve_issue_interaction_flags")
    @patch("mcp_coder.cli.commands.create_plan.resolve_execution_dir")
    @patch("mcp_coder.cli.commands.create_plan.resolve_project_dir")
    @patch("mcp_coder.workflows.create_plan.run_create_plan_workflow")
    @patch("mcp_coder.cli.commands.create_plan.resolve_llm_method")
    @patch("mcp_coder.cli.commands.create_plan.parse_llm_method_from_args")
    def test_default_execution_dir_uses_cwd(
        self,
        mock_parse_llm: MagicMock,
        mock_resolve_llm: MagicMock,
        mock_run_workflow: MagicMock,
        mock_resolve_project: MagicMock,
        mock_resolve_exec: MagicMock,
        mock_resolve_flags: MagicMock,
    ) -> None:
        """Test default execution_dir should use current working directory."""
        project_dir = Path("/test/project")
        execution_dir = Path.cwd()
        mock_resolve_project.return_value = project_dir
        mock_resolve_exec.return_value = str(execution_dir)
        mock_resolve_llm.return_value = ("claude", "cli argument")
        mock_parse_llm.return_value = "claude"
        mock_resolve_flags.return_value = (False, False)
        mock_run_workflow.return_value = 0

        args = MagicMock()
        args.issue_number = 123
        args.project_dir = "/test/project"
        args.execution_dir = None  # No explicit execution_dir
        args.llm_method = "claude"
        args.mcp_config = None
        args.update_issue_labels = None
        args.post_issue_comments = None

        result = execute_create_plan(args)

        assert result == 0
        mock_resolve_exec.assert_called_once_with(None)
        mock_run_workflow.assert_called_once_with(
            123, project_dir, "claude", None, str(execution_dir), False, False
        )

    @patch("mcp_coder.cli.commands.create_plan.resolve_issue_interaction_flags")
    @patch("mcp_coder.cli.commands.create_plan.resolve_execution_dir")
    @patch("mcp_coder.cli.commands.create_plan.resolve_project_dir")
    @patch("mcp_coder.workflows.create_plan.run_create_plan_workflow")
    @patch("mcp_coder.cli.commands.create_plan.resolve_llm_method")
    @patch("mcp_coder.cli.commands.create_plan.parse_llm_method_from_args")
    def test_explicit_execution_dir_absolute(
        self,
        mock_parse_llm: MagicMock,
        mock_resolve_llm: MagicMock,
        mock_run_workflow: MagicMock,
        mock_resolve_project: MagicMock,
        mock_resolve_exec: MagicMock,
        mock_resolve_flags: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test explicit absolute execution_dir should be validated and used."""
        project_dir = Path("/test/project")
        execution_dir = tmp_path / "exec_dir"
        execution_dir.mkdir()

        mock_resolve_project.return_value = project_dir
        mock_resolve_exec.return_value = str(execution_dir)
        mock_resolve_llm.return_value = ("claude", "cli argument")
        mock_parse_llm.return_value = "claude"
        mock_resolve_flags.return_value = (False, False)
        mock_run_workflow.return_value = 0

        args = MagicMock()
        args.issue_number = 123
        args.project_dir = "/test/project"
        args.execution_dir = str(execution_dir)
        args.llm_method = "claude"
        args.mcp_config = None
        args.update_issue_labels = None
        args.post_issue_comments = None

        result = execute_create_plan(args)

        assert result == 0
        mock_resolve_exec.assert_called_once_with(str(execution_dir))
        mock_run_workflow.assert_called_once_with(
            123, project_dir, "claude", None, str(execution_dir), False, False
        )

    @patch("mcp_coder.cli.commands.create_plan.resolve_execution_dir")
    @patch("mcp_coder.cli.commands.create_plan.resolve_project_dir")
    def test_invalid_execution_dir_returns_error(
        self,
        mock_resolve_project: MagicMock,
        mock_resolve_exec: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test invalid execution_dir should return error code 1."""
        import logging

        project_dir = Path("/test/project")
        mock_resolve_project.return_value = project_dir
        mock_resolve_exec.side_effect = ValueError("Directory does not exist")

        args = MagicMock()
        args.issue_number = 123
        args.project_dir = "/test/project"
        args.execution_dir = "/nonexistent/invalid/path"
        args.llm_method = "claude"
        args.mcp_config = None

        with caplog.at_level(logging.DEBUG):
            result = execute_create_plan(args)

        assert result == 1
        assert "Directory does not exist" in caplog.text
