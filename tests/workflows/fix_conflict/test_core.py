"""Tests for the mechanical fix_conflict workflow (rebase + poll + label transition)."""

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.workflow_steps.rebase import RebaseOutcome
from mcp_coder.workflows.fix_conflict.core import run_fix_conflict_workflow

MODULE = "mcp_coder.workflows.fix_conflict.core"
_SHARED_HANDLER = "mcp_coder.workflow_utils.failure_handling.handle_workflow_failure"
_BRANCH_HEAD = "mcp_coder.workflow_utils.failure_handling._branch_head"
PROJECT_DIR = Path("/fake/project")
BRANCH_NAME = "123-fix-something"


def _patch_all(
    mergeable_states: list[list[dict[str, Any]]],
    outcome: RebaseOutcome = RebaseOutcome("ok", "main", "abc1234"),
) -> tuple[tuple[Any, ...], MagicMock]:
    """Patch every external dependency used by run_fix_conflict_workflow.

    ``mergeable_states`` is the sequence of ``find_pull_request_by_head``
    return values, one per poll attempt (repeats the last value once the
    list is exhausted). ``outcome`` is the rebase attempt's return value.
    """
    pr_manager = MagicMock()
    pr_manager.find_pull_request_by_head.side_effect = mergeable_states
    return (
        patch(f"{MODULE}.get_current_branch_name", return_value=BRANCH_NAME),
        patch(f"{MODULE}._attempt_rebase_and_push", return_value=outcome),
        patch(f"{MODULE}.PullRequestManager", return_value=pr_manager),
        patch(f"{MODULE}.IssueManager"),
        patch(f"{MODULE}.update_workflow_label"),
        patch(f"{MODULE}.time.sleep"),
        patch(f"{MODULE}.handle_workflow_failure"),
    ), pr_manager


@pytest.mark.parametrize(
    ("states", "outcome", "verdict", "present", "absent", "expected_sleeps"),
    [
        pytest.param(
            [[{"mergeable_state": "dirty"}]],
            RebaseOutcome("conflict", "main", "abc1234", ("a.py", "b.py")),
            "still conflicting",
            [
                "**Reason:** conflict",
                "**Base:** main",
                "**Likely conflicting files:** a.py, b.py",
            ],
            [],
            0,
            id="dirty",
        ),
        pytest.param(
            [[]] * 6,
            RebaseOutcome("ok", "main", "abc1234"),
            "no open PR found for branch",
            [],
            ["**Reason:**"],
            5,
            id="no_pr",
        ),
        pytest.param(
            [[{"mergeable_state": "unknown"}]] * 6,
            RebaseOutcome("push_failed", "main", "abc1234"),
            "mergeable state unknown, rebase did not complete",
            ["**Reason:** push_failed"],
            [],
            5,
            id="unknown_failed_rebase",
        ),
        pytest.param(
            [[{"mergeable_state": "dirty"}]],
            RebaseOutcome("dirty_tree", files=("uv.lock",)),
            "still conflicting",
            ["**Reason:** dirty_tree", "**Uncommitted files:** uv.lock"],
            ["**Base:**", "**Likely conflicting files:**"],
            0,
            id="dirty_tree",
        ),
    ],
)
def test_unresolved_outcomes_go_to_pr_merge_conflict(
    states: list[list[dict[str, Any]]],
    outcome: RebaseOutcome,
    verdict: str,
    present: list[str],
    absent: list[str],
    expected_sleeps: int,
) -> None:
    patches, _ = _patch_all(states, outcome)
    with (
        patches[0],
        patches[1],
        patches[2],
        patches[3],
        patches[4] as mock_update,
        patches[5] as mock_sleep,
        patches[6] as mock_fail,
        patch(_BRANCH_HEAD, return_value=(BRANCH_NAME, "abc1234")),
    ):
        result = run_fix_conflict_workflow(PROJECT_DIR)

    assert result == 0
    mock_fail.assert_called_once()
    assert mock_fail.call_args[0][0].category == "pr_merge_conflict"
    comment = mock_fail.call_args[0][1]
    assert comment.splitlines()[0] == "## ❌ Fix Conflict Failed"
    assert f"**Verdict:** {verdict}" in comment
    for text in present:
        assert text in comment
    for text in absent:
        assert text not in comment
    kwargs = mock_fail.call_args.kwargs
    assert kwargs["from_label_id"] == "fixing_merge_conflict"
    assert kwargs["update_issue_labels"] is True
    assert kwargs["post_issue_comments"] is True
    mock_update.assert_not_called()
    assert mock_sleep.call_count == expected_sleeps


@pytest.mark.parametrize(
    ("states", "expected_sleeps"),
    [
        pytest.param([[{"mergeable_state": "clean"}]], 0, id="clean"),
        pytest.param([[{"mergeable_state": "unknown"}]] * 6, 5, id="unknown_ok"),
    ],
)
def test_settled_or_self_healing_outcomes_go_to_pr_created(
    states: list[list[dict[str, Any]]], expected_sleeps: int
) -> None:
    patches, _ = _patch_all(states)
    with (
        patches[0],
        patches[1],
        patches[2],
        patches[3] as mock_issue_cls,
        patches[4] as mock_update,
        patches[5] as mock_sleep,
        patches[6] as mock_fail,
    ):
        result = run_fix_conflict_workflow(PROJECT_DIR)

    assert result == 0
    mock_update.assert_called_once_with(
        mock_issue_cls.return_value, "fixing_merge_conflict", "pr_created"
    )
    mock_fail.assert_not_called()
    assert mock_sleep.call_count == expected_sleeps


def test_no_current_branch_returns_1_without_rebase() -> None:
    with (
        patch(f"{MODULE}.get_current_branch_name", return_value=None),
        patch(
            f"{MODULE}._attempt_rebase_and_push",
            return_value=RebaseOutcome("ok", "main", "abc1234"),
        ) as mock_rebase,
    ):
        result = run_fix_conflict_workflow(PROJECT_DIR)

    assert result == 1
    mock_rebase.assert_not_called()


def test_unexpected_exception_is_caught_and_returns_1() -> None:
    with (
        patch(f"{MODULE}.get_current_branch_name", side_effect=RuntimeError("boom")),
        patch(_SHARED_HANDLER) as mock_shared,
        patch(_BRANCH_HEAD, return_value=("feat", "abc1234")),
    ):
        result = run_fix_conflict_workflow(PROJECT_DIR)

    assert result == 1
    mock_shared.assert_called_once()
    netted_failure = mock_shared.call_args[0][0]
    assert netted_failure.category == "merge_conflict_failed"
    comment = mock_shared.call_args[0][1]
    assert comment.splitlines()[0] == "## ❌ Fix Conflict Crashed"


def test_system_exit_is_netted_and_reraised() -> None:
    with (
        patch(f"{MODULE}.get_current_branch_name", side_effect=SystemExit(1)),
        patch(_SHARED_HANDLER) as mock_shared,
    ):
        with pytest.raises(SystemExit):
            run_fix_conflict_workflow(PROJECT_DIR)

    mock_shared.assert_called_once()
    netted_failure = mock_shared.call_args[0][0]
    assert netted_failure.category == "merge_conflict_failed"
