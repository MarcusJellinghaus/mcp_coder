"""Round 1 (#1158) — the flush commit's own CI run must gate the dismiss.

Split out of ``test_core_after_steps``. Drives :func:`run_review_workflow`
against ``REVIEW_IMPLEMENTATION`` with the real ``check_and_fix_ci`` and a fake
GitHub CI whose newest run lags behind the pushed commit.
"""

import time
from pathlib import Path
from types import SimpleNamespace

import pytest

from mcp_coder.checks.branch_status import CIStatus
from mcp_coder.workflow_steps import ci
from mcp_coder.workflows.review import steps
from mcp_coder.workflows.review.config import REVIEW_IMPLEMENTATION
from tests.workflows.review.conftest import (
    _DISMISS,
    _TASKS,
    _label_transition,
    _resp,
    _reviewer,
    _run,
    _status,
)


class _FakeCIResults:
    """A GitHub CI stand-in whose newest run lags behind the pushed commit.

    Each ``get_latest_ci_status`` answers with the next entry and then stays on
    the last one, so ``current()`` is what a *fresh* read would see at any
    point. That models the real lag: right after a push the newest run on the
    branch is still the previous commit's, and only a moment later does the
    pushed commit's own run appear.
    """

    def __init__(self, sequence: list[dict[str, object]]) -> None:
        self.sequence = sequence
        self.index = 0

    def current(self) -> dict[str, object]:
        """Return the run a fresh read would see now, without consuming it."""
        return self.sequence[min(self.index, len(self.sequence) - 1)]

    def get_latest_ci_status(self, _branch: str) -> dict[str, object]:
        """Return the next run in the sequence (then repeat the last)."""
        status = self.current()
        self.index += 1
        return status


def _ci_run(status: str, sha: str, conclusion: str | None = None) -> dict[str, object]:
    """Build one ``get_latest_ci_status`` payload."""
    return {
        "run": {
            "status": status,
            "conclusion": conclusion,
            "run_ids": [1],
            "commit_sha": sha,
        },
        "jobs": [],
    }


def test_dismiss_round_waits_for_the_flush_commit_s_own_ci_run(
    env: SimpleNamespace, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A dismiss round that pushes only the flush commit still ends green.

    Round 1 (``tasks``) leaves its round-log write pending; round 2's loop entry
    commits it, and round 2's otherwise no-op rebase force-pushes that commit —
    so the branch gains a commit right before the CI gate. If the CI step took
    the newest run on the branch (still round 1's, completed green) as this
    commit's result, ``check_ci_proven_gate`` would then read the just-queued
    run as PENDING and fail the run ``ci_unknown``. Pinning the poll to the
    pushed SHA makes it wait for that run instead.
    """
    ci_results = _FakeCIResults(
        [
            _ci_run("completed", "SHA_R1", conclusion="success"),  # round 1's gate
            _ci_run("completed", "SHA_R1", conclusion="success"),  # stale on round 2
            _ci_run("queued", "SHA_R2"),  # the flush commit's run appears
            _ci_run("completed", "SHA_R2", conclusion="success"),
        ]
    )
    monkeypatch.setattr(ci, "CIResultsManager", lambda _project_dir: ci_results)
    monkeypatch.setattr(ci, "time", SimpleNamespace(time=time.time, sleep=lambda _s: 0))
    # The real CI step, so the poll's SHA correlation is what is under test.
    monkeypatch.setattr(steps, "check_and_fix_ci", ci.check_and_fix_ci)
    env.steps_get_latest_commit_sha.side_effect = ["SHA_R1", "SHA_R2"]

    def _gate_status(_project_dir: Path) -> SimpleNamespace:
        """Gate 2 reads live CI state, exactly as collect_branch_status does."""
        run = ci_results.current()["run"]
        assert isinstance(run, dict)
        proven = run["status"] == "completed" and run["conclusion"] == "success"
        return _status(ci_status=CIStatus.PASSED if proven else CIStatus.PENDING)

    env.gate_collect_branch_status.side_effect = _gate_status
    env.prompt_llm.side_effect = [
        _reviewer(),
        _resp(_TASKS),
        _reviewer(session_id="rev-1"),  # round 1 -> tasks
        _reviewer(),
        _resp(_DISMISS),  # round 2 -> dismiss, rebase pushes the flush commit
    ]

    assert _run(tmp_path) == 0
    env.handle_workflow_failure.assert_not_called()
    _, to_id = _label_transition(env.update_workflow_label)
    assert to_id == REVIEW_IMPLEMENTATION.success_label_id
