import logging
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.cli.commands.coordinator import WORKFLOW_MAPPING, dispatch_workflow
from mcp_coder.mcp_workspace_github import IssueData
from tests.github_factories import make_issue_data


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
