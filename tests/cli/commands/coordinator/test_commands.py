"""Tests for coordinator commands.py functions.

This module contains tests for:
- Job output formatting (format_job_output)
- Coordinator test execution (execute_coordinator_test)
- Coordinator run execution (execute_coordinator_run)
"""

import argparse
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.cli.commands.coordinator import (
    CREATE_PLAN_COMMAND_TEMPLATE,
    CREATE_PLAN_COMMAND_WINDOWS,
    CREATE_PR_COMMAND_TEMPLATE,
    CREATE_PR_COMMAND_WINDOWS,
    DEFAULT_TEST_COMMAND,
    DEFAULT_TEST_COMMAND_WINDOWS,
    IMPLEMENT_COMMAND_TEMPLATE,
    IMPLEMENT_COMMAND_WINDOWS,
    execute_coordinator_run,
    execute_coordinator_test,
    format_job_output,
)
from mcp_coder.utils.github_operations.issue_manager import IssueData
from mcp_coder.utils.jenkins_operations.models import JobStatus


class TestFormatJobOutput:
    """Tests for format_job_output function."""

    def test_format_job_output_with_url(self) -> None:
        """Test formatting output when job URL is available."""
        # Execute
        result = format_job_output(
            "MCP_Coder/test-job",
            12345,
            "https://jenkins.example.com/job/MCP_Coder/job/test-job/42/",
        )

        # Verify
        assert "Job triggered: MCP_Coder/test-job - test - queue: 12345" in result
        assert "https://jenkins.example.com/job/MCP_Coder/job/test-job/42/" in result

    def test_format_job_output_without_url(self) -> None:
        """Test formatting output when job URL is not yet available."""
        # Execute
        result = format_job_output("MCP_Coder/test-job", 12345, None)

        # Verify
        assert "Job triggered: MCP_Coder/test-job - test - queue: 12345" in result
        assert "will be available once build starts" in result


class TestExecuteCoordinatorTest:
    """Tests for execute_coordinator_test command function."""

    @patch("mcp_coder.cli.commands.coordinator.commands.JenkinsClient")
    @patch("mcp_coder.cli.commands.coordinator.commands.get_jenkins_credentials")
    @patch("mcp_coder.cli.commands.coordinator.commands.load_repo_config")
    @patch("mcp_coder.cli.commands.coordinator.commands.create_default_config")
    def test_execute_coordinator_test_success(
        self,
        mock_create_config: MagicMock,
        mock_load_repo: MagicMock,
        mock_get_creds: MagicMock,
        mock_jenkins_class: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test successful command execution."""
        # Setup
        args = argparse.Namespace(
            repo_name="mcp_coder", branch_name="feature-x", log_level="DEBUG"
        )

        # Config already exists
        mock_create_config.return_value = False

        # Repo config is valid
        mock_load_repo.return_value = {
            "repo_url": "https://github.com/user/repo.git",
            "executor_job_path": "MCP/test-job",
            "github_credentials_id": "github-pat",
            "executor_os": "linux",
        }

        # Jenkins credentials available
        mock_get_creds.return_value = ("http://jenkins:8080", "user", "token")

        # Mock Jenkins client
        mock_client = MagicMock()
        mock_jenkins_class.return_value = mock_client
        mock_client.start_job.return_value = 12345

        # Mock job status with URL
        mock_client.get_job_status.return_value = JobStatus(
            status="queued",
            build_number=None,
            duration_ms=None,
            url="https://jenkins:8080/queue/item/12345/",
        )

        # Execute
        result = execute_coordinator_test(args)

        # Verify
        assert result == 0

        # Verify JenkinsClient created with credentials
        mock_jenkins_class.assert_called_once_with(
            "http://jenkins:8080", "user", "token"
        )

        # Verify job started with correct params
        mock_client.start_job.assert_called_once_with(
            "MCP/test-job",
            {
                "REPO_URL": "https://github.com/user/repo.git",
                "BRANCH_NAME": "feature-x",
                "COMMAND": DEFAULT_TEST_COMMAND.format(log_level="DEBUG"),
                "GITHUB_CREDENTIALS_ID": "github-pat",
            },
        )

        # Verify output printed
        captured = capsys.readouterr()
        assert "Job triggered: MCP/test-job - test - queue: 12345" in captured.out
        assert "https://jenkins:8080/queue/item/12345/" in captured.out


class TestExecuteCoordinatorRun:
    """Tests for execute_coordinator_run function."""

    @patch("mcp_coder.cli.commands.coordinator.commands.IssueManager")
    @patch("mcp_coder.cli.commands.coordinator.commands.IssueBranchManager")
    @patch("mcp_coder.cli.commands.coordinator.commands.JenkinsClient")
    @patch("mcp_coder.cli.commands.coordinator.commands.get_jenkins_credentials")
    @patch("mcp_coder.cli.commands.coordinator.commands.load_repo_config")
    @patch("mcp_coder.cli.commands.coordinator.commands.get_cached_eligible_issues")
    @patch("mcp_coder.cli.commands.coordinator.commands.dispatch_workflow")
    @patch("mcp_coder.cli.commands.coordinator.commands.create_default_config")
    def test_execute_coordinator_run_single_repo_success(
        self,
        mock_create_config: MagicMock,
        mock_dispatch_workflow: MagicMock,
        mock_get_cached_issues: MagicMock,
        mock_load_repo: MagicMock,
        mock_get_creds: MagicMock,
        mock_jenkins_class: MagicMock,
        mock_branch_mgr_class: MagicMock,
        mock_issue_mgr_class: MagicMock,
    ) -> None:
        """Test successful execution for single repository using cache."""
        # Setup - Mock args for single repository mode
        args = argparse.Namespace(
            command="coordinator",
            coordinator_subcommand="run",
            repo="mcp_coder",
            all=False,
            log_level="INFO",
            force_refresh=False,
        )

        # Setup - Config already exists
        mock_create_config.return_value = False

        # Setup - Valid repository configuration
        mock_load_repo.return_value = {
            "repo_url": "https://github.com/user/mcp_coder.git",
            "executor_job_path": "MCP_Coder/executor-test",
            "github_credentials_id": "github-pat-123",
            "executor_os": "linux",
        }

        # Setup - Jenkins credentials available
        mock_get_creds.return_value = (
            "https://jenkins.example.com",
            "jenkins_user",
            "jenkins_token_123",
        )

        # Setup - Mock Jenkins client
        mock_jenkins = MagicMock()
        mock_jenkins_class.return_value = mock_jenkins

        # Setup - Mock IssueManager and IssueBranchManager
        mock_issue_mgr = MagicMock()
        mock_branch_mgr = MagicMock()
        mock_issue_mgr_class.return_value = mock_issue_mgr
        mock_branch_mgr_class.return_value = mock_branch_mgr

        # Setup - Mock 2 eligible issues from cache
        mock_get_cached_issues.return_value = [
            IssueData(
                number=124,
                title="Create PR for feature",
                body="Ready for PR",
                state="open",
                labels=["status-08:ready-pr"],
                assignees=[],
                user=None,
                created_at=None,
                updated_at=None,
                url="https://github.com/user/mcp_coder/issues/124",
                locked=False,
            ),
            IssueData(
                number=123,
                title="Implement feature",
                body="Plan ready",
                state="open",
                labels=["status-05:plan-ready"],
                assignees=[],
                user=None,
                created_at=None,
                updated_at=None,
                url="https://github.com/user/mcp_coder/issues/123",
                locked=False,
            ),
        ]

        # Setup - Mock dispatch_workflow succeeds (no exception)
        mock_dispatch_workflow.return_value = None

        # Execute
        result = execute_coordinator_run(args)

        # Verify - Exit code 0 (success)
        assert result == 0

        # Verify - get_cached_eligible_issues was called with correct parameters
        mock_get_cached_issues.assert_called_once()
        call_args = mock_get_cached_issues.call_args[1]
        assert call_args["repo_full_name"] == "user/mcp_coder"
        assert call_args["issue_manager"] == mock_issue_mgr
        assert call_args["force_refresh"] is False

        # Verify - dispatch_workflow was called twice (once for each issue)
        assert mock_dispatch_workflow.call_count == 2

    @patch("mcp_coder.cli.commands.coordinator.commands.create_default_config")
    def test_execute_coordinator_run_creates_config_if_missing(
        self, mock_create_config: MagicMock, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test config file is auto-created on first run."""
        # Setup
        args = argparse.Namespace(repo="mcp_coder", branch_name="feature-x")
        mock_create_config.return_value = True  # Config was created

        # Execute
        result = execute_coordinator_test(args)

        # Verify
        assert result == 1  # Exit to let user configure
        mock_create_config.assert_called_once()

        # Verify message printed
        captured = capsys.readouterr()
        assert "Created default config file" in captured.out


class TestLinuxTemplatesUseTypesExtra:
    """Verify Linux templates use --extra types instead of --extra dev."""

    def test_default_test_command_uses_types_extra(self) -> None:
        """DEFAULT_TEST_COMMAND should use --extra types."""
        assert "uv sync --extra types" in DEFAULT_TEST_COMMAND
        assert "uv sync --extra dev" not in DEFAULT_TEST_COMMAND

    def test_create_plan_command_uses_types_extra(self) -> None:
        """CREATE_PLAN_COMMAND_TEMPLATE should use --extra types."""
        assert "uv sync --extra types" in CREATE_PLAN_COMMAND_TEMPLATE
        assert "uv sync --extra dev" not in CREATE_PLAN_COMMAND_TEMPLATE

    def test_implement_command_uses_types_extra(self) -> None:
        """IMPLEMENT_COMMAND_TEMPLATE should use --extra types."""
        assert "uv sync --extra types" in IMPLEMENT_COMMAND_TEMPLATE
        assert "uv sync --extra dev" not in IMPLEMENT_COMMAND_TEMPLATE

    def test_create_pr_command_uses_types_extra(self) -> None:
        """CREATE_PR_COMMAND_TEMPLATE should use --extra types."""
        assert "uv sync --extra types" in CREATE_PR_COMMAND_TEMPLATE
        assert "uv sync --extra dev" not in CREATE_PR_COMMAND_TEMPLATE


class TestWindowsTemplatesInstallTypeStubs:
    """Verify Windows templates include type stub installation."""

    def test_default_test_command_windows_installs_type_stubs(self) -> None:
        """DEFAULT_TEST_COMMAND_WINDOWS should install type stubs."""
        assert "uv sync --project %WORKSPACE%" in DEFAULT_TEST_COMMAND_WINDOWS
        assert "--extra types" in DEFAULT_TEST_COMMAND_WINDOWS

    def test_create_plan_command_windows_installs_type_stubs(self) -> None:
        """CREATE_PLAN_COMMAND_WINDOWS should install type stubs."""
        assert "uv sync --project %WORKSPACE%" in CREATE_PLAN_COMMAND_WINDOWS
        assert "--extra types" in CREATE_PLAN_COMMAND_WINDOWS

    def test_implement_command_windows_installs_type_stubs(self) -> None:
        """IMPLEMENT_COMMAND_WINDOWS should install type stubs."""
        assert "uv sync --project %WORKSPACE%" in IMPLEMENT_COMMAND_WINDOWS
        assert "--extra types" in IMPLEMENT_COMMAND_WINDOWS

    def test_create_pr_command_windows_installs_type_stubs(self) -> None:
        """CREATE_PR_COMMAND_WINDOWS should install type stubs."""
        assert "uv sync --project %WORKSPACE%" in CREATE_PR_COMMAND_WINDOWS
        assert "--extra types" in CREATE_PR_COMMAND_WINDOWS
