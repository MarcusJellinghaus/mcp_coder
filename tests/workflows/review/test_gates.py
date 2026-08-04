"""Tests for the implementation-lane review gates (Steps 5 & 6).

Gate 1 (:func:`check_open_tasks_gate`) is pure logic over ``get_incomplete_tasks``.
Every case patches ``mcp_coder.workflows.review.gates.get_incomplete_tasks`` so
no real ``TASK_TRACKER.md`` is touched, and asserts the returned
``(reason, details)`` tuple (plus, for the plan lane, that the tracker is never
read at all).

Gate 2 (:func:`check_ci_proven_gate`) is pure logic over one
``collect_branch_status`` call; every case patches
``mcp_coder.workflows.review.gates.collect_branch_status`` and asserts the
returned ``(reason, details)`` tuple for each observed ``CIStatus``.

A single ``core``-level test confirms Gate 1 is wired at the top of ``body()``:
a blocking gate returns ``1`` without entering the round loop.
"""

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from mcp_coder.checks.branch_status import CIStatus
from mcp_coder.workflow_utils.task_tracker import (
    TaskTrackerFileNotFoundError,
    TaskTrackerSectionNotFoundError,
)
from mcp_coder.workflows.review import core, gates, handoff, reviewer
from mcp_coder.workflows.review.config import REVIEW_IMPLEMENTATION, REVIEW_PLAN
from mcp_coder.workflows.review.gates import (
    MAX_LISTED_TASKS,
    check_ci_proven_gate,
    check_open_tasks_gate,
)


class TestCheckOpenTasksGate:
    """The pure Gate-1 predicate over the incomplete-task list."""

    def test_plan_lane_skips_and_never_reads_tracker(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """enforce_implementation_gates=False → (None, None), no tracker read."""
        get_tasks = MagicMock(name="get_incomplete_tasks")
        monkeypatch.setattr(gates, "get_incomplete_tasks", get_tasks)

        assert check_open_tasks_gate(REVIEW_PLAN, Path("/repo")) == (None, None)
        get_tasks.assert_not_called()

    def test_no_open_tasks_proceeds(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """An empty incomplete-task list → (None, None)."""
        monkeypatch.setattr(gates, "get_incomplete_tasks", MagicMock(return_value=[]))

        assert check_open_tasks_gate(REVIEW_IMPLEMENTATION, Path("/repo")) == (
            None,
            None,
        )

    def test_reads_pr_info_folder(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The tracker folder passed is ``<project_dir>/pr_info`` as a string."""
        get_tasks = MagicMock(return_value=[])
        monkeypatch.setattr(gates, "get_incomplete_tasks", get_tasks)

        check_open_tasks_gate(REVIEW_IMPLEMENTATION, Path("/repo"))

        assert get_tasks.call_args.args[0] == str(Path("/repo") / "pr_info")

    def test_open_tasks_block_and_list_them(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Open tasks → ("tasks", details) naming each task + the recovery cmd."""
        monkeypatch.setattr(
            gates, "get_incomplete_tasks", MagicMock(return_value=["A", "B"])
        )

        reason, details = check_open_tasks_gate(REVIEW_IMPLEMENTATION, Path("/repo"))

        assert reason == "tasks"
        assert details is not None
        assert "A" in details and "B" in details
        assert "2 open task" in details
        assert "/implementation_finalise" in details
        assert "more" not in details  # under the cap: no "… and N more"

    def test_listing_capped_at_ten(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """12 open tasks → exactly 10 listed + '… and 2 more'; count is 12."""
        tasks = [f"T{i}" for i in range(12)]
        monkeypatch.setattr(
            gates, "get_incomplete_tasks", MagicMock(return_value=tasks)
        )

        reason, details = check_open_tasks_gate(REVIEW_IMPLEMENTATION, Path("/repo"))

        assert reason == "tasks"
        assert details is not None
        assert "12 open task" in details
        for shown in tasks[:MAX_LISTED_TASKS]:
            assert shown in details
        # The 11th/12th task names are not listed, only summarized.
        assert "T10" not in details and "T11" not in details
        assert "… and 2 more" in details

    def test_missing_tracker_skips(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """TaskTrackerFileNotFoundError → (None, None) (skip, mirrors create_pr)."""
        monkeypatch.setattr(
            gates,
            "get_incomplete_tasks",
            MagicMock(side_effect=TaskTrackerFileNotFoundError("missing")),
        )

        assert check_open_tasks_gate(REVIEW_IMPLEMENTATION, Path("/repo")) == (
            None,
            None,
        )

    def test_malformed_tracker_blocks(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A missing ## Tasks section → ("tasks", details) naming the cause.

        The details must not imply /implementation_finalise repairs structure.
        """
        monkeypatch.setattr(
            gates,
            "get_incomplete_tasks",
            MagicMock(side_effect=TaskTrackerSectionNotFoundError("no ## Tasks")),
        )

        reason, details = check_open_tasks_gate(REVIEW_IMPLEMENTATION, Path("/repo"))

        assert reason == "tasks"
        assert details is not None
        assert "could not be read as a task list" in details
        assert "no ## Tasks" in details
        assert "will not repair" in details


class TestGateWiredIntoCore:
    """Gate 1 is called at the top of body(), before the round loop."""

    def test_blocking_gate_returns_one_without_looping(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """A blocking gate → run_review_workflow returns 1, reviewer never runs."""
        monkeypatch.setattr(
            core,
            "check_open_tasks_gate",
            MagicMock(return_value=("tasks", "d")),
        )
        # Pre-loop context resolution touches git; stub it so the test is
        # isolated from the (non-git) tmp_path.
        monkeypatch.setattr(
            core, "_resolve_context", MagicMock(return_value=(None, None))
        )
        # Prove the round loop is never entered: the reviewer would be the first
        # LLM call, so a failure here would surface as a call, not a stub return.
        reviewer_run = MagicMock(name="_run_reviewer")
        monkeypatch.setattr(reviewer, "_run_reviewer", reviewer_run)
        monkeypatch.setattr(handoff, "handle_workflow_failure", MagicMock())
        monkeypatch.setattr(handoff, "IssueManager", MagicMock())
        monkeypatch.setattr(handoff, "update_workflow_label", MagicMock())

        result = core.run_review_workflow(
            config=REVIEW_IMPLEMENTATION,
            project_dir=tmp_path,
            provider="claude",
        )

        assert result == 1
        reviewer_run.assert_not_called()


class TestCheckCiProvenGate:
    """The pure Gate-2 predicate over a single ``collect_branch_status`` call."""

    def _patch_ci(
        self, monkeypatch: pytest.MonkeyPatch, ci_status: CIStatus
    ) -> MagicMock:
        """Patch ``gates.collect_branch_status`` to report ``ci_status`` once."""
        collect = MagicMock(
            return_value=SimpleNamespace(ci_status=ci_status),
            name="collect_branch_status",
        )
        monkeypatch.setattr(gates, "collect_branch_status", collect)
        return collect

    def test_passed_proves_green_with_single_status_call(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """PASSED -> (None, None); status is collected exactly once (no retry)."""
        collect = self._patch_ci(monkeypatch, CIStatus.PASSED)

        assert check_ci_proven_gate(Path("/repo")) == (None, None)
        collect.assert_called_once_with(Path("/repo"))

    def test_failed_is_the_existing_ci_reason(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """FAILED -> ("ci", details); the determinably-red case.

        A determinably-red pipeline stays the existing ``17f-ci`` case, not
        ``ci_unknown``.
        """
        self._patch_ci(monkeypatch, CIStatus.FAILED)

        reason, details = check_ci_proven_gate(Path("/repo"))

        assert reason == "ci"
        assert details is not None
        assert "FAILED" in details
        assert "could not prove CI ran green" in details

    @pytest.mark.parametrize(
        "ci_status",
        [
            CIStatus.PENDING,
            CIStatus.NOT_CONFIGURED,
            CIStatus.UNKNOWN,
            CIStatus.UNAVAILABLE,
        ],
    )
    def test_unprovable_states_are_ci_unknown(
        self, monkeypatch: pytest.MonkeyPatch, ci_status: CIStatus
    ) -> None:
        """Every non-PASSED, non-FAILED status -> ("ci_unknown", details).

        The details name the observed status and point at the token / CI-exists
        recovery rather than "fix the code".
        """
        self._patch_ci(monkeypatch, ci_status)

        reason, details = check_ci_proven_gate(Path("/repo"))

        assert reason == "ci_unknown"
        assert details is not None
        assert ci_status.value in details
        assert "GitHub token" in details
