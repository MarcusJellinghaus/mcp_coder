"""Tests for process_eligible_issues branch requirements and pre-fetched issues."""

import logging
from typing import Any
from unittest.mock import MagicMock

import pytest

from mcp_coder.mcp_workspace_github import (
    BranchLookup,
    BranchLookupError,
    GitHubRateLimitError,
    IssueData,
)
from mcp_coder.workflows.vscodeclaude.session_launch import (
    process_eligible_issues,
)
from tests.github_factories import make_issue_data
from tests.workflows.vscodeclaude.conftest import patch_branch_cache

LAUNCH = "mcp_coder.workflows.vscodeclaude.session_launch"


class TestProcessEligibleIssuesMaxSessions:
    """Tests for the max_sessions limit in process_eligible_issues()."""

    def test_process_eligible_issues_respects_max_sessions(
        self,
    ) -> None:
        """Doesn't start sessions beyond max."""
        # Should return empty since already at/above max
        sessions = process_eligible_issues(
            repo_name="test",
            repo_config={"repo_url": "https://github.com/owner/repo.git"},
            vscodeclaude_config={"workspace_base": "/tmp", "max_sessions": 2},
            max_sessions=2,
            current_count=2,
        )

        assert sessions == []


class TestProcessEligibleIssuesBranchRequirement:
    """Tests for branch requirement enforcement in process_eligible_issues()."""

    def test_status_01_without_branch_launches_on_main(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """status-01 without linked branch launches session on main."""
        # Setup mocks
        mock_issue = make_issue_data(
            number=123,
            title="Test Issue",
            labels=["status-01:created"],
            assignees=["testuser"],
        )

        # Mock IssueManager and IssueBranchManager to avoid token validation
        mock_issue_manager = MagicMock()
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.IssueManager",
            lambda **kwargs: mock_issue_manager,
        )
        patch_branch_cache(monkeypatch, LAUNCH)

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.get_all_cached_issues",
            lambda *args, **kwargs: [mock_issue],
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch._filter_eligible_vscodeclaude_issues",
            lambda *args, **kwargs: [mock_issue],
        )
        mock_launch = MagicMock()
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.prepare_and_launch_session",
            mock_launch,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.get_session_for_issue",
            lambda *args, **kwargs: None,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.get_github_username",
            lambda: "testuser",
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.load_repo_vscodeclaude_config",
            lambda *args, **kwargs: {},
        )

        process_eligible_issues(
            repo_name="test-repo",
            repo_config={"repo_url": "https://github.com/owner/repo"},
            vscodeclaude_config={"workspace_base": "/tmp", "max_sessions": 3},
            max_sessions=3,
            current_count=0,
        )

        # Session should be launched with branch_name=None (defaults to main)
        mock_launch.assert_called_once()
        call_kwargs = mock_launch.call_args.kwargs
        assert call_kwargs["branch_name"] is None

    def test_status_04_without_branch_skips_issue(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        """status-04 without linked branch skips issue and logs error."""
        mock_issue = make_issue_data(
            number=456,
            title="Plan Review Issue",
            labels=["status-04:plan-review"],
            assignees=["testuser"],
        )

        # Mock IssueManager and IssueBranchManager to avoid token validation
        mock_issue_manager = MagicMock()
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.IssueManager",
            lambda **kwargs: mock_issue_manager,
        )
        patch_branch_cache(monkeypatch, LAUNCH)

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.get_all_cached_issues",
            lambda *args, **kwargs: [mock_issue],
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch._filter_eligible_vscodeclaude_issues",
            lambda *args, **kwargs: [mock_issue],
        )
        mock_launch = MagicMock()
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.prepare_and_launch_session",
            mock_launch,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.get_session_for_issue",
            lambda *args, **kwargs: None,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.get_github_username",
            lambda: "testuser",
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.load_repo_vscodeclaude_config",
            lambda *args, **kwargs: {},
        )

        with caplog.at_level(logging.ERROR):
            result = process_eligible_issues(
                repo_name="test-repo",
                repo_config={"repo_url": "https://github.com/owner/repo"},
                vscodeclaude_config={"workspace_base": "/tmp", "max_sessions": 3},
                max_sessions=3,
                current_count=0,
            )

        # Session should NOT be launched
        mock_launch.assert_not_called()
        # Error should be logged
        assert "no linked branch" in caplog.text.lower()
        assert "#456" in caplog.text
        # Empty result
        assert result == []

    def test_status_07_without_branch_skips_issue(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        """status-07 without linked branch skips issue."""
        mock_issue = make_issue_data(
            number=789,
            title="Code Review Issue",
            labels=["status-07:code-review"],
            assignees=["testuser"],
        )

        # Mock IssueManager and IssueBranchManager to avoid token validation
        mock_issue_manager = MagicMock()
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.IssueManager",
            lambda **kwargs: mock_issue_manager,
        )
        patch_branch_cache(monkeypatch, LAUNCH)

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.get_all_cached_issues",
            lambda *args, **kwargs: [mock_issue],
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch._filter_eligible_vscodeclaude_issues",
            lambda *args, **kwargs: [mock_issue],
        )
        mock_launch = MagicMock()
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.prepare_and_launch_session",
            mock_launch,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.get_session_for_issue",
            lambda *args, **kwargs: None,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.get_github_username",
            lambda: "testuser",
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.load_repo_vscodeclaude_config",
            lambda *args, **kwargs: {},
        )

        with caplog.at_level(logging.ERROR):
            result = process_eligible_issues(
                repo_name="test-repo",
                repo_config={"repo_url": "https://github.com/owner/repo"},
                vscodeclaude_config={"workspace_base": "/tmp", "max_sessions": 3},
                max_sessions=3,
                current_count=0,
            )

        mock_launch.assert_not_called()
        assert result == []

    def test_status_04_with_branch_launches_session(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """status-04 with linked branch launches session normally."""
        mock_issue = make_issue_data(
            number=456,
            title="Plan Review Issue",
            labels=["status-04:plan-review"],
            assignees=["testuser"],
        )

        # Mock IssueManager and IssueBranchManager to avoid token validation
        mock_issue_manager = MagicMock()
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.IssueManager",
            lambda **kwargs: mock_issue_manager,
        )
        patch_branch_cache(monkeypatch, LAUNCH, branch="feat-456")

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.get_all_cached_issues",
            lambda *args, **kwargs: [mock_issue],
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch._filter_eligible_vscodeclaude_issues",
            lambda *args, **kwargs: [mock_issue],
        )
        mock_launch = MagicMock()
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.prepare_and_launch_session",
            mock_launch,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.get_session_for_issue",
            lambda *args, **kwargs: None,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.get_github_username",
            lambda: "testuser",
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.load_repo_vscodeclaude_config",
            lambda *args, **kwargs: {},
        )

        process_eligible_issues(
            repo_name="test-repo",
            repo_config={"repo_url": "https://github.com/owner/repo"},
            vscodeclaude_config={"workspace_base": "/tmp", "max_sessions": 3},
            max_sessions=3,
            current_count=0,
        )

        mock_launch.assert_called_once()
        call_kwargs = mock_launch.call_args.kwargs
        assert call_kwargs["branch_name"] == "feat-456"

    def test_status_04_with_multiple_branches_skips_issue(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        """status-04 with multiple linked branches skips issue and logs error."""
        mock_issue = make_issue_data(
            number=456,
            title="Plan Review Issue",
            labels=["status-04:plan-review"],
            assignees=["testuser"],
        )

        # Mock IssueManager and IssueBranchManager to avoid token validation
        mock_issue_manager = MagicMock()
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.IssueManager",
            lambda **kwargs: mock_issue_manager,
        )
        branch_cache = patch_branch_cache(monkeypatch, LAUNCH)
        branch_cache.lookup.return_value = BranchLookup("ambiguous")

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.get_all_cached_issues",
            lambda *args, **kwargs: [mock_issue],
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch._filter_eligible_vscodeclaude_issues",
            lambda *args, **kwargs: [mock_issue],
        )

        mock_launch = MagicMock()
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.prepare_and_launch_session",
            mock_launch,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.get_session_for_issue",
            lambda *args, **kwargs: None,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.get_github_username",
            lambda: "testuser",
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.load_repo_vscodeclaude_config",
            lambda *args, **kwargs: {},
        )

        with caplog.at_level(logging.ERROR):
            result = process_eligible_issues(
                repo_name="test-repo",
                repo_config={"repo_url": "https://github.com/owner/repo"},
                vscodeclaude_config={"workspace_base": "/tmp", "max_sessions": 3},
                max_sessions=3,
                current_count=0,
            )

        # Session should NOT be launched
        mock_launch.assert_not_called()
        # Error should be logged
        assert "no linked branch" in caplog.text.lower()
        assert "#456" in caplog.text
        # Empty result
        assert result == []


class TestProcessEligibleIssuesPrefetchedIssues:
    """Tests for pre-fetched issues bypassing get_all_cached_issues."""

    def test_pre_fetched_issues_bypasses_get_all_cached_issues(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """When all_cached_issues is passed, get_all_cached_issues is not called."""
        mock_issue = make_issue_data(
            number=101,
            title="Pre-fetched Issue",
            labels=["status-01:created"],
            assignees=["testuser"],
        )

        # Mock IssueManager and IssueBranchManager to avoid token validation
        mock_issue_manager = MagicMock()
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.IssueManager",
            lambda **kwargs: mock_issue_manager,
        )
        patch_branch_cache(monkeypatch, LAUNCH)

        # get_all_cached_issues must NOT be called — raises AssertionError if invoked
        def _should_not_be_called(*args: Any, **kwargs: Any) -> list[IssueData]:
            raise AssertionError("get_all_cached_issues should not be called")

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.get_all_cached_issues",
            _should_not_be_called,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch._filter_eligible_vscodeclaude_issues",
            lambda *args, **kwargs: [mock_issue],
        )
        mock_launch = MagicMock()
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.prepare_and_launch_session",
            mock_launch,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.get_session_for_issue",
            lambda *args, **kwargs: None,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.get_github_username",
            lambda: "testuser",
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.load_repo_vscodeclaude_config",
            lambda *args, **kwargs: {},
        )

        # Pass pre-fetched issues directly — get_all_cached_issues must not be called
        process_eligible_issues(
            repo_name="test-repo",
            repo_config={"repo_url": "https://github.com/owner/repo"},
            vscodeclaude_config={"workspace_base": "/tmp", "max_sessions": 3},
            max_sessions=3,
            current_count=0,
            all_cached_issues=[mock_issue],
        )

        # The pre-fetched issue was used: session was launched once
        mock_launch.assert_called_once()


class TestProcessEligibleIssuesBranchCache:
    """process_eligible_issues resolves branches through one BranchLookupCache."""

    @staticmethod
    def _patch(monkeypatch: pytest.MonkeyPatch) -> tuple[MagicMock, MagicMock]:
        branch_cache = patch_branch_cache(monkeypatch, LAUNCH, branch="feat")
        launch = MagicMock()
        monkeypatch.setattr(f"{LAUNCH}.IssueManager", lambda **kw: MagicMock())
        monkeypatch.setattr(f"{LAUNCH}.get_github_username", lambda: "testuser")
        monkeypatch.setattr(
            f"{LAUNCH}._filter_eligible_vscodeclaude_issues", lambda i, u: i
        )
        monkeypatch.setattr(f"{LAUNCH}.get_session_for_issue", lambda *a, **kw: None)
        monkeypatch.setattr(
            f"{LAUNCH}.load_repo_vscodeclaude_config", lambda *a, **kw: {}
        )
        monkeypatch.setattr(f"{LAUNCH}.prepare_and_launch_session", launch)
        return branch_cache, launch

    @staticmethod
    def _run(issues: list[IssueData]) -> None:
        process_eligible_issues(
            repo_name="test-repo",
            repo_config={"repo_url": "https://github.com/owner/repo"},
            vscodeclaude_config={"workspace_base": "/tmp", "max_sessions": 3},
            max_sessions=3,
            current_count=0,
            all_cached_issues=issues,
        )

    @staticmethod
    def _issues() -> list[IssueData]:
        return [
            make_issue_data(
                number=n, labels=["status-04:plan-review"], assignees=["testuser"]
            )
            for n in (1, 2)
        ]

    def test_lookup_error_skips_issue_and_continues(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        branch_cache, launch = self._patch(monkeypatch)
        branch_cache.lookup.side_effect = [
            BranchLookupError("boom"),
            BranchLookup("found", "2-fix"),
        ]

        self._run(self._issues())

        launch.assert_called_once()
        assert launch.call_args.kwargs["branch_name"] == "2-fix"

    def test_one_load_and_one_save(self, monkeypatch: pytest.MonkeyPatch) -> None:
        branch_cache, launch = self._patch(monkeypatch)

        self._run(self._issues())

        branch_cache.cache_cls.load.assert_called_once()
        assert branch_cache.lookup.call_count == 2
        branch_cache.save.assert_called_once_with()
        assert launch.call_count == 2

    def test_rate_limit_propagates_and_saves(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        branch_cache, launch = self._patch(monkeypatch)
        branch_cache.lookup.side_effect = GitHubRateLimitError("limited")

        with pytest.raises(GitHubRateLimitError):
            self._run(self._issues())

        assert branch_cache.lookup.call_count == 1
        branch_cache.save.assert_called_once_with()
        launch.assert_not_called()
