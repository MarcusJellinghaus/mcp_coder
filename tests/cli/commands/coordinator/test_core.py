"""Tests for coordinator core.py functions.

This module contains tests for:
- Configuration management functions (load_repo_config, validate_repo_config, get_jenkins_credentials)
- Workflow dispatch function (dispatch_workflow)
"""

import logging
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.cli.commands.coordinator import (
    WORKFLOW_MAPPING,
    dispatch_workflow,
    get_jenkins_credentials,
    load_repo_config,
    validate_repo_config,
)
from mcp_coder.mcp_workspace_github import IssueData
from tests.github_factories import make_issue_data


class TestLoadRepoConfig:
    """Tests for load_repo_config function."""

    @patch("mcp_coder.cli.commands.coordinator.core.get_config_values")
    def test_load_repo_config_success(self, mock_get_config: MagicMock) -> None:
        """Test successful loading of repository configuration."""
        # Setup - return batch config values dict
        mock_get_config.return_value = {
            (
                "coordinator.repos.mcp_coder",
                "repo_url",
            ): "https://github.com/user/repo.git",
            ("coordinator.repos.mcp_coder", "executor_job_path"): "Folder/job-name",
            ("coordinator.repos.mcp_coder", "github_credentials_id"): "github-pat",
            ("coordinator.repos.mcp_coder", "executor_os"): None,
            ("coordinator.repos.mcp_coder", "update_issue_labels"): None,
            ("coordinator.repos.mcp_coder", "post_issue_comments"): None,
        }

        # Execute
        result = load_repo_config("mcp_coder")

        # Verify
        assert result is not None
        assert result["repo_url"] == "https://github.com/user/repo.git"
        assert result["executor_job_path"] == "Folder/job-name"
        assert result["github_credentials_id"] == "github-pat"
        assert result["executor_os"] == "linux"  # Default

    @patch("mcp_coder.cli.commands.coordinator.core.get_config_values")
    def test_load_repo_config_missing_repo(self, mock_get_config: MagicMock) -> None:
        """Test that missing repository returns dict with None values."""
        # Setup - return dict with None values for all keys
        mock_get_config.return_value = {
            ("coordinator.repos.nonexistent_repo", "repo_url"): None,
            ("coordinator.repos.nonexistent_repo", "executor_job_path"): None,
            ("coordinator.repos.nonexistent_repo", "github_credentials_id"): None,
            ("coordinator.repos.nonexistent_repo", "executor_os"): None,
            ("coordinator.repos.nonexistent_repo", "update_issue_labels"): None,
            ("coordinator.repos.nonexistent_repo", "post_issue_comments"): None,
        }

        # Execute
        result = load_repo_config("nonexistent_repo")

        # Verify - returns dict with None values
        assert result is not None
        assert result["repo_url"] is None
        assert result["executor_job_path"] is None
        assert result["github_credentials_id"] is None
        assert result["executor_os"] == "linux"  # Default

    @patch("mcp_coder.cli.commands.coordinator.core.get_config_values")
    def test_load_repo_config_defaults_executor_os(
        self, mock_get_config: MagicMock
    ) -> None:
        """Test executor_os defaults to 'linux' when not specified."""
        # Setup - return batch config values dict with executor_os as None
        mock_get_config.return_value = {
            (
                "coordinator.repos.test_repo",
                "repo_url",
            ): "https://github.com/test/repo.git",
            ("coordinator.repos.test_repo", "executor_job_path"): "Tests/test",
            ("coordinator.repos.test_repo", "github_credentials_id"): "cred-id",
            ("coordinator.repos.test_repo", "executor_os"): None,  # Not in config
            ("coordinator.repos.test_repo", "update_issue_labels"): None,
            ("coordinator.repos.test_repo", "post_issue_comments"): None,
        }

        # Execute
        config = load_repo_config("test_repo")

        # Verify
        assert config["executor_os"] == "linux"

    @patch("mcp_coder.cli.commands.coordinator.core.get_config_values")
    def test_load_repo_config_normalizes_executor_os(
        self, mock_get_config: MagicMock
    ) -> None:
        """Test executor_os is normalized to lowercase."""
        # Setup - return batch config values dict with mixed case executor_os
        mock_get_config.return_value = {
            (
                "coordinator.repos.test_repo",
                "repo_url",
            ): "https://github.com/test/repo.git",
            ("coordinator.repos.test_repo", "executor_job_path"): "Tests/test",
            ("coordinator.repos.test_repo", "github_credentials_id"): "cred-id",
            ("coordinator.repos.test_repo", "executor_os"): "Windows",  # Mixed case
            ("coordinator.repos.test_repo", "update_issue_labels"): None,
            ("coordinator.repos.test_repo", "post_issue_comments"): None,
        }

        # Execute
        config = load_repo_config("test_repo")

        # Verify
        assert config["executor_os"] == "windows"  # Normalized to lowercase

    @patch("mcp_coder.cli.commands.coordinator.core.get_config_values")
    def test_load_repo_config_includes_issue_interaction_flags(
        self, mock_get_config: MagicMock
    ) -> None:
        """Test config includes update_issue_labels and post_issue_comments when set to True."""
        section = "coordinator.repos.test_repo"
        mock_get_config.return_value = {
            (section, "repo_url"): "https://github.com/test/repo.git",
            (section, "executor_job_path"): "Tests/test",
            (section, "github_credentials_id"): "cred-id",
            (section, "executor_os"): "linux",
            (section, "update_issue_labels"): True,
            (section, "post_issue_comments"): True,
        }

        config = load_repo_config("test_repo")

        assert config["update_issue_labels"] is True
        assert config["post_issue_comments"] is True

    @patch("mcp_coder.cli.commands.coordinator.core.get_config_values")
    def test_load_repo_config_defaults_flags_when_missing(
        self, mock_get_config: MagicMock
    ) -> None:
        """Test flags default to False when not present in config."""
        section = "coordinator.repos.test_repo"
        mock_get_config.return_value = {
            (section, "repo_url"): "https://github.com/test/repo.git",
            (section, "executor_job_path"): "Tests/test",
            (section, "github_credentials_id"): "cred-id",
            (section, "executor_os"): None,
            (section, "update_issue_labels"): None,
            (section, "post_issue_comments"): None,
        }

        config = load_repo_config("test_repo")

        assert config["update_issue_labels"] is False
        assert config["post_issue_comments"] is False


class TestValidateRepoConfig:
    """Tests for validate_repo_config function."""

    def test_validate_repo_config_complete(self) -> None:
        """Test validation passes for complete configuration."""
        # Setup
        config: dict[str, str | bool | int | list[str] | None] = {
            "repo_url": "https://github.com/user/repo.git",
            "executor_job_path": "Folder/job-name",
            "github_credentials_id": "github-pat",
            "executor_os": "linux",
        }

        # Execute - should not raise exception
        validate_repo_config("mcp_coder", config)

    def test_validate_repo_config_missing_repo_url(self) -> None:
        """Test validation fails when repo_url is missing."""
        # Setup
        config: dict[str, str | bool | int | list[str] | None] = {
            "repo_url": None,
            "executor_job_path": "Folder/job-name",
            "github_credentials_id": "github-pat",
        }

        # Execute & Verify
        with pytest.raises(
            ValueError, match="Config file:.*value for field 'repo_url' missing"
        ):
            validate_repo_config("mcp_coder", config)

    def test_validate_repo_config_missing_executor_job_path(self) -> None:
        """Test validation fails when executor_job_path is missing."""
        # Setup
        config: dict[str, str | bool | int | list[str] | None] = {
            "repo_url": "https://github.com/user/repo.git",
            "executor_job_path": None,
            "github_credentials_id": "github-pat",
        }

        # Execute & Verify
        with pytest.raises(
            ValueError,
            match="Config file:.*value for field 'executor_job_path' missing",
        ):
            validate_repo_config("mcp_coder", config)

    def test_validate_repo_config_missing_github_credentials_id(self) -> None:
        """Test validation fails when github_credentials_id is missing."""
        # Setup
        config: dict[str, str | bool | int | list[str] | None] = {
            "repo_url": "https://github.com/user/repo.git",
            "executor_job_path": "Folder/job-name",
            "github_credentials_id": None,
        }

        # Execute & Verify
        with pytest.raises(
            ValueError,
            match="Config file:.*value for field 'github_credentials_id' missing",
        ):
            validate_repo_config("mcp_coder", config)

    def test_validate_repo_config_invalid_executor_os(self) -> None:
        """Test validation fails for invalid executor_os values."""
        # Setup
        config: dict[str, str | bool | int | list[str] | None] = {
            "repo_url": "https://github.com/test/repo.git",
            "executor_job_path": "Tests/test",
            "github_credentials_id": "cred-id",
            "executor_os": "macos",  # Invalid value (already normalized to lowercase)
        }

        # Execute & Verify
        with pytest.raises(
            ValueError,
            match=r"executor_os.*invalid.*got.*macos.*windows.*linux.*case-insensitive",
        ):
            validate_repo_config("test_repo", config)

    def test_validate_repo_config_valid_executor_os(self) -> None:
        """Test validation passes for valid executor_os values (case-insensitive)."""
        # Test both lowercase (normalized) values
        for os_value in ["windows", "linux"]:
            # Setup
            config: dict[str, str | bool | int | list[str] | None] = {
                "repo_url": "https://github.com/test/repo.git",
                "executor_job_path": "Tests/test",
                "github_credentials_id": "cred-id",
                "executor_os": os_value,  # Already normalized to lowercase by load_repo_config
            }

            # Execute & Verify - Should not raise
            validate_repo_config("test_repo", config)


class TestGetJenkinsCredentials:
    """Tests for get_jenkins_credentials function."""

    def test_get_jenkins_credentials_from_env(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test loading credentials from environment variables."""
        # Setup
        monkeypatch.setenv("JENKINS_URL", "https://jenkins.example.com")
        monkeypatch.setenv("JENKINS_USER", "testuser")
        monkeypatch.setenv("JENKINS_TOKEN", "testtoken123")

        # Execute
        server_url, username, api_token = get_jenkins_credentials()

        # Verify
        assert server_url == "https://jenkins.example.com"
        assert username == "testuser"
        assert api_token == "testtoken123"

    @patch("mcp_coder.cli.commands.coordinator.core.get_config_values")
    def test_get_jenkins_credentials_from_config(
        self, mock_get_config: MagicMock, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test loading credentials from config file."""
        # Setup - clear any env vars
        monkeypatch.delenv("JENKINS_URL", raising=False)
        monkeypatch.delenv("JENKINS_USER", raising=False)
        monkeypatch.delenv("JENKINS_TOKEN", raising=False)

        # Setup - return batch config values dict
        mock_get_config.return_value = {
            ("jenkins", "server_url"): "https://jenkins.config.com",
            ("jenkins", "username"): "configuser",
            ("jenkins", "api_token"): "configtoken456",
        }

        # Execute
        server_url, username, api_token = get_jenkins_credentials()

        # Verify
        assert server_url == "https://jenkins.config.com"
        assert username == "configuser"
        assert api_token == "configtoken456"


class TestDispatchWorkflow:
    """Tests for dispatch_workflow function."""

    @patch("mcp_coder.cli.commands.coordinator.core.IssueBranchManager")
    @patch("mcp_coder.cli.commands.coordinator.core.IssueManager")
    @patch("mcp_coder.cli.commands.coordinator.core.JenkinsClient")
    def test_dispatch_workflow_create_plan(
        self,
        mock_jenkins_class: MagicMock,
        mock_issue_mgr_class: MagicMock,
        mock_branch_mgr_class: MagicMock,
    ) -> None:
        """Test dispatching create-plan workflow."""
        # Setup - Mock managers
        mock_jenkins = MagicMock()
        mock_issue_mgr = MagicMock()
        mock_branch_mgr = MagicMock()

        # Setup - Mock issue with status-02:awaiting-planning label
        issue = make_issue_data(
            number=123,
            title="Add feature X",
            body="Description of feature",
            labels=["status-02:awaiting-planning", "enhancement"],
            url="https://github.com/user/repo/issues/123",
        )

        # Setup - Repo configuration
        repo_config = {
            "repo_url": "https://github.com/user/repo.git",
            "executor_job_path": "MCP_Coder/executor-test",
            "github_credentials_id": "github-pat-123",
        }

        # Setup - Mock Jenkins responses
        mock_jenkins.start_job.return_value = 98765  # Queue ID
        mock_jenkins.get_job_status.return_value = MagicMock(status="queued")

        # Execute
        dispatch_workflow(
            issue=issue,
            workflow_name="create-plan",
            repo_config=repo_config,
            repo_name="mcp_coder",
            jenkins_client=mock_jenkins,
            issue_manager=mock_issue_mgr,
            branch_manager=mock_branch_mgr,
            log_level="INFO",
        )

        # Verify - Jenkins job started with correct parameters
        mock_jenkins.start_job.assert_called_once()
        call_args = mock_jenkins.start_job.call_args
        executor_path = call_args[0][0]
        params = call_args[0][1]

        # Verify executor path
        assert executor_path == "MCP_Coder/executor-test"

        # Verify job parameters
        assert params["REPO_URL"] == "https://github.com/user/repo.git"
        assert params["BRANCH_NAME"] == "main"  # create-plan uses main branch
        assert params["GITHUB_CREDENTIALS_ID"] == "github-pat-123"

        # Verify COMMAND contains expected elements for create-plan
        command = params["COMMAND"]
        assert "git checkout main" in command
        assert "git pull" in command
        assert "mcp-coder --log-level INFO create-plan 123" in command

    def test_dispatch_workflow_builds_pipeline_url_from_base_url(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """The queued pipeline link is built from JenkinsClient.base_url."""
        # Setup - Mock managers
        mock_jenkins = MagicMock()
        mock_issue_mgr = MagicMock()
        mock_branch_mgr = MagicMock()

        issue = make_issue_data(
            number=123,
            title="Add feature X",
            body="Description of feature",
            labels=["status-02:awaiting-planning", "enhancement"],
            url="https://github.com/user/repo/issues/123",
        )

        repo_config = {
            "repo_url": "https://github.com/user/repo.git",
            "executor_job_path": "Tests/mcp-coder-test",
            "github_credentials_id": "github-pat-123",
        }

        mock_jenkins.base_url = "https://jenkins.test.com"
        mock_jenkins.start_job.return_value = 98765
        # No build URL yet - dispatch falls back to the pipeline URL
        mock_jenkins.get_job_status.return_value = MagicMock(status="queued", url=None)

        caplog.set_level(logging.INFO, logger="mcp_coder.cli.commands.coordinator.core")

        # Execute
        dispatch_workflow(
            issue=issue,
            workflow_name="create-plan",
            repo_config=repo_config,
            repo_name="mcp_coder",
            jenkins_client=mock_jenkins,
            issue_manager=mock_issue_mgr,
            branch_manager=mock_branch_mgr,
            log_level="INFO",
        )

        # Verify - pipeline URL uses base_url, not the python-jenkins internals
        assert (
            "Pipeline: https://jenkins.test.com/job/Tests/job/mcp-coder-test"
            in caplog.text
        )

    @patch("mcp_coder.cli.commands.coordinator.core.RepoIdentifier")
    def test_dispatch_workflow_handles_missing_branch_gracefully(
        self, mock_repo_id_cls: MagicMock, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test that dispatch_workflow logs error and returns early when no branch found."""
        # Setup - Mock issue with status-08:ready-pr label (requires branch)
        issue = make_issue_data(
            number=156,
            title="Create PR for feature",
            body="Feature ready for PR",
            labels=["status-08:ready-pr"],
            user="testuser",
            created_at="2025-12-31T08:00:00Z",
            updated_at="2025-12-31T09:00:00Z",
            url="https://github.com/test/repo/issues/156",
        )

        # Setup - Repo configuration
        repo_config = {
            "repo_url": "https://github.com/test/repo.git",
            "executor_job_path": "Tests/executor",
            "github_credentials_id": "github-pat",
            "executor_os": "linux",
        }

        # Setup - Mock managers
        mock_jenkins = MagicMock()
        mock_issue_mgr = MagicMock()
        mock_branch_mgr = MagicMock()

        # Mock RepoIdentifier.from_repo_url to return identifier with owner and repo
        mock_repo_id = MagicMock(owner="test", repo_name="repo")
        mock_repo_id_cls.from_repo_url.return_value = mock_repo_id

        # Mock get_branch_with_pr_fallback to return None (missing branch scenario)
        mock_branch_mgr.get_branch_with_pr_fallback.return_value = None

        # Set up logging capture
        caplog.set_level(logging.ERROR, logger="mcp_coder.cli.commands.coordinator")

        # Execute - should complete gracefully without raising exception
        dispatch_workflow(
            issue=issue,
            workflow_name="create-pr",
            repo_config=repo_config,
            repo_name="mcp_coder",
            jenkins_client=mock_jenkins,
            issue_manager=mock_issue_mgr,
            branch_manager=mock_branch_mgr,
            log_level="INFO",
        )

        # Verify RepoIdentifier.from_repo_url was called
        mock_repo_id_cls.from_repo_url.assert_called_once_with(
            "https://github.com/test/repo.git"
        )

        # Verify branch manager was called with correct parameters
        mock_branch_mgr.get_branch_with_pr_fallback.assert_called_once_with(
            issue_number=156, repo_owner="test", repo_name="repo"
        )

        # Verify error was logged with correct message
        assert "No branch found for issue #156" in caplog.text

        # Verify no Jenkins job was triggered (should return early)
        mock_jenkins.start_job.assert_not_called()

        # Verify no label updates occurred (should return early)
        mock_issue_mgr.remove_labels.assert_not_called()
        mock_issue_mgr.add_labels.assert_not_called()

    @patch("mcp_coder.cli.commands.coordinator.core.RepoIdentifier")
    def test_dispatch_workflow_preserves_existing_behavior_with_valid_branch(
        self, mock_repo_id_cls: MagicMock
    ) -> None:
        """Test that existing functionality works unchanged when branch exists."""
        # Setup - Mock issue with status-05:plan-ready label (requires branch)
        issue = make_issue_data(
            number=123,
            title="Implement feature",
            body="Plan is ready for implementation",
            labels=["status-05:plan-ready"],
            user="testuser",
            created_at="2025-12-31T08:00:00Z",
            updated_at="2025-12-31T09:00:00Z",
            url="https://github.com/test/repo/issues/123",
        )

        # Setup - Repo configuration
        repo_config = {
            "repo_url": "https://github.com/test/repo.git",
            "executor_job_path": "Tests/executor",
            "github_credentials_id": "github-pat",
            "executor_os": "linux",
        }

        # Setup - Mock managers
        mock_jenkins = MagicMock()
        mock_issue_mgr = MagicMock()
        mock_branch_mgr = MagicMock()

        # Mock RepoIdentifier.from_repo_url to return identifier with owner and repo
        mock_repo_id = MagicMock(owner="test", repo_name="repo")
        mock_repo_id_cls.from_repo_url.return_value = mock_repo_id

        # Mock get_branch_with_pr_fallback to return valid branch
        mock_branch_mgr.get_branch_with_pr_fallback.return_value = "feature/issue-123"

        # Mock Jenkins responses
        mock_jenkins.start_job.return_value = 98765
        mock_jenkins.get_job_status.return_value = MagicMock(status="queued", url=None)
        mock_jenkins.base_url = "https://jenkins.test.com"

        # Execute - should complete successfully
        dispatch_workflow(
            issue=issue,
            workflow_name="implement",
            repo_config=repo_config,
            repo_name="mcp_coder",
            jenkins_client=mock_jenkins,
            issue_manager=mock_issue_mgr,
            branch_manager=mock_branch_mgr,
            log_level="INFO",
        )

        # Verify RepoIdentifier.from_repo_url was called
        mock_repo_id_cls.from_repo_url.assert_called_once_with(
            "https://github.com/test/repo.git"
        )

        # Verify branch manager was called with correct parameters
        mock_branch_mgr.get_branch_with_pr_fallback.assert_called_once_with(
            issue_number=123, repo_owner="test", repo_name="repo"
        )

        # Verify Jenkins job was triggered with correct branch
        mock_jenkins.start_job.assert_called_once()
        call_args = mock_jenkins.start_job.call_args
        params = call_args[0][1]
        assert params["BRANCH_NAME"] == "feature/issue-123"

        # Verify label updates occurred
        mock_issue_mgr.remove_labels.assert_called_once_with(
            123, "status-05:plan-ready"
        )
        mock_issue_mgr.add_labels.assert_called_once_with(123, "status-06:implementing")


class TestDispatchWorkflowSilentFallthroughGuard:
    """Behavioral guard: every WORKFLOW_MAPPING workflow dispatches its own verb.

    A workflow present in WORKFLOW_MAPPING but missing from WORKFLOW_TEMPLATES
    would raise KeyError at dispatch (loud failure) instead of silently
    misrouting to create-pr. This test drives dispatch_workflow for every
    distinct workflow on both executor_os arms and asserts the COMMAND passed
    to Jenkins carries that workflow's CLI verb.
    """

    @staticmethod
    def _make_issue(pickup_label: str) -> IssueData:
        """Build a minimal open IssueData carrying the given pickup label.

        Returns:
            IssueData with the pickup label applied.
        """
        return make_issue_data(
            number=777,
            title="Guard issue",
            labels=[pickup_label],
            user="testuser",
            created_at="2026-01-01T00:00:00Z",
            updated_at="2026-01-01T00:00:00Z",
            url="https://github.com/test/repo/issues/777",
        )

    @pytest.mark.parametrize("executor_os", ["windows", "linux"])
    @pytest.mark.parametrize(
        "pickup_label,config",
        list(WORKFLOW_MAPPING.items()),
        ids=[config["workflow"] for config in WORKFLOW_MAPPING.values()],
    )
    @patch("mcp_coder.cli.commands.coordinator.core.RepoIdentifier")
    def test_each_workflow_dispatches_its_verb(
        self,
        mock_repo_id_cls: MagicMock,
        pickup_label: str,
        config: dict[str, str],
        executor_os: str,
    ) -> None:
        """The COMMAND for each workflow contains that workflow's CLI verb."""
        workflow = config["workflow"]

        issue = self._make_issue(pickup_label)

        repo_config = {
            "repo_url": "https://github.com/test/repo.git",
            "executor_job_path": "Tests/executor",
            "github_credentials_id": "github-pat",
            "executor_os": executor_os,
        }

        mock_jenkins = MagicMock()
        mock_issue_mgr = MagicMock()
        mock_branch_mgr = MagicMock()

        # Branch resolution (used by from_issue strategies)
        mock_repo_id = MagicMock(owner="test", repo_name="repo")
        mock_repo_id_cls.from_repo_url.return_value = mock_repo_id
        mock_branch_mgr.get_branch_with_pr_fallback.return_value = "feature/issue-777"

        mock_jenkins.start_job.return_value = 12345
        mock_jenkins.get_job_status.return_value = MagicMock(url=None)
        mock_jenkins.base_url = "https://jenkins.test.com"

        dispatch_workflow(
            issue=issue,
            workflow_name=workflow,
            repo_config=repo_config,
            repo_name="test_repo",
            jenkins_client=mock_jenkins,
            issue_manager=mock_issue_mgr,
            branch_manager=mock_branch_mgr,
            log_level="INFO",
        )

        mock_jenkins.start_job.assert_called_once()
        params = mock_jenkins.start_job.call_args[0][1]
        command = params["COMMAND"]
        assert f"mcp-coder --log-level INFO {workflow} " in command, (
            f"COMMAND for {workflow!r} ({executor_os}) missing its verb"
        )
        assert params["LABEL"] == f"test_repo - #777 - {workflow}"
