"""Tests for create-plan CLI command handler."""

from pathlib import Path
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
        args.llm_method = "claude_code_cli"
        return args

    def test_execute_create_plan_success(self, mock_args: MagicMock) -> None:
        """Test successful create-plan command execution."""
        test_project_dir = Path("/test/project")

        with patch(
            "mcp_coder.cli.commands.create_plan.resolve_project_dir"
        ) as mock_resolve:
            with patch(
                "mcp_coder.cli.commands.create_plan.parse_llm_method_from_args"
            ) as mock_parse:
                with patch(
                    "mcp_coder.workflows.create_plan.run_create_plan_workflow"
                ) as mock_workflow:
                    # Configure mocks
                    mock_resolve.return_value = test_project_dir
                    mock_parse.return_value = ("claude", "cli")
                    mock_workflow.return_value = 0

                    # Execute
                    result = execute_create_plan(mock_args)

                    # Assert
                    assert result == 0
                    mock_resolve.assert_called_once_with("/test/project")
                    mock_parse.assert_called_once_with("claude_code_cli")
                    mock_workflow.assert_called_once_with(
                        123, test_project_dir, "claude", "cli", mock_args.mcp_config
                    )

    def test_execute_create_plan_error_handling(self, mock_args: MagicMock) -> None:
        """Test error handling for workflow failures and exceptions."""
        test_project_dir = Path("/test/project")

        # Test workflow failure (returns error code)
        with patch(
            "mcp_coder.cli.commands.create_plan.resolve_project_dir",
            return_value=test_project_dir,
        ):
            with patch(
                "mcp_coder.cli.commands.create_plan.parse_llm_method_from_args",
                return_value=("claude", "cli"),
            ):
                with patch(
                    "mcp_coder.workflows.create_plan.run_create_plan_workflow",
                    return_value=1,
                ):
                    result = execute_create_plan(mock_args)
                    assert result == 1

        # Test exception handling
        with patch(
            "mcp_coder.cli.commands.create_plan.resolve_project_dir",
            side_effect=RuntimeError("Test error"),
        ):
            result = execute_create_plan(mock_args)
            assert result == 1

        # Test keyboard interrupt
        with patch(
            "mcp_coder.cli.commands.create_plan.resolve_project_dir",
            return_value=test_project_dir,
        ):
            with patch(
                "mcp_coder.cli.commands.create_plan.parse_llm_method_from_args",
                return_value=("claude", "cli"),
            ):
                with patch(
                    "mcp_coder.workflows.create_plan.run_create_plan_workflow",
                    side_effect=KeyboardInterrupt(),
                ):
                    result = execute_create_plan(mock_args)
                    assert result == 1
