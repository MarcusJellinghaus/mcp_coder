"""Tests for the mechanical fix_conflict workflow (rebase + poll + label transition)."""

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.workflows.fix_conflict.core import run_fix_conflict_workflow

MODULE = "mcp_coder.workflows.fix_conflict.core"
_SHARED_HANDLER = "mcp_coder.workflow_utils.failure_handling.handle_workflow_failure"
PROJECT_DIR = Path("/fake/project")
BRANCH_NAME = "123-fix-something"


def _patch_all(
    mergeable_states: list[list[dict[str, Any]]],
) -> tuple[tuple[Any, ...], MagicMock]:
    """Patch every external dependency used by run_fix_conflict_workflow.

    ``mergeable_states`` is the sequence of ``find_pull_request_by_head``
    return values, one per poll attempt (repeats the last value once the
    list is exhausted).
    """
    pr_manager = MagicMock()
    pr_manager.find_pull_request_by_head.side_effect = mergeable_states
    return (
        patch(f"{MODULE}.get_current_branch_name", return_value=BRANCH_NAME),
        patch(f"{MODULE}._attempt_rebase_and_push", return_value=True),
        patch(f"{MODULE}.PullRequestManager", return_value=pr_manager),
        patch(f"{MODULE}.IssueManager"),
        patch(f"{MODULE}.update_workflow_label"),
        patch(f"{MODULE}.time.sleep"),
    ), pr_manager


def test_dirty_on_first_poll_transitions_to_pr_merge_conflict() -> None:
    patches, _ = _patch_all([[{"mergeable_state": "dirty"}]])
    with (
        patches[0],
        patches[1],
        patches[2],
        patches[3] as mock_issue_cls,
        patches[4] as mock_update,
        patches[5] as mock_sleep,
    ):
        result = run_fix_conflict_workflow(PROJECT_DIR)

    assert result == 0
    mock_update.assert_called_once_with(
        mock_issue_cls.return_value, "fixing_merge_conflict", "pr_merge_conflict"
    )
    mock_sleep.assert_not_called()


def test_clean_transitions_to_pr_created() -> None:
    patches, _ = _patch_all([[{"mergeable_state": "clean"}]])
    with (
        patches[0],
        patches[1],
        patches[2],
        patches[3] as mock_issue_cls,
        patches[4] as mock_update,
        patches[5] as _,
    ):
        result = run_fix_conflict_workflow(PROJECT_DIR)

    assert result == 0
    mock_update.assert_called_once_with(
        mock_issue_cls.return_value, "fixing_merge_conflict", "pr_created"
    )


def test_unknown_for_all_attempts_leaves_label_untouched() -> None:
    patches, _ = _patch_all([[{"mergeable_state": "unknown"}]] * 6)
    with (
        patches[0],
        patches[1],
        patches[2],
        patches[3],
        patches[4] as mock_update,
        patches[5] as mock_sleep,
    ):
        result = run_fix_conflict_workflow(PROJECT_DIR)

    assert result == 0
    mock_update.assert_not_called()
    assert mock_sleep.call_count == 5


def test_no_open_pr_found_treated_as_unresolved() -> None:
    patches, _ = _patch_all([[]] * 6)
    with (
        patches[0],
        patches[1],
        patches[2],
        patches[3],
        patches[4] as mock_update,
        patches[5] as _,
    ):
        result = run_fix_conflict_workflow(PROJECT_DIR)

    assert result == 0
    mock_update.assert_not_called()


def test_no_current_branch_returns_1_without_rebase() -> None:
    with (
        patch(f"{MODULE}.get_current_branch_name", return_value=None),
        patch(f"{MODULE}._attempt_rebase_and_push") as mock_rebase,
    ):
        result = run_fix_conflict_workflow(PROJECT_DIR)

    assert result == 1
    mock_rebase.assert_not_called()


def test_unexpected_exception_is_caught_and_returns_1() -> None:
    with (
        patch(f"{MODULE}.get_current_branch_name", side_effect=RuntimeError("boom")),
        patch(_SHARED_HANDLER) as mock_shared,
    ):
        result = run_fix_conflict_workflow(PROJECT_DIR)

    assert result == 1
    mock_shared.assert_called_once()
    netted_failure = mock_shared.call_args[0][0]
    assert netted_failure.category == "merge_conflict_failed"


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
