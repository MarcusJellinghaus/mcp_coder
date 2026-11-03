"""Tests for the auto-merge workflow step (run_auto_merge and helpers)."""

from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.mcp_workspace_github import GithubException, GitHubRateLimitError
from mcp_coder.workflow_steps.merge import (
    MergeOutcome,
    is_real_green,
    resolve_merge_issue_number,
    run_auto_merge,
)
from mcp_coder.workflow_steps.rebase import RebaseOutcome

_MODULE = "mcp_coder.workflow_steps.merge"
_PROJECT = Path("/fake/project")
_BRANCH = "123-feature"
_SHA = "a" * 40
_NEW_SHA = "b" * 40


def _pr(head_sha: str | None = _SHA) -> dict[str, Any]:
    return {"number": 7, "title": "Add feature", "head_sha": head_sha}


def _green(sha: str | None = _SHA) -> dict[str, Any]:
    return {"run": {"commit_sha": sha, "conclusion": "success"}, "jobs": []}


def _merge(outcome: str, status: int | None, message: str = "msg") -> dict[str, Any]:
    return {
        "merged": outcome == "merged",
        "outcome": outcome,
        "sha": None,
        "message": message,
        "status": status,
    }


MERGED = _merge("merged", 200)
REFUSED_405 = _merge("refused", 405, "not mergeable")


@dataclass
class Mocks:
    """Patched collaborators of run_auto_merge."""

    pr_manager: MagicMock
    latest_sha: MagicMock
    poll_ci: MagicMock
    poll_state: MagicMock
    rebase: MagicMock
    reset_hard: MagicMock
    ci_manager: MagicMock = field(default_factory=MagicMock)


@pytest.fixture(name="mocks")
def _mocks() -> Iterator[Mocks]:
    pr_manager = MagicMock()
    pr_manager.find_pull_request_by_head.return_value = [_pr()]
    pr_manager.merge_pull_request.return_value = MERGED
    with (
        patch(f"{_MODULE}.PullRequestManager", return_value=pr_manager),
        patch(f"{_MODULE}.CIResultsManager") as ci_cls,
        patch(f"{_MODULE}.get_latest_commit_sha", return_value=_SHA) as latest_sha,
        patch(
            f"{_MODULE}._poll_for_ci_completion", return_value=(_green(), True)
        ) as poll_ci,
        patch(f"{_MODULE}._poll_mergeable_state", return_value="dirty") as poll_state,
        patch(
            f"{_MODULE}._attempt_rebase_and_push",
            return_value=RebaseOutcome("ok", "main", "1234567"),
        ) as rebase,
        patch(f"{_MODULE}._reset_hard", return_value=True) as reset_hard,
    ):
        yield Mocks(
            pr_manager=pr_manager,
            latest_sha=latest_sha,
            poll_ci=poll_ci,
            poll_state=poll_state,
            rebase=rebase,
            reset_hard=reset_hard,
            ci_manager=ci_cls.return_value,
        )


def _fields(outcome: MergeOutcome) -> dict[str, str | None]:
    return dict(outcome.comment_fields)


class TestIsRealGreen:
    """is_real_green requires a green run for exactly the expected commit."""

    @pytest.mark.parametrize(
        ("ci_status", "ci_ok", "expected_sha", "expected"),
        [
            pytest.param(_green(), True, _SHA, True, id="green_on_sha"),
            pytest.param(None, True, _SHA, False, id="soft_pass"),
            pytest.param(_green(), False, _SHA, False, id="red"),
            pytest.param(_green(_NEW_SHA), True, _SHA, False, id="other_sha"),
            pytest.param(_green(None), True, _SHA, False, id="run_without_sha"),
            pytest.param({}, True, _SHA, False, id="no_run"),
            pytest.param(_green(), True, None, False, id="no_expected_sha"),
        ],
    )
    def test_is_real_green(
        self,
        ci_status: dict[str, Any] | None,
        ci_ok: bool,
        expected_sha: str | None,
        expected: bool,
    ) -> None:
        assert is_real_green(ci_status, ci_ok, expected_sha) is expected  # type: ignore[arg-type]


class TestResolveMergeIssueNumber:
    """resolve_merge_issue_number never raises and skips unlinked branches."""

    @pytest.mark.parametrize(
        ("number", "linked", "expected"),
        [
            pytest.param(123, True, 123, id="linked"),
            pytest.param(123, None, 123, id="lookup_failed"),
            pytest.param(123, RuntimeError("boom"), 123, id="lookup_raised"),
            pytest.param(123, False, None, id="unlinked"),
            pytest.param(None, True, None, id="no_number"),
        ],
    )
    def test_resolve(
        self, number: int | None, linked: object, expected: int | None
    ) -> None:
        link_kwargs: dict[str, Any] = (
            {"side_effect": linked}
            if isinstance(linked, Exception)
            else {"return_value": linked}
        )
        with (
            patch(
                f"{_MODULE}.extract_issue_number_from_branch", return_value=number
            ) as extract,
            patch(f"{_MODULE}.IssueBranchManager") as branch_mgr_cls,
            patch(f"{_MODULE}.is_branch_linked_to_issue", **link_kwargs) as is_linked,
        ):
            result = resolve_merge_issue_number(_PROJECT, _BRANCH)

        assert result == expected
        extract.assert_called_once_with(_BRANCH)
        if number is None:
            is_linked.assert_not_called()
        else:
            branch_mgr_cls.assert_called_once_with(project_dir=_PROJECT)
            is_linked.assert_called_once_with(
                branch_mgr_cls.return_value, number, _BRANCH
            )


class TestRunAutoMergeStep0:
    """Step 0: exactly one PR with a head SHA, else pr_created without merge."""

    @pytest.mark.parametrize(
        "prs",
        [
            pytest.param([], id="no_pr"),
            pytest.param([_pr(), _pr()], id="two_prs"),
            pytest.param([_pr(None)], id="no_head_sha"),
        ],
    )
    def test_no_single_pr(self, mocks: Mocks, prs: list[dict[str, Any]]) -> None:
        mocks.pr_manager.find_pull_request_by_head.return_value = prs

        outcome = run_auto_merge(_PROJECT, _BRANCH)

        assert outcome == MergeOutcome("pr_created")
        mocks.pr_manager.merge_pull_request.assert_not_called()
        mocks.poll_ci.assert_not_called()


class TestRunAutoMergeStep1:
    """Step 1: real green on HEAD, then head-SHA re-check."""

    def test_red_ci_is_failing_ci(self, mocks: Mocks) -> None:
        mocks.poll_ci.return_value = (_green(), False)

        outcome = run_auto_merge(_PROJECT, _BRANCH)

        assert outcome == MergeOutcome("failing_ci")
        mocks.pr_manager.merge_pull_request.assert_not_called()

    @pytest.mark.parametrize(
        "ci_result",
        [
            pytest.param((None, True), id="soft_pass"),
            pytest.param((_green(_NEW_SHA), True), id="green_other_sha"),
            pytest.param((_green(None), True), id="green_no_sha"),
        ],
    )
    def test_not_real_green_is_pr_created(
        self, mocks: Mocks, ci_result: tuple[dict[str, Any] | None, bool]
    ) -> None:
        mocks.poll_ci.return_value = ci_result

        outcome = run_auto_merge(_PROJECT, _BRANCH)

        assert outcome == MergeOutcome("pr_created")
        mocks.pr_manager.merge_pull_request.assert_not_called()

    def test_polls_ci_with_expected_sha(self, mocks: Mocks) -> None:
        run_auto_merge(_PROJECT, _BRANCH)

        mocks.poll_ci.assert_called_once_with(
            mocks.ci_manager, _BRANCH, expected_sha=_SHA
        )

    def test_verified_sha_skips_ci_poll(self, mocks: Mocks) -> None:
        outcome = run_auto_merge(_PROJECT, _BRANCH, verified_sha=_SHA)

        assert outcome == MergeOutcome("merged")
        mocks.poll_ci.assert_not_called()
        mocks.latest_sha.assert_not_called()

    def test_head_mismatch_is_pr_created(self, mocks: Mocks) -> None:
        mocks.pr_manager.find_pull_request_by_head.side_effect = [
            [_pr()],
            [_pr(_NEW_SHA)],
        ]

        outcome = run_auto_merge(_PROJECT, _BRANCH)

        assert outcome == MergeOutcome("pr_created")
        mocks.pr_manager.merge_pull_request.assert_not_called()


class TestRunAutoMergeStep2:
    """Step 2: squash merge with the sha= guard."""

    def test_merged(self, mocks: Mocks) -> None:
        outcome = run_auto_merge(_PROJECT, _BRANCH)

        assert outcome == MergeOutcome("merged")
        mocks.pr_manager.merge_pull_request.assert_called_once_with(
            7, "squash", sha=_SHA, commit_title="Add feature (#7)"
        )
        mocks.poll_state.assert_not_called()

    def test_409_is_merge_failed_without_poll(self, mocks: Mocks) -> None:
        mocks.pr_manager.merge_pull_request.return_value = _merge(
            "refused", 409, "head moved"
        )

        outcome = run_auto_merge(_PROJECT, _BRANCH)

        assert outcome.label_id == "merge_failed"
        assert _fields(outcome) == {
            "Stage": "Auto-merge",
            "Error": "head moved",
            "Merge outcome": "refused",
            "HTTP status": "409",
            "Mergeable state": None,
        }
        mocks.poll_state.assert_not_called()
        mocks.rebase.assert_not_called()

    def test_refused_blocked_is_merge_failed_with_state(self, mocks: Mocks) -> None:
        mocks.pr_manager.merge_pull_request.return_value = REFUSED_405
        mocks.poll_state.return_value = "blocked"

        outcome = run_auto_merge(_PROJECT, _BRANCH)

        assert outcome.label_id == "merge_failed"
        assert _fields(outcome)["Mergeable state"] == "blocked"
        assert _fields(outcome)["HTTP status"] == "405"
        mocks.poll_state.assert_called_once_with(_PROJECT, _BRANCH)
        mocks.rebase.assert_not_called()

    def test_error_429_is_pr_created(self, mocks: Mocks) -> None:
        mocks.pr_manager.merge_pull_request.return_value = _merge("error", 429)

        outcome = run_auto_merge(_PROJECT, _BRANCH)

        assert outcome == MergeOutcome("pr_created")

    @pytest.mark.parametrize(
        ("status", "expected_status_field"),
        [pytest.param(500, "500", id="500"), pytest.param(None, None, id="network")],
    )
    def test_error_is_merge_failed(
        self, mocks: Mocks, status: int | None, expected_status_field: str | None
    ) -> None:
        mocks.pr_manager.merge_pull_request.return_value = _merge(
            "error", status, "server error"
        )

        outcome = run_auto_merge(_PROJECT, _BRANCH)

        assert outcome.label_id == "merge_failed"
        assert _fields(outcome)["Merge outcome"] == "error"
        assert _fields(outcome)["HTTP status"] == expected_status_field
        assert _fields(outcome)["Error"] == "server error"
        mocks.poll_state.assert_not_called()


class TestRunAutoMergeStep3:
    """Step 3: one mechanical rebase on dirty/behind, then one retry."""

    @pytest.mark.parametrize("state", ["dirty", "behind"])
    def test_rebase_then_merged(self, mocks: Mocks, state: str) -> None:
        mocks.pr_manager.merge_pull_request.side_effect = [REFUSED_405, MERGED]
        mocks.poll_state.return_value = state
        mocks.pr_manager.find_pull_request_by_head.side_effect = [
            [_pr()],
            [_pr()],
            [_pr(_NEW_SHA)],
        ]
        # 1st: before rebase; 2nd: new HEAD after rebase (re-poll CI)
        mocks.latest_sha.side_effect = [_SHA, _NEW_SHA]
        mocks.poll_ci.return_value = (_green(_NEW_SHA), True)

        outcome = run_auto_merge(_PROJECT, _BRANCH, verified_sha=_SHA)

        assert outcome == MergeOutcome("merged")
        mocks.rebase.assert_called_once_with(_PROJECT)
        mocks.poll_ci.assert_called_once_with(
            mocks.ci_manager, _BRANCH, expected_sha=_NEW_SHA
        )
        second = mocks.pr_manager.merge_pull_request.call_args_list[1]
        assert second.kwargs["sha"] == _NEW_SHA

    def test_rebase_then_red_ci_is_failing_ci(self, mocks: Mocks) -> None:
        mocks.pr_manager.merge_pull_request.return_value = REFUSED_405
        mocks.latest_sha.side_effect = [_SHA, _NEW_SHA]
        mocks.poll_ci.return_value = (_green(_NEW_SHA), False)

        outcome = run_auto_merge(_PROJECT, _BRANCH, verified_sha=_SHA)

        assert outcome == MergeOutcome("failing_ci")
        assert mocks.pr_manager.merge_pull_request.call_count == 1

    def test_retry_refused_is_merge_failed_no_second_rebase(self, mocks: Mocks) -> None:
        mocks.pr_manager.merge_pull_request.return_value = REFUSED_405
        mocks.pr_manager.find_pull_request_by_head.side_effect = [
            [_pr()],
            [_pr()],
            [_pr(_NEW_SHA)],
        ]
        mocks.latest_sha.side_effect = [_SHA, _NEW_SHA]
        mocks.poll_ci.return_value = (_green(_NEW_SHA), True)

        outcome = run_auto_merge(_PROJECT, _BRANCH, verified_sha=_SHA)

        assert outcome.label_id == "merge_failed"
        assert _fields(outcome)["Mergeable state"] is None
        assert mocks.pr_manager.merge_pull_request.call_count == 2
        mocks.rebase.assert_called_once()
        mocks.poll_state.assert_called_once()

    def test_rebase_conflict_is_pr_merge_conflict(self, mocks: Mocks) -> None:
        mocks.pr_manager.merge_pull_request.return_value = REFUSED_405
        mocks.rebase.return_value = RebaseOutcome(
            "conflict", "main", "1234567", ("a.py", "b.py")
        )

        outcome = run_auto_merge(_PROJECT, _BRANCH, verified_sha=_SHA)

        assert outcome.label_id == "pr_merge_conflict"
        assert _fields(outcome) == {
            "Stage": "Auto-merge rebase",
            "Reason": "conflict",
            "Base": "main",
            "Likely conflicting files": "a.py, b.py",
        }
        assert mocks.pr_manager.merge_pull_request.call_count == 1

    def test_rebase_conflict_without_files(self, mocks: Mocks) -> None:
        mocks.pr_manager.merge_pull_request.return_value = REFUSED_405
        mocks.rebase.return_value = RebaseOutcome("conflict", "main")

        outcome = run_auto_merge(_PROJECT, _BRANCH, verified_sha=_SHA)

        assert _fields(outcome)["Likely conflicting files"] is None

    def test_push_failed_resets_and_is_merge_failed(self, mocks: Mocks) -> None:
        mocks.pr_manager.merge_pull_request.return_value = REFUSED_405
        mocks.rebase.return_value = RebaseOutcome("push_failed", "main", "1234567")

        outcome = run_auto_merge(_PROJECT, _BRANCH, verified_sha=_SHA)

        mocks.reset_hard.assert_called_once_with(_PROJECT, _SHA)
        assert outcome.label_id == "merge_failed"
        assert _fields(outcome)["Reason"] == "push_failed"
        assert _fields(outcome)["Base"] == "main"
        assert _fields(outcome)["Mergeable state"] == "dirty"

    def test_other_rebase_failure_no_reset(self, mocks: Mocks) -> None:
        mocks.pr_manager.merge_pull_request.return_value = REFUSED_405
        mocks.rebase.return_value = RebaseOutcome("rebase_failed", "main")

        outcome = run_auto_merge(_PROJECT, _BRANCH, verified_sha=_SHA)

        mocks.reset_hard.assert_not_called()
        assert outcome.label_id == "merge_failed"
        assert _fields(outcome)["Reason"] == "rebase_failed"


class TestRunAutoMergeExceptions:
    """The single exception handler: rate limit, auth, everything else raises."""

    def test_rate_limit_is_pr_created(self, mocks: Mocks) -> None:
        mocks.pr_manager.merge_pull_request.side_effect = GitHubRateLimitError(
            "limited"
        )

        with patch(f"{_MODULE}.log_rate_limit_stop") as log_stop:
            outcome = run_auto_merge(_PROJECT, _BRANCH)

        assert outcome == MergeOutcome("pr_created")
        log_stop.assert_called_once()

    @pytest.mark.parametrize("status", [401, 403])
    def test_auth_error_is_merge_failed(self, mocks: Mocks, status: int) -> None:
        mocks.pr_manager.merge_pull_request.side_effect = GithubException(
            status, {"message": "Bad credentials"}, None
        )

        outcome = run_auto_merge(_PROJECT, _BRANCH)

        assert outcome.label_id == "merge_failed"
        fields = _fields(outcome)
        assert fields["Stage"] == "Auto-merge"
        assert fields["Error"]

    def test_other_exception_propagates(self, mocks: Mocks) -> None:
        mocks.pr_manager.find_pull_request_by_head.side_effect = ValueError("boom")

        with pytest.raises(ValueError, match="boom"):
            run_auto_merge(_PROJECT, _BRANCH)

    def test_other_github_exception_propagates(self, mocks: Mocks) -> None:
        mocks.pr_manager.merge_pull_request.side_effect = GithubException(
            404, {"message": "Not Found"}, None
        )

        with pytest.raises(GithubException):
            run_auto_merge(_PROJECT, _BRANCH)
