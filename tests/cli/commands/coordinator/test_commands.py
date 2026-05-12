"""Tests for coordinator commands.py functions.

This module contains tests for:
- Job output formatting (format_job_output)
- Coordinator test execution (execute_coordinator_test)
- Coordinator run execution (execute_coordinator_run)
"""

import argparse
import logging
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.cli.commands.coordinator import (
    DEFAULT_TEST_COMMAND,
    execute_coordinator_run,
    execute_coordinator_test,
    format_job_output,
)
from mcp_coder.mcp_workspace_github import IssueData
from mcp_coder.utils.jenkins_operations.models import JobStatus
from mcp_coder.workflows.vscodeclaude.types import VSCodeClaudeConfig


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
        caplog: pytest.LogCaptureFixture,
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
        with caplog.at_level(logging.DEBUG):
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

        # Verify output logged
        assert "Job triggered: MCP/test-job - test - queue: 12345" in caplog.text
        assert "https://jenkins:8080/queue/item/12345/" in caplog.text


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
        self, mock_create_config: MagicMock, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test config file is auto-created on first run."""
        # Setup
        args = argparse.Namespace(repo="mcp_coder", branch_name="feature-x")
        mock_create_config.return_value = True  # Config was created

        # Execute
        with caplog.at_level(logging.DEBUG):
            result = execute_coordinator_test(args)

        # Verify
        assert result == 1  # Exit to let user configure
        mock_create_config.assert_called_once()

        # Verify message logged
        assert "Created default config file" in caplog.text


class TestSkipGithubInstallWiring:
    """Tests for --no-install-from-github flag wiring through commands."""

    @patch("mcp_coder.cli.commands.coordinator.commands.process_eligible_issues")
    @patch("mcp_coder.cli.commands.coordinator.commands.restart_closed_sessions")
    @patch("mcp_coder.cli.commands.coordinator.commands.cleanup_stale_sessions")
    @patch("mcp_coder.cli.commands.coordinator.commands._build_cached_issues_by_repo")
    @patch("mcp_coder.cli.commands.coordinator.commands.load_sessions")
    @patch("mcp_coder.cli.commands.coordinator.commands.load_config")
    @patch("mcp_coder.cli.commands.coordinator.commands.load_vscodeclaude_config")
    @patch("mcp_coder.cli.commands.coordinator.commands.load_repo_config")
    @patch("mcp_coder.cli.commands.coordinator.commands.create_default_config")
    def test_execute_coordinator_vscodeclaude_passes_skip_github_install(
        self,
        mock_create_config: MagicMock,
        mock_load_repo: MagicMock,
        mock_load_vsc_config: MagicMock,
        mock_load_config: MagicMock,
        mock_load_sessions: MagicMock,
        mock_build_cache: MagicMock,
        mock_cleanup: MagicMock,
        mock_restart: MagicMock,
        mock_process: MagicMock,
    ) -> None:
        """execute_coordinator_vscodeclaude passes skip_github_install to process_eligible_issues."""
        mock_create_config.return_value = False
        mock_load_vsc_config.return_value = {
            "workspace_base": "/tmp",
            "max_sessions": 3,
        }
        mock_load_config.return_value = {"coordinator": {"repos": {"mcp_coder": {}}}}
        mock_load_sessions.return_value = {"sessions": [], "last_updated": ""}
        mock_build_cache.return_value = (
            {"owner/mcp_coder": {1: MagicMock()}},
            set(),
        )
        mock_restart.return_value = []
        mock_load_repo.return_value = {
            "repo_url": "https://github.com/owner/mcp_coder.git",
        }
        mock_process.return_value = []

        args = argparse.Namespace(
            repo=None,
            max_sessions=None,
            cleanup=False,
            intervene=False,
            issue=None,
            no_install_from_github=True,
        )

        from mcp_coder.cli.commands.coordinator.commands import (
            execute_coordinator_vscodeclaude,
        )

        execute_coordinator_vscodeclaude(args)

        mock_process.assert_called_once()
        call_kwargs = mock_process.call_args[1]
        assert call_kwargs["skip_github_install"] is True

    @patch("mcp_coder.cli.commands.coordinator.commands.prepare_and_launch_session")
    @patch("mcp_coder.cli.commands.coordinator.commands.load_repo_vscodeclaude_config")
    @patch("mcp_coder.cli.commands.coordinator.commands.IssueBranchManager")
    @patch("mcp_coder.cli.commands.coordinator.commands.IssueManager")
    @patch("mcp_coder.cli.commands.coordinator.commands.load_repo_config")
    def test_handle_intervention_mode_passes_skip_github_install(
        self,
        mock_load_repo: MagicMock,
        mock_issue_mgr_cls: MagicMock,
        mock_branch_mgr_cls: MagicMock,
        mock_load_repo_vsc: MagicMock,
        mock_prepare: MagicMock,
    ) -> None:
        """_handle_intervention_mode passes skip_github_install to prepare_and_launch_session."""
        mock_load_repo.return_value = {
            "repo_url": "https://github.com/owner/repo.git",
        }
        mock_issue_mgr = MagicMock()
        mock_issue_mgr.get_issue.return_value = {
            "number": 42,
            "title": "Test",
            "labels": [],
            "state": "open",
            "url": "",
        }
        mock_issue_mgr_cls.return_value = mock_issue_mgr

        mock_branch_mgr = MagicMock()
        mock_branch_mgr.get_branch_with_pr_fallback.return_value = "feature-branch"
        mock_branch_mgr_cls.return_value = mock_branch_mgr

        mock_load_repo_vsc.return_value = {}
        mock_prepare.return_value = {
            "issue_number": 42,
            "repo": "owner/repo",
            "folder": "/tmp/test",
            "status": "open",
            "vscode_pid": 1234,
            "is_intervention": True,
            "started_at": "2024-01-01",
        }

        args = argparse.Namespace(
            repo="mcp_coder",
            issue=42,
            intervene=True,
            no_install_from_github=True,
        )
        vscodeclaude_config: VSCodeClaudeConfig = {
            "workspace_base": "/tmp",
            "max_sessions": 3,
        }

        from mcp_coder.cli.commands.coordinator.commands import (
            _handle_intervention_mode,
        )

        _handle_intervention_mode(args, vscodeclaude_config)

        mock_prepare.assert_called_once()
        call_kwargs = mock_prepare.call_args[1]
        assert call_kwargs["skip_github_install"] is True


class TestAtCapacityDiagnosticLog:
    """Tests for the at-capacity diagnostic log line in execute_coordinator_vscodeclaude."""

    @patch("mcp_coder.cli.commands.coordinator.commands.process_eligible_issues")
    @patch("mcp_coder.cli.commands.coordinator.commands.restart_closed_sessions")
    @patch("mcp_coder.cli.commands.coordinator.commands.cleanup_stale_sessions")
    @patch("mcp_coder.cli.commands.coordinator.commands.build_active_session_set")
    @patch("mcp_coder.cli.commands.coordinator.commands._build_cached_issues_by_repo")
    @patch("mcp_coder.cli.commands.coordinator.commands.load_sessions")
    @patch("mcp_coder.cli.commands.coordinator.commands.load_config")
    @patch("mcp_coder.cli.commands.coordinator.commands.load_vscodeclaude_config")
    @patch("mcp_coder.cli.commands.coordinator.commands.load_repo_config")
    @patch("mcp_coder.cli.commands.coordinator.commands.create_default_config")
    def test_at_capacity_log_includes_folder_basenames(
        self,
        mock_create_config: MagicMock,
        mock_load_repo: MagicMock,
        mock_load_vsc_config: MagicMock,
        mock_load_config: MagicMock,
        mock_load_sessions: MagicMock,
        mock_build_cache: MagicMock,
        mock_build_active: MagicMock,
        mock_cleanup: MagicMock,
        mock_restart: MagicMock,
        mock_process: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """At capacity, the tail log line names the folders consuming the slots."""
        mock_create_config.return_value = False
        mock_load_vsc_config.return_value = {
            "workspace_base": "/tmp",
            "max_sessions": 2,
        }
        mock_load_config.return_value = {"coordinator": {"repos": {"mcp_coder": {}}}}
        mock_load_sessions.return_value = {"sessions": [], "last_updated": ""}
        mock_build_cache.return_value = (
            {"owner/mcp_coder": {1: MagicMock()}},
            set(),
        )
        # Two active folders => at capacity for max_sessions=2.
        mock_build_active.return_value = {
            "/tmp/repo_111": True,
            "/tmp/repo_222": True,
        }
        mock_restart.return_value = []
        mock_load_repo.return_value = {
            "repo_url": "https://github.com/owner/mcp_coder.git",
        }
        mock_process.return_value = []  # No new sessions started

        args = argparse.Namespace(
            repo=None,
            max_sessions=None,
            cleanup=False,
            intervene=False,
            issue=None,
            no_install_from_github=False,
        )

        from mcp_coder.cli.commands.coordinator.commands import (
            execute_coordinator_vscodeclaude,
        )

        with caplog.at_level(logging.INFO):
            execute_coordinator_vscodeclaude(args)

        assert "at capacity (2/2)" in caplog.text
        assert "repo_111" in caplog.text
        assert "repo_222" in caplog.text

    @patch("mcp_coder.cli.commands.coordinator.commands.process_eligible_issues")
    @patch("mcp_coder.cli.commands.coordinator.commands.restart_closed_sessions")
    @patch("mcp_coder.cli.commands.coordinator.commands.cleanup_stale_sessions")
    @patch("mcp_coder.cli.commands.coordinator.commands.build_active_session_set")
    @patch("mcp_coder.cli.commands.coordinator.commands._build_cached_issues_by_repo")
    @patch("mcp_coder.cli.commands.coordinator.commands.load_sessions")
    @patch("mcp_coder.cli.commands.coordinator.commands.load_config")
    @patch("mcp_coder.cli.commands.coordinator.commands.load_vscodeclaude_config")
    @patch("mcp_coder.cli.commands.coordinator.commands.load_repo_config")
    @patch("mcp_coder.cli.commands.coordinator.commands.create_default_config")
    def test_below_capacity_message_unchanged(
        self,
        mock_create_config: MagicMock,
        mock_load_repo: MagicMock,
        mock_load_vsc_config: MagicMock,
        mock_load_config: MagicMock,
        mock_load_sessions: MagicMock,
        mock_build_cache: MagicMock,
        mock_build_active: MagicMock,
        mock_cleanup: MagicMock,
        mock_restart: MagicMock,
        mock_process: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Below capacity with no started sessions preserves the legacy tail format."""
        mock_create_config.return_value = False
        mock_load_vsc_config.return_value = {
            "workspace_base": "/tmp",
            "max_sessions": 3,
        }
        mock_load_config.return_value = {"coordinator": {"repos": {"mcp_coder": {}}}}
        mock_load_sessions.return_value = {"sessions": [], "last_updated": ""}
        mock_build_cache.return_value = (
            {"owner/mcp_coder": {1: MagicMock()}},
            set(),
        )
        mock_build_active.return_value = {}  # No active sessions
        mock_restart.return_value = []
        mock_load_repo.return_value = {
            "repo_url": "https://github.com/owner/mcp_coder.git",
        }
        mock_process.return_value = []

        args = argparse.Namespace(
            repo=None,
            max_sessions=None,
            cleanup=False,
            intervene=False,
            issue=None,
            no_install_from_github=False,
        )

        from mcp_coder.cli.commands.coordinator.commands import (
            execute_coordinator_vscodeclaude,
        )

        with caplog.at_level(logging.INFO):
            execute_coordinator_vscodeclaude(args)

        assert "No new sessions started (active: 0/3)" in caplog.text
        assert "at capacity" not in caplog.text

    def test_process_eligible_issues_at_capacity_log_is_debug(
        self,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """The per-repo 'Already at max sessions' log is emitted at DEBUG, not INFO."""
        from mcp_coder.workflows.vscodeclaude.session_launch import (
            process_eligible_issues,
        )

        with caplog.at_level(logging.INFO):
            result = process_eligible_issues(
                repo_name="test-repo",
                repo_config={"repo_url": "https://github.com/owner/repo"},
                vscodeclaude_config={"workspace_base": "/tmp", "max_sessions": 2},
                max_sessions=2,
                current_count=2,
            )

        assert result == []
        # At INFO level, the message must NOT appear (downgraded to DEBUG).
        assert "Already at max sessions" not in caplog.text

        # At DEBUG level, the message should still be present.
        caplog.clear()
        with caplog.at_level(logging.DEBUG):
            process_eligible_issues(
                repo_name="test-repo",
                repo_config={"repo_url": "https://github.com/owner/repo"},
                vscodeclaude_config={"workspace_base": "/tmp", "max_sessions": 2},
                max_sessions=2,
                current_count=2,
            )

        assert "Already at max sessions" in caplog.text
