"""Step 6 — Gate 2 exit-guard tests (CI proven green before success).

These deterministic tests drive :func:`run_review_workflow` against
``REVIEW_IMPLEMENTATION`` (``run_after_steps=True``) and assert the Gate 2
exit guard: after a dismiss + clean after-steps, the run only reaches success
when a fresh ``gates.collect_branch_status`` proves CI ``PASSED``. The shared
``env`` fixture and the ``_status``/``_reviewer``/``_resp``/``_run``/
``_label_transition`` helpers live in ``conftest``.
"""

from pathlib import Path
from types import SimpleNamespace

import pytest

from mcp_coder.checks.branch_status import CIStatus
from mcp_coder.workflows.review.config import REVIEW_IMPLEMENTATION, REVIEW_PLAN
from tests.workflows.review.conftest import (
    _DISMISS,
    _label_transition,
    _resp,
    _reviewer,
    _run,
    _status,
)

# --- Step 6: Gate 2 exit guard (CI proven green) ---------------------------


def test_gate2_dismiss_ci_passed_succeeds(env: SimpleNamespace, tmp_path: Path) -> None:
    """dismiss + after-steps clean + Gate 2 sees PASSED -> success (ready_pr)."""
    env.gate_collect_branch_status.return_value = _status(ci_status=CIStatus.PASSED)
    env.prompt_llm.side_effect = [_reviewer(), _resp(_DISMISS)]

    result = _run(tmp_path)

    assert result == 0
    # Gate 2 makes exactly one fresh branch-status call — no retry loop.
    env.gate_collect_branch_status.assert_called_once_with(tmp_path)
    env.handle_workflow_failure.assert_not_called()
    _, to_id = _label_transition(env.update_workflow_label)
    assert to_id == REVIEW_IMPLEMENTATION.success_label_id


@pytest.mark.parametrize(
    "ci_status",
    [
        CIStatus.PENDING,
        CIStatus.NOT_CONFIGURED,
        CIStatus.UNKNOWN,
        CIStatus.UNAVAILABLE,
    ],
)
def test_gate2_unprovable_ci_fails_ci_unknown(
    env: SimpleNamespace, tmp_path: Path, ci_status: CIStatus
) -> None:
    """A non-PASSED, non-FAILED status -> RC=1 with the ci_unknown label.

    The round log is flushed (Gate 2 runs before the success push) so the last
    round still lands in the committed review log, and the failure comment names
    the observed CI status.
    """
    env.gate_collect_branch_status.return_value = _status(ci_status=ci_status)
    env.prompt_llm.side_effect = [_reviewer(), _resp(_DISMISS)]

    result = _run(tmp_path)

    assert result == 1
    failure = env.handle_workflow_failure.call_args.args[0]
    assert failure.category == REVIEW_IMPLEMENTATION.failure_labels["ci_unknown"]
    # Not conflated with the determinably-red ci label.
    assert failure.category != REVIEW_IMPLEMENTATION.failure_labels["ci"]
    # The details line names the observed status in the failure comment.
    assert ci_status.value in env.handle_workflow_failure.call_args.args[1]
    # The last round's log was flushed to the committed log before _fail.
    env.commit_all_changes.assert_called()


def test_gate2_failed_ci_uses_ci_label_not_ci_unknown(
    env: SimpleNamespace, tmp_path: Path
) -> None:
    """Gate 2 seeing FAILED -> RC=1 with the ci label (not ci_unknown)."""
    env.gate_collect_branch_status.return_value = _status(ci_status=CIStatus.FAILED)
    env.prompt_llm.side_effect = [_reviewer(), _resp(_DISMISS)]

    result = _run(tmp_path)

    assert result == 1
    failure = env.handle_workflow_failure.call_args.args[0]
    assert failure.category == REVIEW_IMPLEMENTATION.failure_labels["ci"]
    assert failure.category != REVIEW_IMPLEMENTATION.failure_labels["ci_unknown"]


def test_gate2_skipped_on_plan_lane(env: SimpleNamespace, tmp_path: Path) -> None:
    """review-plan dismiss -> Gate 2 never runs; success is unchanged."""
    env.prompt_llm.side_effect = [_reviewer(), _resp(_DISMISS)]

    result = _run(tmp_path, config=REVIEW_PLAN)

    assert result == 0
    env.gate_collect_branch_status.assert_not_called()
    _, to_id = _label_transition(env.update_workflow_label)
    assert to_id == REVIEW_PLAN.success_label_id
