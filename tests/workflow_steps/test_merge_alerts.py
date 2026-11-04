"""Tests for the auto-merge alert gate: CodeQL wait, alerts read, real-gate runs."""

import logging
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, call, patch

import pytest
from requests.exceptions import RetryError

from mcp_coder.mcp_workspace_github import GithubException
from mcp_coder.workflow_steps.constants import CI_POLL_INTERVAL_SECONDS
from mcp_coder.workflow_steps.merge import (
    MergeOutcome,
    _check_alert_gate,
    run_auto_merge,
)
from mcp_coder.workflow_steps.rebase import RebaseOutcome

_MODULE = "mcp_coder.workflow_steps.merge"
_PROJECT = Path("/fake/project")
_BRANCH = "123-feature"
_SHA = "a" * 40
_NEW_SHA = "b" * 40
_OLD_SHA = "c" * 40
_REF = "refs/pull/7/head"


def _pr(head_sha: str = _SHA) -> dict[str, Any]:
    return {"number": 7, "title": "Add feature", "head_sha": head_sha}


def _run(
    sha: str = _SHA, status: str = "completed", conclusion: str | None = "success"
) -> dict[str, Any]:
    return {
        "run": {"commit_sha": sha, "status": status, "conclusion": conclusion},
        "jobs": [],
    }


def _feedback(
    alerts: list[dict[str, Any]] | None = None,
    unavailable: dict[str, Exception] | None = None,
    skipped: dict[str, Exception] | None = None,
) -> dict[str, Any]:
    return {
        "unresolved_threads": [],
        "resolved_thread_count": 0,
        "changes_requested": [],
        "conversation_comments": [],
        "alerts": alerts or [],
        "unavailable": unavailable or {},
        "skipped": skipped or {},
    }


def _github_error(status: int) -> GithubException:
    return GithubException(status, {"message": "nope"}, None)


SUCCESS = _run()
IN_PROGRESS = _run(status="in_progress", conclusion=None)
OLD_RUN = _run(_OLD_SHA)
NO_RUN: dict[str, Any] = {"run": {}, "jobs": []}
LOOKUP_FAILED: dict[str, Any] = {"run": {}, "jobs": [], "lookup_failed": True}
ALERT = {"number": 51, "rule_id": "py/sql-injection"}
REFUSED_405 = {
    "merged": False,
    "outcome": "refused",
    "sha": None,
    "message": "not mergeable",
    "status": 405,
}
MERGED = {
    "merged": True,
    "outcome": "merged",
    "sha": None,
    "message": "merged",
    "status": 200,
}


@dataclass
class Mocks:
    """Patched collaborators of the alert gate and run_auto_merge."""

    pr_manager: MagicMock
    ci_manager: MagicMock
    latest_sha: MagicMock
    poll_ci: MagicMock
    sleep: MagicMock


@pytest.fixture(name="mocks")
def _mocks() -> Iterator[Mocks]:
    pr_manager = MagicMock()
    pr_manager.find_pull_request_by_head.return_value = [_pr()]
    pr_manager.merge_pull_request.return_value = MERGED
    pr_manager.get_pr_feedback.return_value = _feedback()
    with (
        patch(f"{_MODULE}.PullRequestManager", return_value=pr_manager),
        patch(f"{_MODULE}.CIResultsManager") as ci_cls,
        patch(f"{_MODULE}.get_latest_commit_sha", return_value=_SHA) as latest_sha,
        patch(
            f"{_MODULE}._poll_for_ci_completion",
            return_value=(_run(), True),
        ) as poll_ci,
        patch(f"{_MODULE}._poll_mergeable_state", return_value="dirty"),
        patch(
            f"{_MODULE}._attempt_rebase_and_push",
            return_value=RebaseOutcome("ok", "main", "1234567"),
        ),
        patch(f"{_MODULE}._reset_hard", return_value=True),
        patch(f"{_MODULE}.time.sleep") as sleep,
    ):
        ci_cls.return_value.get_latest_ci_status.return_value = SUCCESS
        yield Mocks(
            pr_manager=pr_manager,
            ci_manager=ci_cls.return_value,
            latest_sha=latest_sha,
            poll_ci=poll_ci,
            sleep=sleep,
        )


def _fields(outcome: MergeOutcome | None) -> dict[str, str | None]:
    assert outcome is not None
    return dict(outcome.comment_fields)


class TestWaitForCodeScanning:
    """The wait on refs/pull/N/head before alerts are read."""

    @pytest.mark.parametrize(
        "polls",
        [
            pytest.param([SUCCESS], id="success_at_once"),
            pytest.param([IN_PROGRESS, SUCCESS], id="in_progress_then_success"),
            pytest.param([IN_PROGRESS] * 20 + [SUCCESS], id="success_on_last_poll"),
            pytest.param([OLD_RUN, SUCCESS], id="older_sha_then_success"),
            pytest.param(
                [_run(_OLD_SHA, conclusion="failure"), SUCCESS],
                id="older_sha_failure_is_ignored",
            ),
            pytest.param([NO_RUN, SUCCESS], id="no_run_then_success"),
            pytest.param([NO_RUN] * 8, id="no_run_on_8_polls"),
            pytest.param([OLD_RUN] * 8, id="older_sha_on_8_polls"),
            pytest.param([LOOKUP_FAILED, SUCCESS], id="one_lookup_failed"),
            pytest.param(
                [LOOKUP_FAILED, LOOKUP_FAILED, IN_PROGRESS] * 2 + [SUCCESS],
                id="lookup_failed_count_resets",
            ),
        ],
    )
    def test_goes_on_to_read_alerts(
        self, mocks: Mocks, polls: list[dict[str, Any]]
    ) -> None:
        mocks.ci_manager.get_latest_ci_status.side_effect = polls

        assert _check_alert_gate(_PROJECT, 7, _SHA) is None

        assert mocks.ci_manager.get_latest_ci_status.call_args_list == (
            [call(_REF)] * len(polls)
        )
        assert mocks.sleep.call_args_list == (
            [call(CI_POLL_INTERVAL_SECONDS)] * (len(polls) - 1)
        )
        mocks.pr_manager.get_pr_feedback.assert_called_once_with(7)

    @pytest.mark.parametrize(
        ("polls", "error"),
        [
            pytest.param(
                [_run(conclusion="failure")], "failure", id="completed_non_success"
            ),
            pytest.param(
                [IN_PROGRESS, _run(conclusion="cancelled")],
                "cancelled",
                id="in_progress_then_non_success",
            ),
            pytest.param([IN_PROGRESS] * 21, "in time", id="in_progress_on_21_polls"),
            pytest.param(
                [NO_RUN] * 7 + [IN_PROGRESS] * 14, "in time", id="late_run_same_budget"
            ),
            pytest.param([LOOKUP_FAILED] * 3, "lookup", id="lookup_failed_on_3_polls"),
            pytest.param(
                [NO_RUN] * 7 + [LOOKUP_FAILED] * 3,
                "lookup",
                id="lookup_failed_is_never_no_run",
            ),
        ],
    )
    def test_failed_alert_check(
        self, mocks: Mocks, polls: list[dict[str, Any]], error: str
    ) -> None:
        mocks.ci_manager.get_latest_ci_status.side_effect = polls

        outcome = _check_alert_gate(_PROJECT, 7, _SHA)

        assert outcome is not None
        assert outcome.label_id == "merge_failed"
        assert _fields(outcome)["Stage"] == "Auto-merge alert check"
        assert error in str(_fields(outcome)["Error"])
        assert mocks.ci_manager.get_latest_ci_status.call_count == len(polls)
        assert mocks.sleep.call_count == len(polls) - 1
        mocks.pr_manager.get_pr_feedback.assert_not_called()

    def test_no_run_logs_warning(
        self, mocks: Mocks, caplog: pytest.LogCaptureFixture
    ) -> None:
        mocks.ci_manager.get_latest_ci_status.side_effect = [NO_RUN] * 8

        with caplog.at_level(logging.WARNING, logger=_MODULE):
            _check_alert_gate(_PROJECT, 7, _SHA)

        assert any(
            record.levelno == logging.WARNING and "code-scanning run" in record.message
            for record in caplog.records
        )

    def test_lookup_error_is_named(self, mocks: Mocks) -> None:
        mocks.ci_manager.get_latest_ci_status.return_value = {
            **LOOKUP_FAILED,
            "lookup_error": "GitHub API error 502: Bad Gateway",
        }

        outcome = _check_alert_gate(_PROJECT, 7, _SHA)

        assert "GitHub API error 502" in str(_fields(outcome)["Error"])


class TestCheckAlertGate:
    """Every result of reading the alerts keys."""

    def test_no_alerts_merges(self, mocks: Mocks) -> None:
        assert _check_alert_gate(_PROJECT, 7, _SHA) is None
        mocks.pr_manager.get_pr_feedback.assert_called_once_with(7)

    def test_open_alert_blocks(
        self, mocks: Mocks, caplog: pytest.LogCaptureFixture
    ) -> None:
        mocks.pr_manager.get_pr_feedback.return_value = _feedback(alerts=[ALERT, ALERT])

        with caplog.at_level(logging.DEBUG, logger=_MODULE):
            outcome = _check_alert_gate(_PROJECT, 7, _SHA)

        assert outcome == MergeOutcome("pr_created")
        assert (
            "Auto-merge: 2 open code-scanning alert(s) on PR #7 — not merging"
            in caplog.messages
        )

    @pytest.mark.parametrize("status", [401, 500])
    def test_unavailable_alerts_is_merge_failed(
        self, mocks: Mocks, status: int
    ) -> None:
        mocks.pr_manager.get_pr_feedback.return_value = _feedback(
            unavailable={"alerts": _github_error(status)}
        )

        outcome = _check_alert_gate(_PROJECT, 7, _SHA)

        assert outcome is not None
        assert outcome.label_id == "merge_failed"
        assert _fields(outcome)["Stage"] == "Auto-merge alert check"
        assert _fields(outcome)["Error"]

    def test_unavailable_rate_limit_stops(
        self, mocks: Mocks, caplog: pytest.LogCaptureFixture
    ) -> None:
        mocks.pr_manager.get_pr_feedback.return_value = _feedback(
            unavailable={"alerts": _github_error(429)}
        )

        with caplog.at_level(logging.DEBUG):
            outcome = _check_alert_gate(_PROJECT, 7, _SHA)

        assert outcome == MergeOutcome("pr_created")
        assert any("GitHub rate limit hit" in message for message in caplog.messages)

    @pytest.mark.parametrize("section", ["threads", "comments"])
    def test_other_unavailable_sections_merge(self, mocks: Mocks, section: str) -> None:
        mocks.pr_manager.get_pr_feedback.return_value = _feedback(
            unavailable={section: RuntimeError("boom")}
        )

        assert _check_alert_gate(_PROJECT, 7, _SHA) is None

    @pytest.mark.parametrize(
        ("exc", "status_text"),
        [
            pytest.param(_github_error(403), "status 403", id="403"),
            pytest.param(_github_error(404), "status 404", id="404"),
            pytest.param(RuntimeError("no status"), "status None", id="no_status"),
        ],
    )
    def test_skipped_merges_with_warning(
        self,
        mocks: Mocks,
        caplog: pytest.LogCaptureFixture,
        exc: Exception,
        status_text: str,
    ) -> None:
        mocks.pr_manager.get_pr_feedback.return_value = _feedback(
            skipped={"alerts": exc}
        )

        with caplog.at_level(logging.WARNING, logger=_MODULE):
            outcome = _check_alert_gate(_PROJECT, 7, _SHA)

        assert outcome is None
        assert (
            f"alerts not checked ({status_text}); the token may lack "
            "`Code scanning alerts: Read`, or code scanning is not enabled"
            in caplog.messages
        )

    @pytest.mark.parametrize(
        ("target", "exc"),
        [
            pytest.param("feedback", RuntimeError("boom"), id="feedback_raises"),
            pytest.param("ci", ValueError("bad ref"), id="ci_lookup_raises"),
            pytest.param("feedback", _github_error(500), id="feedback_500"),
        ],
    )
    def test_raised_error_is_merge_failed(
        self, mocks: Mocks, target: str, exc: Exception
    ) -> None:
        if target == "ci":
            mocks.ci_manager.get_latest_ci_status.side_effect = exc
        else:
            mocks.pr_manager.get_pr_feedback.side_effect = exc

        outcome = _check_alert_gate(_PROJECT, 7, _SHA)

        assert outcome is not None
        assert outcome.label_id == "merge_failed"
        assert _fields(outcome)["Stage"] == "Auto-merge alert check"
        assert _fields(outcome)["Error"]

    @pytest.mark.parametrize(
        "exc",
        [
            pytest.param(_github_error(401), id="401"),
            pytest.param(_github_error(403), id="403"),
            pytest.param(_github_error(429), id="429"),
            pytest.param(RetryError("retries exhausted"), id="retry_error"),
        ],
    )
    def test_auth_and_rate_limit_propagate(self, mocks: Mocks, exc: Exception) -> None:
        mocks.pr_manager.get_pr_feedback.side_effect = exc

        with pytest.raises(type(exc)):
            _check_alert_gate(_PROJECT, 7, _SHA)


class TestRunAutoMergeRealGate:
    """run_auto_merge with the gate not patched."""

    def test_no_alerts_merges(self, mocks: Mocks) -> None:
        outcome = run_auto_merge(_PROJECT, _BRANCH, verified_sha=_SHA)

        assert outcome == MergeOutcome("merged")
        mocks.ci_manager.get_latest_ci_status.assert_called_once_with(_REF)
        mocks.pr_manager.get_pr_feedback.assert_called_once_with(7)
        mocks.pr_manager.merge_pull_request.assert_called_once()

    @pytest.mark.parametrize(
        "exc",
        [
            pytest.param(_github_error(429), id="raw_429"),
            pytest.param(RetryError("retries exhausted"), id="retry_error"),
        ],
    )
    def test_ci_lookup_rate_limit_is_pr_created(
        self, mocks: Mocks, caplog: pytest.LogCaptureFixture, exc: Exception
    ) -> None:
        mocks.ci_manager.get_latest_ci_status.side_effect = exc

        with caplog.at_level(logging.DEBUG):
            outcome = run_auto_merge(_PROJECT, _BRANCH, verified_sha=_SHA)

        assert outcome == MergeOutcome("pr_created")
        assert any("GitHub rate limit hit" in message for message in caplog.messages)
        mocks.pr_manager.merge_pull_request.assert_not_called()

    def test_feedback_401_is_merge_failed_from_outer_handler(
        self, mocks: Mocks
    ) -> None:
        mocks.pr_manager.get_pr_feedback.side_effect = _github_error(401)

        outcome = run_auto_merge(_PROJECT, _BRANCH, verified_sha=_SHA)

        assert outcome.label_id == "merge_failed"
        assert _fields(outcome)["Stage"] == "Auto-merge"
        mocks.pr_manager.merge_pull_request.assert_not_called()

    def test_open_alert_on_verified_sha_path_does_not_merge(self, mocks: Mocks) -> None:
        mocks.pr_manager.get_pr_feedback.return_value = _feedback(alerts=[ALERT])

        outcome = run_auto_merge(_PROJECT, _BRANCH, verified_sha=_SHA)

        assert outcome == MergeOutcome("pr_created")
        mocks.poll_ci.assert_not_called()
        mocks.pr_manager.merge_pull_request.assert_not_called()

    def test_open_alert_after_rebase_retry_does_not_merge_again(
        self, mocks: Mocks
    ) -> None:
        mocks.pr_manager.merge_pull_request.return_value = REFUSED_405
        mocks.pr_manager.find_pull_request_by_head.side_effect = [
            [_pr()],
            [_pr()],
            [_pr(_NEW_SHA)],
        ]
        mocks.latest_sha.side_effect = [_SHA, _NEW_SHA]
        mocks.poll_ci.return_value = (_run(_NEW_SHA), True)
        mocks.ci_manager.get_latest_ci_status.side_effect = [SUCCESS, _run(_NEW_SHA)]
        mocks.pr_manager.get_pr_feedback.side_effect = [
            _feedback(),
            _feedback(alerts=[ALERT]),
        ]

        outcome = run_auto_merge(_PROJECT, _BRANCH, verified_sha=_SHA)

        assert outcome == MergeOutcome("pr_created")
        assert mocks.pr_manager.merge_pull_request.call_count == 1
        assert mocks.pr_manager.get_pr_feedback.call_count == 2
