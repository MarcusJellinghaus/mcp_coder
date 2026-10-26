from typing import Any
from unittest.mock import Mock

import pytest

from mcp_coder.mcp_workspace_github import IssueData
from mcp_coder.workflows.vscodeclaude.issues import (
    build_eligible_issues_with_branch_check,
)
from tests.github_factories import make_issue_data


class TestBuildEligibleIssuesWithBranchCheck:
    """Tests for build_eligible_issues_with_branch_check()."""

    def test_returns_empty_for_no_repos(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Empty repo list returns empty results."""
        # Mock load_config to return empty repos
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.issues.load_config",
            lambda: {"coordinator": {"repos": {}}},
        )

        eligible_issues, issues_without_branch = (
            build_eligible_issues_with_branch_check([])
        )

        assert eligible_issues == []
        assert issues_without_branch == set()

    def test_returns_eligible_issues(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Returns eligible issues from all repos."""
        # Mock config
        mock_config = {
            "coordinator": {
                "repos": {
                    "test-repo": {"repo_url": "https://github.com/owner/repo.git"},
                },
                "vscodeclaude": {"github_username": "testuser"},
            }
        }
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.issues.load_config",
            lambda: mock_config,
        )

        # Mock get_github_username to avoid needing GitHub token
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.issues.get_github_username",
            lambda: "testuser",
        )

        # Mock IssueManager and IssueBranchManager to avoid needing GitHub token
        mock_issue_manager = Mock()
        mock_branch_manager = Mock()
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.issues.IssueManager",
            lambda **kwargs: mock_issue_manager,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.issues.IssueBranchManager",
            lambda **kwargs: mock_branch_manager,
        )

        # Mock eligible issues
        mock_issue = make_issue_data(
            title="Test", labels=["status-01:created"], assignees=["testuser"]
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.issues.get_cached_eligible_vscodeclaude_issues",
            lambda **kwargs: [mock_issue],
        )

        # Mock get_issue_status
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.issues.get_issue_status",
            lambda issue: "status-01:created",
        )

        eligible_issues, issues_without_branch = (
            build_eligible_issues_with_branch_check(["test-repo"])
        )

        assert len(eligible_issues) == 1
        assert eligible_issues[0][0] == "owner/repo"
        assert eligible_issues[0][1]["number"] == 1
        assert issues_without_branch == set()

    def test_identifies_status_04_without_branch(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Issues at status-04 without linked branch added to set."""
        # Mock config
        mock_config = {
            "coordinator": {
                "repos": {
                    "test-repo": {"repo_url": "https://github.com/owner/repo.git"},
                },
                "vscodeclaude": {"github_username": "testuser"},
            }
        }
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.issues.load_config",
            lambda: mock_config,
        )

        # Mock get_github_username to avoid needing GitHub token
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.issues.get_github_username",
            lambda: "testuser",
        )

        # Mock IssueManager and IssueBranchManager to avoid needing GitHub token
        mock_issue_manager = Mock()
        mock_branch_manager = Mock()
        mock_branch_manager.get_branch_with_pr_fallback = Mock(return_value=None)
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.issues.IssueManager",
            lambda **kwargs: mock_issue_manager,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.issues.IssueBranchManager",
            lambda **kwargs: mock_branch_manager,
        )

        # Mock issue at status-04
        mock_issue = make_issue_data(
            title="Test", labels=["status-04:plan-review"], assignees=["testuser"]
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.issues.get_cached_eligible_vscodeclaude_issues",
            lambda **kwargs: [mock_issue],
        )

        # Mock get_issue_status
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.issues.get_issue_status",
            lambda issue: "status-04:plan-review",
        )

        eligible_issues, issues_without_branch = (
            build_eligible_issues_with_branch_check(["test-repo"])
        )

        assert len(eligible_issues) == 1
        assert ("owner/repo", 1) in issues_without_branch

    def test_identifies_status_07_without_branch(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Issues at status-07 without linked branch added to set."""
        # Mock config
        mock_config = {
            "coordinator": {
                "repos": {
                    "test-repo": {"repo_url": "https://github.com/owner/repo.git"},
                },
                "vscodeclaude": {"github_username": "testuser"},
            }
        }
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.issues.load_config",
            lambda: mock_config,
        )

        # Mock get_github_username to avoid needing GitHub token
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.issues.get_github_username",
            lambda: "testuser",
        )

        # Mock IssueManager and IssueBranchManager to avoid needing GitHub token
        mock_issue_manager = Mock()
        mock_branch_manager = Mock()
        mock_branch_manager.get_branch_with_pr_fallback = Mock(return_value=None)
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.issues.IssueManager",
            lambda **kwargs: mock_issue_manager,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.issues.IssueBranchManager",
            lambda **kwargs: mock_branch_manager,
        )

        # Mock issue at status-07
        mock_issue = make_issue_data(
            number=2,
            title="Test",
            labels=["status-07:code-review"],
            assignees=["testuser"],
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.issues.get_cached_eligible_vscodeclaude_issues",
            lambda **kwargs: [mock_issue],
        )

        # Mock get_issue_status
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.issues.get_issue_status",
            lambda issue: "status-07:code-review",
        )

        eligible_issues, issues_without_branch = (
            build_eligible_issues_with_branch_check(["test-repo"])
        )

        assert len(eligible_issues) == 1
        assert ("owner/repo", 2) in issues_without_branch

    def test_handles_multiple_branches(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Issues with multiple linked branches (returns None) added to set."""
        # Mock config
        mock_config = {
            "coordinator": {
                "repos": {
                    "test-repo": {"repo_url": "https://github.com/owner/repo.git"},
                },
                "vscodeclaude": {"github_username": "testuser"},
            }
        }
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.issues.load_config",
            lambda: mock_config,
        )

        # Mock get_github_username to avoid needing GitHub token
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.issues.get_github_username",
            lambda: "testuser",
        )

        # Mock IssueManager and IssueBranchManager to avoid needing GitHub token
        mock_issue_manager = Mock()
        mock_branch_manager = Mock()
        mock_branch_manager.get_branch_with_pr_fallback = Mock(return_value=None)
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.issues.IssueManager",
            lambda **kwargs: mock_issue_manager,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.issues.IssueBranchManager",
            lambda **kwargs: mock_branch_manager,
        )

        # Mock issue at status-04
        mock_issue = make_issue_data(
            number=3,
            title="Test",
            labels=["status-04:plan-review"],
            assignees=["testuser"],
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.issues.get_cached_eligible_vscodeclaude_issues",
            lambda **kwargs: [mock_issue],
        )

        # Mock get_issue_status
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.issues.get_issue_status",
            lambda issue: "status-04:plan-review",
        )

        eligible_issues, issues_without_branch = (
            build_eligible_issues_with_branch_check(["test-repo"])
        )

        assert len(eligible_issues) == 1
        assert ("owner/repo", 3) in issues_without_branch

    def test_status_01_without_branch_not_in_set(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """status-01 issues without branch NOT added to set."""
        # Mock config
        mock_config = {
            "coordinator": {
                "repos": {
                    "test-repo": {"repo_url": "https://github.com/owner/repo.git"},
                },
                "vscodeclaude": {"github_username": "testuser"},
            }
        }
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.issues.load_config",
            lambda: mock_config,
        )

        # Mock get_github_username to avoid needing GitHub token
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.issues.get_github_username",
            lambda: "testuser",
        )

        # Mock IssueManager and IssueBranchManager to avoid needing GitHub token
        mock_issue_manager = Mock()
        mock_branch_manager = Mock()
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.issues.IssueManager",
            lambda **kwargs: mock_issue_manager,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.issues.IssueBranchManager",
            lambda **kwargs: mock_branch_manager,
        )

        # Mock issue at status-01
        mock_issue = make_issue_data(
            number=4,
            title="Test",
            labels=["status-01:created"],
            assignees=["testuser"],
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.issues.get_cached_eligible_vscodeclaude_issues",
            lambda **kwargs: [mock_issue],
        )

        # Mock get_issue_status
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.issues.get_issue_status",
            lambda issue: "status-01:created",
        )

        eligible_issues, issues_without_branch = (
            build_eligible_issues_with_branch_check(["test-repo"])
        )

        assert len(eligible_issues) == 1
        assert ("owner/repo", 4) not in issues_without_branch
        assert issues_without_branch == set()

    def test_continues_on_repo_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Continues processing if one repo fails."""
        # Mock config with two repos
        mock_config = {
            "coordinator": {
                "repos": {
                    "bad-repo": {"repo_url": "https://github.com/owner/bad.git"},
                    "good-repo": {"repo_url": "https://github.com/owner/good.git"},
                },
                "vscodeclaude": {"github_username": "testuser"},
            }
        }
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.issues.load_config",
            lambda: mock_config,
        )

        # Mock get_github_username to avoid needing GitHub token
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.issues.get_github_username",
            lambda: "testuser",
        )

        # Mock IssueManager and IssueBranchManager to avoid needing GitHub token
        mock_issue_manager = Mock()
        mock_branch_manager = Mock()
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.issues.IssueManager",
            lambda **kwargs: mock_issue_manager,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.issues.IssueBranchManager",
            lambda **kwargs: mock_branch_manager,
        )

        # Mock get_cached_eligible_vscodeclaude_issues to fail for bad-repo
        def mock_get_cached(repo_full_name: str, **kwargs: Any) -> list[IssueData]:
            if "bad" in repo_full_name:
                raise RuntimeError("API error")
            return [
                make_issue_data(
                    number=5,
                    title="Good issue",
                    labels=["status-01:created"],
                    assignees=["testuser"],
                    url="https://github.com/owner/good/issues/5",
                )
            ]

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.issues.get_cached_eligible_vscodeclaude_issues",
            mock_get_cached,
        )

        # Mock get_issue_status
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.issues.get_issue_status",
            lambda issue: "status-01:created",
        )

        eligible_issues, _ = build_eligible_issues_with_branch_check(
            ["bad-repo", "good-repo"]
        )

        # Should have issue from good-repo only
        assert len(eligible_issues) == 1
        assert eligible_issues[0][0] == "owner/good"
        assert eligible_issues[0][1]["number"] == 5
