"""Tests for PR-health checks on status-10 issues (checks.py)."""

import logging
from typing import Any
from unittest.mock import MagicMock

import pytest

from mcp_coder.mcp_workspace_github import (
    BranchLookup,
    BranchLookupError,
    IssueData,
    OpenPullRequest,
)
from mcp_coder.utils.log_utils import OUTPUT
from mcp_coder.workflows.vscodeclaude.checks import (
    _check_ci,
    _check_merge_conflict,
    _resolve_pr_target,
    check_pr_health,
)
from tests.github_factories import make_issue_data

CHECKS = "mcp_coder.workflows.vscodeclaude.checks"
ISSUES = "mcp_coder.workflows.vscodeclaude.issues"
REPO_CONFIG = {"repo_url": "https://github.com/owner/repo"}

MOCK_MERGE_CONFLICT_LABELS_CONFIG: dict[str, Any] = {
    "workflow_labels": [
        {
            "internal_id": "pr_created",
            "name": "status-10:pr-created",
            "color": "8b5cf6",
            "description": "Pull request created, awaiting approval/merge",
            "category": "human_action",
        },
        {
            "internal_id": "merge_conflict",
            "name": "status-71:merge-conflict",
            "color": "fda4af",
            "description": "PR is no longer cleanly mergeable against its base",
            "category": "bot_pickup",
        },
    ],
    "ignore_labels": [],
}

MOCK_CI_LABELS_CONFIG: dict[str, Any] = {
    "workflow_labels": [
        {
            "internal_id": "pr_created",
            "name": "status-10:pr-created",
            "color": "8b5cf6",
            "description": "Pull request created, awaiting approval/merge",
            "category": "human_action",
        },
        {
            "internal_id": "merge_conflict",
            "name": "status-71:merge-conflict",
            "color": "fda4af",
            "description": "PR is no longer cleanly mergeable against its base",
            "category": "bot_pickup",
        },
        {
            "internal_id": "failing_ci",
            "name": "status-81:failing-ci",
            "color": "f87171",
            "description": "PR's latest CI run failed",
            "category": "bot_pickup",
        },
    ],
    "ignore_labels": [],
}


def _make_pr_issue(number: int, labels: list[str] | None = None) -> IssueData:
    return make_issue_data(
        number=number,
        title="PR Created Issue",
        labels=labels if labels is not None else ["status-10:pr-created"],
        assignees=["testuser"],
    )


def _make_pr(number: int = 1) -> OpenPullRequest:
    return {
        "number": number,
        "head_branch": f"{number}-fix",
        "head_sha": "abc123",
        "head_label": f"owner:{number}-fix",
        "base_branch": "main",
        "updated_at": None,
        "user": "owner",
        "author_association": "OWNER",
        "draft": False,
    }


def _empty_feedback() -> dict[str, Any]:
    return {
        "unresolved_threads": [],
        "resolved_thread_count": 0,
        "changes_requested": [],
        "conversation_comments": [],
        "alerts": [],
        "unavailable": {},
    }


def _default_mocks() -> tuple[MagicMock, MagicMock, MagicMock, MagicMock]:
    """Build the issue/branch/CI manager mocks and the ``PullRequestCache`` mock."""
    issue_manager = MagicMock()
    issue_manager.project_dir = None
    issue_manager.transition_issue_label.return_value = True
    branch_cache = MagicMock()
    branch_cache.lookup.return_value = BranchLookup("found", "999-fix")
    ci_manager = MagicMock()
    ci_manager.get_latest_ci_status.return_value = {"run": {}, "jobs": []}
    pr_cache = MagicMock()
    pr_cache.find_pr.return_value = _make_pr()
    pr_cache.mergeable_state.return_value = "clean"
    pr_cache.ci_status.return_value = {"run": {}, "jobs": []}
    pr_cache.feedback.return_value = _empty_feedback()
    pr_cache.label_events.return_value = []
    return issue_manager, branch_cache, ci_manager, pr_cache


def _patch_env(
    monkeypatch: pytest.MonkeyPatch,
    *,
    issue_manager: MagicMock,
    branch_cache: MagicMock,
    ci_manager: MagicMock,
    pr_cache: MagicMock,
    labels_config: dict[str, Any] | None = None,
) -> MagicMock:
    """Patch the managers, the PR and branch caches and config lookups.

    Returns:
        The ``get_trusted_commenters`` mock (returns an empty allowlist).
    """
    config = MOCK_CI_LABELS_CONFIG if labels_config is None else labels_config
    get_trusted = MagicMock(return_value=frozenset())
    monkeypatch.setattr(f"{CHECKS}.get_trusted_commenters", get_trusted)
    monkeypatch.setattr(f"{CHECKS}.IssueManager", lambda **kw: issue_manager)
    monkeypatch.setattr(f"{CHECKS}.IssueBranchManager", lambda **kw: MagicMock())
    monkeypatch.setattr(f"{CHECKS}.CIResultsManager", lambda **kw: ci_manager)
    monkeypatch.setattr(f"{CHECKS}.PullRequestManager", lambda **kw: MagicMock())
    cache_cls = MagicMock()
    cache_cls.load.return_value = pr_cache
    monkeypatch.setattr(f"{CHECKS}.PullRequestCache", cache_cls)
    branch_cache_cls = MagicMock()
    branch_cache_cls.load.return_value = branch_cache
    monkeypatch.setattr(f"{CHECKS}.BranchLookupCache", branch_cache_cls)
    monkeypatch.setattr(f"{CHECKS}.get_github_username", lambda: "testuser")
    monkeypatch.setattr(
        f"{CHECKS}._filter_eligible_vscodeclaude_issues", lambda issues, user: issues
    )
    monkeypatch.setattr(
        "mcp_coder.workflow_utils.label_transitions.load_labels_config",
        lambda *a, **k: config,
    )
    return get_trusted


def _setup(
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[MagicMock, MagicMock, MagicMock, MagicMock]:
    """Patch the environment with default mocks.

    Returns:
        ``(issue_manager, branch_cache, ci_manager, pr_cache)``.
    """
    mocks = _default_mocks()
    issue_manager, branch_cache, ci_manager, pr_cache = mocks
    _patch_env(
        monkeypatch,
        issue_manager=issue_manager,
        branch_cache=branch_cache,
        ci_manager=ci_manager,
        pr_cache=pr_cache,
    )
    return mocks


def _run(issue: IssueData) -> None:
    check_pr_health("test-repo", REPO_CONFIG, [issue])


class TestCheckPrHealth:
    """Tests for check_pr_health() orchestration."""

    def test_dirty_pr_transitions_to_merge_conflict(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A status-10 issue whose PR is dirty gets escalated to status-71."""
        issue_manager, _, _, pr_cache = _setup(monkeypatch)
        pr_cache.mergeable_state.return_value = "dirty"

        _run(_make_pr_issue(999))

        issue_manager.transition_issue_label.assert_called_once()
        call_args = issue_manager.transition_issue_label.call_args
        assert call_args[0][0] == 999
        assert call_args[0][1] == "status-71:merge-conflict"

    def test_clean_pr_green_ci_no_feedback_does_not_transition(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A clean PR with green CI and no feedback is left untouched."""
        issue_manager, _, _, pr_cache = _setup(monkeypatch)
        pr_cache.ci_status.return_value = {
            "run": {"status": "completed", "conclusion": "success"},
            "jobs": [],
        }

        _run(_make_pr_issue(998))

        issue_manager.transition_issue_label.assert_not_called()

    def test_failed_ci_run_transitions_to_failing_ci(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A status-10 issue whose latest CI run failed gets escalated to status-81."""
        issue_manager, _, _, pr_cache = _setup(monkeypatch)
        pr_cache.ci_status.return_value = {
            "run": {"status": "completed", "conclusion": "failure"},
            "jobs": [],
        }

        _run(_make_pr_issue(995))

        issue_manager.transition_issue_label.assert_called_once()
        call_args = issue_manager.transition_issue_label.call_args
        assert call_args[0][0] == 995
        assert call_args[0][1] == "status-81:failing-ci"

    @pytest.mark.parametrize(
        "run",
        [
            {"status": "completed", "conclusion": "success"},
            {"status": "in_progress", "conclusion": None},
        ],
    )
    def test_successful_or_pending_ci_does_not_transition(
        self, monkeypatch: pytest.MonkeyPatch, run: dict[str, Any]
    ) -> None:
        """A successful or still-running CI run is left untouched."""
        issue_manager, _, _, pr_cache = _setup(monkeypatch)
        pr_cache.ci_status.return_value = {"run": run, "jobs": []}

        _run(_make_pr_issue(994))

        issue_manager.transition_issue_label.assert_not_called()

    def test_ci_status_exception_is_swallowed(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A CI status exception is swallowed; it does not raise."""
        issue_manager, _, _, pr_cache = _setup(monkeypatch)
        pr_cache.ci_status.side_effect = RuntimeError("GitHub API boom")

        _run(_make_pr_issue(991))

        issue_manager.transition_issue_label.assert_not_called()

    def test_dirty_pr_skips_ci_and_review_checks(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A dirty PR never reaches the CI check or the review-comments check."""
        _, _, ci_manager, pr_cache = _setup(monkeypatch)
        pr_cache.mergeable_state.return_value = "dirty"

        _run(_make_pr_issue(990))

        pr_cache.ci_status.assert_not_called()
        ci_manager.get_latest_ci_status.assert_not_called()
        pr_cache.feedback.assert_not_called()

    def test_failed_ci_skips_review_check(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A failing CI run never reaches the review-comments check."""
        _, _, _, pr_cache = _setup(monkeypatch)
        pr_cache.ci_status.return_value = {
            "run": {"status": "completed", "conclusion": "failure"},
            "jobs": [],
        }

        _run(_make_pr_issue(989))

        pr_cache.feedback.assert_not_called()

    def test_no_branch_skips_pr_and_ci_lookups(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """An issue with no resolvable branch calls neither the PR nor the CI API."""
        issue_manager, branch_cache, ci_manager, pr_cache = _setup(monkeypatch)
        branch_cache.lookup.return_value = BranchLookup("not_found")

        _run(_make_pr_issue(997))

        pr_cache.find_pr.assert_not_called()
        pr_cache.ci_status.assert_not_called()
        ci_manager.get_latest_ci_status.assert_not_called()
        issue_manager.transition_issue_label.assert_not_called()

    def test_no_pr_found_checks_ci_live(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """No open PR: CI is checked live, conflict and review are not."""
        issue_manager, _, ci_manager, pr_cache = _setup(monkeypatch)
        pr_cache.find_pr.return_value = None

        _run(_make_pr_issue(988))

        ci_manager.get_latest_ci_status.assert_called_once_with("999-fix")
        pr_cache.ci_status.assert_not_called()
        pr_cache.mergeable_state.assert_not_called()
        pr_cache.feedback.assert_not_called()
        issue_manager.transition_issue_label.assert_not_called()

    def test_non_status_10_issues_build_no_managers(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Without status-10 issues no manager or cache is built."""
        _setup(monkeypatch)
        mock_issue_manager_cls = MagicMock()
        mock_branch_manager_cls = MagicMock()
        mock_ci_manager_cls = MagicMock()
        mock_pr_manager_cls = MagicMock()
        mock_cache_cls = MagicMock()
        mock_branch_cache_cls = MagicMock()
        monkeypatch.setattr(f"{CHECKS}.IssueManager", mock_issue_manager_cls)
        monkeypatch.setattr(f"{CHECKS}.IssueBranchManager", mock_branch_manager_cls)
        monkeypatch.setattr(f"{CHECKS}.CIResultsManager", mock_ci_manager_cls)
        monkeypatch.setattr(f"{CHECKS}.PullRequestManager", mock_pr_manager_cls)
        monkeypatch.setattr(f"{CHECKS}.PullRequestCache", mock_cache_cls)
        monkeypatch.setattr(f"{CHECKS}.BranchLookupCache", mock_branch_cache_cls)

        _run(_make_pr_issue(123, labels=["status-01:created"]))

        mock_issue_manager_cls.assert_not_called()
        mock_branch_manager_cls.assert_not_called()
        mock_ci_manager_cls.assert_not_called()
        mock_pr_manager_cls.assert_not_called()
        mock_cache_cls.load.assert_not_called()
        mock_branch_cache_cls.load.assert_not_called()

    def test_setup_failure_logs_warning_and_does_not_raise(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        """A setup failure (username lookup) is swallowed with a warning."""
        _setup(monkeypatch)

        def _raise() -> str:
            raise RuntimeError("no token")

        monkeypatch.setattr(f"{CHECKS}.get_github_username", _raise)

        with caplog.at_level(logging.WARNING, logger=CHECKS):
            _run(_make_pr_issue(987))

        assert any(
            record.levelno == logging.WARNING and "test-repo" in record.getMessage()
            for record in caplog.records
        )

    def test_one_lookup_per_issue(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Branch and PR are each looked up exactly once per issue."""
        _, branch_cache, _, pr_cache = _setup(monkeypatch)

        _run(_make_pr_issue(986))

        branch_cache.lookup.assert_called_once()
        pr_cache.find_pr.assert_called_once_with("999-fix")

    def test_trusted_commenters_read_once_per_poll(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The allowlist is read once per check_pr_health call, not per issue."""
        issue_manager, branch_cache, ci_manager, pr_cache = _default_mocks()
        get_trusted = _patch_env(
            monkeypatch,
            issue_manager=issue_manager,
            branch_cache=branch_cache,
            ci_manager=ci_manager,
            pr_cache=pr_cache,
        )

        check_pr_health(
            "test-repo", REPO_CONFIG, [_make_pr_issue(984), _make_pr_issue(985)]
        )

        get_trusted.assert_called_once_with()
        assert pr_cache.feedback.call_count == 2


class TestResolvePrTarget:
    """Tests for _resolve_pr_target()."""

    def test_branch_lookup_raises_returns_none_none(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """A branch-lookup exception yields (None, None) and a warning."""
        branch_cache = MagicMock()
        branch_cache.lookup.side_effect = BranchLookupError("boom")
        pr_cache = MagicMock()

        with caplog.at_level(logging.WARNING, logger=ISSUES):
            result = _resolve_pr_target(_make_pr_issue(1), branch_cache, pr_cache)

        assert result == (None, None)
        assert any(r.levelno == logging.WARNING for r in caplog.records)
        pr_cache.find_pr.assert_not_called()

    def test_no_branch_returns_none_none(self) -> None:
        """No resolvable branch yields (None, None) without a PR lookup."""
        branch_cache = MagicMock()
        branch_cache.lookup.return_value = BranchLookup("ambiguous")
        pr_cache = MagicMock()

        result = _resolve_pr_target(_make_pr_issue(2), branch_cache, pr_cache)

        assert result == (None, None)
        pr_cache.find_pr.assert_not_called()

    def test_pr_lookup_raises_returns_branch_none(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """A PR-lookup exception yields (branch, None) and a warning."""
        branch_cache = MagicMock()
        branch_cache.lookup.return_value = BranchLookup("found", "3-fix")
        pr_cache = MagicMock()
        pr_cache.find_pr.side_effect = RuntimeError("boom")

        with caplog.at_level(logging.WARNING, logger=CHECKS):
            result = _resolve_pr_target(_make_pr_issue(3), branch_cache, pr_cache)

        assert result == ("3-fix", None)
        assert any(r.levelno == logging.WARNING for r in caplog.records)

    def test_no_pr_returns_branch_none(self) -> None:
        """No PR for the branch yields (branch, None)."""
        branch_cache = MagicMock()
        branch_cache.lookup.return_value = BranchLookup("found", "4-fix")
        pr_cache = MagicMock()
        pr_cache.find_pr.return_value = None

        result = _resolve_pr_target(_make_pr_issue(4), branch_cache, pr_cache)

        assert result == ("4-fix", None)

    def test_pr_found_returns_branch_and_pr(self) -> None:
        """A found PR yields (branch, pr)."""
        branch_cache = MagicMock()
        branch_cache.lookup.return_value = BranchLookup("found", "5-fix")
        pr_cache = MagicMock()
        pr = _make_pr(7)
        pr_cache.find_pr.return_value = pr

        result = _resolve_pr_target(_make_pr_issue(5), branch_cache, pr_cache)

        assert result == ("5-fix", pr)
        pr_cache.find_pr.assert_called_once_with("5-fix")

    def test_pr_lookup_raises_still_checks_ci_via_check_pr_health(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A PR-lookup failure still runs the live CI check, but no PR-based check."""
        issue_manager, _, ci_manager, pr_cache = _setup(monkeypatch)
        pr_cache.find_pr.side_effect = RuntimeError("boom")

        _run(_make_pr_issue(6))

        ci_manager.get_latest_ci_status.assert_called_once_with("999-fix")
        pr_cache.feedback.assert_not_called()
        issue_manager.transition_issue_label.assert_not_called()


class TestCheckCi:
    """Tests for _check_ci()'s bool return value."""

    def _mocks(
        self, monkeypatch: pytest.MonkeyPatch, run_status: dict[str, Any]
    ) -> tuple[MagicMock, MagicMock, MagicMock]:
        ci_manager = MagicMock()
        ci_manager.get_latest_ci_status.return_value = run_status
        pr_cache = MagicMock()
        pr_cache.ci_status.return_value = run_status
        issue_manager = MagicMock()
        issue_manager.project_dir = None
        issue_manager.transition_issue_label.return_value = True
        monkeypatch.setattr(
            "mcp_coder.workflow_utils.label_transitions.load_labels_config",
            lambda *a, **k: MOCK_CI_LABELS_CONFIG,
        )
        return ci_manager, pr_cache, issue_manager

    def _call(
        self,
        ci_manager: MagicMock,
        pr_cache: MagicMock,
        issue_manager: MagicMock,
        pr: OpenPullRequest | None = None,
        issue: IssueData | None = None,
    ) -> bool:
        return _check_ci(
            issue or _make_pr_issue(123),
            "123-fix",
            pr,
            pr_cache,
            ci_manager,
            issue_manager,
            "test-repo",
            "status-81:failing-ci",
        )

    def test_returns_true_when_ci_failed(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A failed CI run returns True."""
        ci_manager, pr_cache, issue_manager = self._mocks(
            monkeypatch,
            {"run": {"status": "completed", "conclusion": "failure"}, "jobs": []},
        )

        assert self._call(ci_manager, pr_cache, issue_manager) is True
        ci_manager.get_latest_ci_status.assert_called_once_with("123-fix")

    def test_with_pr_uses_cache(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """With an open PR the status comes from the cache, not the live API."""
        ci_manager, pr_cache, issue_manager = self._mocks(
            monkeypatch,
            {"run": {"status": "completed", "conclusion": "failure"}, "jobs": []},
        )
        pr = _make_pr(123)
        issue = _make_pr_issue(123)

        assert self._call(ci_manager, pr_cache, issue_manager, pr, issue) is True
        pr_cache.ci_status.assert_called_once_with(pr, issue)
        ci_manager.get_latest_ci_status.assert_not_called()

    def test_returns_false_when_ci_successful(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A successful CI run returns False."""
        ci_manager, pr_cache, issue_manager = self._mocks(
            monkeypatch,
            {"run": {"status": "completed", "conclusion": "success"}, "jobs": []},
        )

        assert self._call(ci_manager, pr_cache, issue_manager) is False

    def test_returns_false_when_ci_pending(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A still-running CI run returns False."""
        ci_manager, pr_cache, issue_manager = self._mocks(
            monkeypatch,
            {"run": {"status": "in_progress", "conclusion": None}, "jobs": []},
        )

        assert self._call(ci_manager, pr_cache, issue_manager) is False

    def test_returns_false_on_exception(self) -> None:
        """A CIResultsManager exception is swallowed and returns False."""
        ci_manager = MagicMock()
        ci_manager.get_latest_ci_status.side_effect = RuntimeError("boom")

        assert self._call(ci_manager, MagicMock(), MagicMock()) is False


class TestPrHealthOutput:
    """Tests for the OUTPUT line logged on escalation."""

    def _output_records(
        self, caplog: pytest.LogCaptureFixture
    ) -> list[logging.LogRecord]:
        return [r for r in caplog.records if r.levelno == OUTPUT]

    def test_escalation_logs_one_output_line(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        """An escalation logs exactly one OUTPUT line naming repo, issue and label."""
        _, _, _, pr_cache = _setup(monkeypatch)
        pr_cache.mergeable_state.return_value = "dirty"

        with caplog.at_level(OUTPUT, logger=CHECKS):
            _run(_make_pr_issue(999))

        records = self._output_records(caplog)
        assert len(records) == 1
        assert (
            records[0].getMessage()
            == "PR-health: test-repo #999 → status-71:merge-conflict"
        )

    def test_no_escalation_logs_no_output_line(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        """No escalation logs no OUTPUT line."""
        _setup(monkeypatch)

        with caplog.at_level(OUTPUT, logger=CHECKS):
            _run(_make_pr_issue(998))

        assert not self._output_records(caplog)

    def test_failed_label_update_logs_no_output_line(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        """A failed label update logs no OUTPUT line; the check still reports a hit."""
        issue_manager = MagicMock()
        issue_manager.project_dir = None
        issue_manager.transition_issue_label.return_value = False
        pr_cache = MagicMock()
        pr_cache.mergeable_state.return_value = "dirty"
        monkeypatch.setattr(
            "mcp_coder.workflow_utils.label_transitions.load_labels_config",
            lambda *a, **k: MOCK_MERGE_CONFLICT_LABELS_CONFIG,
        )

        with caplog.at_level(OUTPUT, logger=CHECKS):
            result = _check_merge_conflict(
                _make_pr_issue(999),
                _make_pr(),
                pr_cache,
                issue_manager,
                "test-repo",
                "status-71:merge-conflict",
            )

        assert result is True
        issue_manager.transition_issue_label.assert_called_once()
        assert not self._output_records(caplog)
