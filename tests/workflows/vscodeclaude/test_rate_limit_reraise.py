"""Inner vscodeclaude ``except`` blocks re-raise GitHub rate limits."""

import json
import logging
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from mcp_coder.mcp_workspace_github import (
    GithubException,
    GitHubRateLimitError,
    IssueData,
)
from mcp_coder.workflows.vscodeclaude.assessment import (
    _fetch_issue_individually,
    build_assessments,
)
from mcp_coder.workflows.vscodeclaude.checks import check_pr_health
from mcp_coder.workflows.vscodeclaude.issues import (
    build_eligible_issues_with_branch_check,
)
from mcp_coder.workflows.vscodeclaude.session_launch import process_eligible_issues
from mcp_coder.workflows.vscodeclaude.session_restart import (
    BranchPrepResult,
    restart_closed_sessions,
)
from mcp_coder.workflows.vscodeclaude.types import VSCodeClaudeSession
from mcp_coder.workflows.vscodeclaude.workspace import _fetch_marked_comment
from tests.github_factories import make_issue_data
from tests.workflows.vscodeclaude.conftest import (
    make_assessment,
    make_session_at,
    patch_branch_cache,
)
from tests.workflows.vscodeclaude.test_checks import (
    REPO_CONFIG,
    _make_pr_issue,
    _setup,
)

CHECKS = "mcp_coder.workflows.vscodeclaude.checks"
ISSUES = "mcp_coder.workflows.vscodeclaude.issues"
LAUNCH = "mcp_coder.workflows.vscodeclaude.session_launch"
RESTART = "mcp_coder.workflows.vscodeclaude.session_restart"
ASSESSMENT = "mcp_coder.workflows.vscodeclaude.assessment"
WORKSPACE = "mcp_coder.workflows.vscodeclaude.workspace"


def _rate_limit() -> GithubException:
    return GithubException(
        403,
        {"message": "API rate limit exceeded"},
        headers={"x-ratelimit-remaining": "0", "x-ratelimit-reset": "1900000000"},
    )


def _wrapped_rate_limit() -> ValueError:
    """The ``GET /user`` shape: a ValueError whose ``__cause__`` is the limit."""
    try:
        try:
            raise _rate_limit()
        except GithubException as e:
            raise ValueError("could not get user") from e
    except ValueError as wrapped:
        return wrapped


class TestCheckPrHealthRateLimit:
    """check_pr_health stops on the first rate limit."""

    @pytest.mark.parametrize(
        "manager_index, method",
        [
            (1, "lookup"),
            (3, "find_pr"),
            (3, "mergeable_state"),
            (3, "ci_status"),
            (2, "get_latest_ci_status"),
            (3, "feedback"),
        ],
    )
    def test_limit_in_first_issue_propagates(
        self, monkeypatch: pytest.MonkeyPatch, manager_index: int, method: str
    ) -> None:
        mocks = _setup(monkeypatch)
        if method == "get_latest_ci_status":
            mocks[3].find_pr.return_value = None  # no open PR → live CI lookup
        # BranchLookupCache.lookup converts rate limits itself.
        limit = GitHubRateLimitError("limited") if method == "lookup" else _rate_limit()
        getattr(mocks[manager_index], method).side_effect = limit
        branch_cache = mocks[1]

        with pytest.raises(GitHubRateLimitError):
            check_pr_health(
                "test-repo", REPO_CONFIG, [_make_pr_issue(1), _make_pr_issue(2)]
            )

        assert branch_cache.lookup.call_count == 1

    def test_escalate_label_limit_propagates(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _, branch_cache, _, pr_cache = _setup(monkeypatch)
        pr_cache.mergeable_state.return_value = "dirty"
        monkeypatch.setattr(
            f"{CHECKS}.update_workflow_label",
            Mock(side_effect=GitHubRateLimitError("limited")),
        )

        with pytest.raises(GitHubRateLimitError):
            check_pr_health(
                "test-repo", REPO_CONFIG, [_make_pr_issue(1), _make_pr_issue(2)]
            )

        assert branch_cache.lookup.call_count == 1

    def test_username_limit_propagates(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _setup(monkeypatch)
        monkeypatch.setattr(
            f"{CHECKS}.get_github_username", Mock(side_effect=_wrapped_rate_limit())
        )

        with pytest.raises(GitHubRateLimitError):
            check_pr_health("test-repo", REPO_CONFIG, [_make_pr_issue(1)])


class TestBuildEligibleIssuesRateLimit:
    """build_eligible_issues_with_branch_check stops on the first rate limit."""

    def _patch(self, monkeypatch: pytest.MonkeyPatch) -> MagicMock:
        config = {
            "coordinator": {
                "repos": {
                    "repo-1": {"repo_url": "https://github.com/owner/one.git"},
                    "repo-2": {"repo_url": "https://github.com/owner/two.git"},
                }
            }
        }
        monkeypatch.setattr(f"{ISSUES}.load_config", lambda: config)
        monkeypatch.setattr(f"{ISSUES}.get_github_username", lambda: "testuser")
        monkeypatch.setattr(f"{ISSUES}.IssueManager", lambda **kw: Mock())
        branch_cache = patch_branch_cache(
            monkeypatch, ISSUES, side_effect=GitHubRateLimitError("limited")
        )
        monkeypatch.setattr(
            f"{ISSUES}.get_issue_status", lambda issue: "status-04:plan-review"
        )
        return branch_cache

    def _cached(self) -> dict[str, dict[int, IssueData]]:
        def issue(number: int) -> IssueData:
            return make_issue_data(
                number=number, labels=["status-04:plan-review"], assignees=["testuser"]
            )

        return {"owner/one": {1: issue(1)}, "owner/two": {2: issue(2)}}

    def test_branch_lookup_limit_stops_before_repo_2(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        branch_cache = self._patch(monkeypatch)

        with pytest.raises(GitHubRateLimitError):
            build_eligible_issues_with_branch_check(
                ["repo-1", "repo-2"], cached_issues_by_repo=self._cached()
            )

        assert branch_cache.lookup.call_count == 1
        branch_cache.save.assert_called_once_with()

    def test_username_limit_propagates(self, monkeypatch: pytest.MonkeyPatch) -> None:
        branch_cache = self._patch(monkeypatch)
        username = Mock(side_effect=_wrapped_rate_limit())
        monkeypatch.setattr(f"{ISSUES}.get_github_username", username)

        with pytest.raises(GitHubRateLimitError):
            build_eligible_issues_with_branch_check(
                ["repo-1", "repo-2"], cached_issues_by_repo=self._cached()
            )

        assert username.call_count == 1
        branch_cache.lookup.assert_not_called()


class TestProcessEligibleIssuesRateLimit:
    """process_eligible_issues stops on the first rate limit."""

    def test_branch_lookup_limit_stops_before_issue_2(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        issues = [
            make_issue_data(
                number=n, labels=["status-01:created"], assignees=["testuser"]
            )
            for n in (1, 2)
        ]
        branch_cache = patch_branch_cache(
            monkeypatch, LAUNCH, side_effect=GitHubRateLimitError("limited")
        )
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

        with pytest.raises(GitHubRateLimitError):
            process_eligible_issues(
                repo_name="test-repo",
                repo_config={"repo_url": "https://github.com/owner/repo"},
                vscodeclaude_config={"workspace_base": "/tmp", "max_sessions": 3},
                max_sessions=3,
                current_count=0,
                all_cached_issues=issues,
            )

        assert branch_cache.lookup.call_count == 1
        branch_cache.save.assert_called_once_with()
        launch.assert_not_called()


class TestRestartClosedSessionsRateLimit:
    """restart_closed_sessions stops on a rate limit in branch preparation."""

    def test_prepare_branch_limit_propagates(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        sessions_file = tmp_path / "sessions.json"
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.get_sessions_file_path",
            lambda: sessions_file,
        )
        folder = tmp_path / "repo_100"
        folder.mkdir()
        (tmp_path / "repo_100.code-workspace").write_text("{}")
        session = {
            "folder": str(folder),
            "repo": "owner/repo",
            "issue_number": 100,
            "status": "status-04:plan-review",
            "vscode_pid": None,
            "started_at": "2024-01-01T00:00:00Z",
            "is_intervention": False,
        }
        sessions_file.write_text(
            json.dumps({"sessions": [session], "last_updated": ""})
        )
        monkeypatch.setattr(f"{RESTART}._get_configured_repos", lambda: {"owner/repo"})
        monkeypatch.setattr(f"{RESTART}.IssueManager", lambda **kw: MagicMock())
        branch_cache = patch_branch_cache(monkeypatch, RESTART)
        monkeypatch.setattr(
            f"{RESTART}._prepare_restart_branch", Mock(side_effect=_rate_limit())
        )
        launch = MagicMock(return_value=9999)
        monkeypatch.setattr(f"{RESTART}.launch_vscode", launch)
        cached: dict[str, dict[int, IssueData]] = {
            "owner/repo": {
                100: make_issue_data(number=100, labels=["status-04:plan-review"])
            }
        }

        with pytest.raises(GitHubRateLimitError):
            restart_closed_sessions(
                assessments={str(folder): make_assessment(str(folder))},
                cached_issues_by_repo=cached,
            )

        launch.assert_not_called()
        branch_cache.save.assert_called_once_with()

    def test_limit_after_restart_keeps_restarted_session(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        sessions_file = tmp_path / "sessions.json"
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.get_sessions_file_path",
            lambda: sessions_file,
        )
        folders = [str(tmp_path / f"repo_{number}") for number in (100, 101)]
        sessions = []
        for number, folder in zip((100, 101), folders, strict=True):
            Path(folder).mkdir()
            (tmp_path / f"repo_{number}.code-workspace").write_text("{}")
            sessions.append(
                {
                    "folder": folder,
                    "repo": "owner/repo",
                    "issue_number": number,
                    "status": "status-04:plan-review",
                    "vscode_pid": None,
                    "started_at": "2024-01-01T00:00:00Z",
                    "is_intervention": False,
                }
            )
        sessions_file.write_text(json.dumps({"sessions": sessions, "last_updated": ""}))
        monkeypatch.setattr(f"{RESTART}._get_configured_repos", lambda: {"owner/repo"})
        monkeypatch.setattr(f"{RESTART}.IssueManager", lambda **kw: MagicMock())
        monkeypatch.setattr(f"{RESTART}.regenerate_session_files", MagicMock())
        patch_branch_cache(monkeypatch, RESTART)
        monkeypatch.setattr(
            f"{RESTART}._prepare_restart_branch",
            Mock(side_effect=[BranchPrepResult(True, None, None), _rate_limit()]),
        )
        launch = MagicMock(return_value=9999)
        monkeypatch.setattr(f"{RESTART}.launch_vscode", launch)
        cached: dict[str, dict[int, IssueData]] = {
            "owner/repo": {
                n: make_issue_data(number=n, labels=["status-04:plan-review"])
                for n in (100, 101)
            }
        }
        restarted: list[VSCodeClaudeSession] = []

        with pytest.raises(GitHubRateLimitError):
            restart_closed_sessions(
                assessments={f: make_assessment(f) for f in folders},
                cached_issues_by_repo=cached,
                restarted=restarted,
            )

        launch.assert_called_once()
        assert [s["issue_number"] for s in restarted] == [100]
        assert restarted[0]["vscode_pid"] == 9999


class TestAssessmentRateLimit:
    """assessment.py re-raises rate limits from its GitHub calls."""

    def test_fetch_issue_individually_limit_propagates(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(f"{ASSESSMENT}.IssueManager", lambda **kw: Mock())
        monkeypatch.setattr(
            f"{ASSESSMENT}.get_all_cached_issues", Mock(side_effect=_rate_limit())
        )

        with pytest.raises(GitHubRateLimitError):
            _fetch_issue_individually("owner/repo", 7)

    def test_fetch_issue_individually_other_error_returns_none(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(f"{ASSESSMENT}.IssueManager", lambda **kw: Mock())
        monkeypatch.setattr(
            f"{ASSESSMENT}.get_all_cached_issues",
            Mock(side_effect=RuntimeError("boom")),
        )

        assert _fetch_issue_individually("owner/repo", 7) is None

    @patch(f"{ASSESSMENT}.capture_detection_snapshot")
    @patch(f"{ASSESSMENT}.get_ignore_labels", return_value=set())
    def test_build_assessments_username_limit_propagates(
        self, mock_ignore: object, mock_snap: object
    ) -> None:
        cached: dict[str, dict[int, IssueData]] = {
            "owner/repo": {42: make_issue_data(number=42)}
        }
        with patch(
            f"{ASSESSMENT}.get_github_username",
            side_effect=_wrapped_rate_limit(),
        ):
            with pytest.raises(GitHubRateLimitError):
                build_assessments([make_session_at("C:/work/a", 42)], cached)


class TestFetchMarkedCommentRateLimit:
    """_fetch_marked_comment keeps swallowing rate limits (WARNING)."""

    def test_rate_limit_returns_none_with_warning(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        manager = Mock()
        manager.get_comments.side_effect = _rate_limit()
        monkeypatch.setattr(f"{WORKSPACE}.IssueManager", lambda **kw: manager)

        with caplog.at_level(logging.WARNING):
            assert _fetch_marked_comment(tmp_path, 5) is None

        assert "Failed to fetch issue comments for #5" in caplog.text
