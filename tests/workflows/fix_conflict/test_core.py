"""Tests for the fix_conflict workflow (rebase + poll + label transition)."""

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.workflow_steps.rebase import (
    BRANCH_MOVED_NEXT_STEP,
    BRANCH_MOVED_REASON,
    RebaseOutcome,
)
from mcp_coder.workflows.fix_conflict.core import run_fix_conflict_workflow

MODULE = "mcp_coder.workflows.fix_conflict.core"
_REBASE_MODULE = "mcp_coder.workflow_steps.rebase"
_SHARED_HANDLER = "mcp_coder.workflow_utils.failure_handling.handle_workflow_failure"
_BRANCH_HEAD = "mcp_coder.workflow_utils.failure_handling._branch_head"
PROJECT_DIR = Path("/fake/project")
BRANCH_NAME = "123-fix-something"
PROVIDER = "claude"
_OK_OUTCOME = RebaseOutcome("ok", "main", "abc1234")
_BRANCH_MOVED_OUTCOME = RebaseOutcome("branch_moved", "main", "abc1234")


def _patch_all(
    mergeable_states: list[list[dict[str, Any]]],
    outcome: RebaseOutcome = _OK_OUTCOME,
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
        patch(f"{MODULE}.rebase_with_llm_fallback", return_value=outcome),
        patch(f"{_REBASE_MODULE}.PullRequestManager", return_value=pr_manager),
        patch(_SHARED_HANDLER),
        patch(f"{MODULE}.apply_final_label", return_value=0),
        patch(f"{_REBASE_MODULE}.time.sleep"),
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
        pytest.param(
            [[{"mergeable_state": "dirty"}]],
            RebaseOutcome(
                "conflict",
                "main",
                "abc1234",
                ("a.py",),
                llm_detail="markers remain in a.py",
            ),
            "still conflicting",
            ["**Reason:** conflict", "**LLM rebase:** markers remain in a.py"],
            [],
            0,
            id="llm_detail",
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
        patches[3] as mock_net,
        patches[4] as mock_update,
        patches[5] as mock_sleep,
        patches[6] as mock_fail,
        patch(_BRANCH_HEAD, return_value=(BRANCH_NAME, "abc1234")),
    ):
        result = run_fix_conflict_workflow(PROJECT_DIR, PROVIDER)

    assert result == 1
    mock_net.assert_not_called()
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
        patches[3],
        patches[4] as mock_update,
        patches[5] as mock_sleep,
        patches[6] as mock_fail,
    ):
        result = run_fix_conflict_workflow(PROJECT_DIR, PROVIDER)

    assert result == 0
    mock_update.assert_called_once_with(
        PROJECT_DIR, "fixing_merge_conflict", "pr_created"
    )
    mock_fail.assert_not_called()
    assert mock_sleep.call_count == expected_sleeps


@pytest.mark.parametrize("finish_code", [0, 1])
def test_auto_merge_success_path_runs_helper_chain(finish_code: int) -> None:
    patches, _ = _patch_all([[{"mergeable_state": "clean"}]])
    calls = MagicMock()
    with (
        patches[0],
        patches[1],
        patches[2],
        patches[3],
        patches[4] as mock_update,
        patches[5] as _mock_sleep,
        patches[6] as mock_fail,
        patch(f"{MODULE}.resolve_merge_issue_number", return_value=123) as mock_resolve,
        patch(f"{MODULE}.run_auto_merge") as mock_merge,
        patch(f"{MODULE}.finish_auto_merge", return_value=finish_code) as mock_finish,
    ):
        calls.attach_mock(mock_resolve, "resolve")
        calls.attach_mock(mock_merge, "merge")
        result = run_fix_conflict_workflow(PROJECT_DIR, PROVIDER, auto_merge=True)

    assert result == finish_code
    assert [c[0] for c in calls.mock_calls] == ["resolve", "merge"]
    mock_resolve.assert_called_once_with(PROJECT_DIR, BRANCH_NAME)
    mock_merge.assert_called_once_with(PROJECT_DIR, BRANCH_NAME)
    mock_finish.assert_called_once_with(
        PROJECT_DIR,
        mock_merge.return_value,
        from_label_id="fixing_merge_conflict",
        issue_number=123,
        update_issue_labels=True,
        post_issue_comments=True,
    )
    mock_update.assert_not_called()
    mock_fail.assert_not_called()


def test_auto_merge_verdict_path_skips_helper() -> None:
    patches, _ = _patch_all(
        [[{"mergeable_state": "dirty"}]],
        RebaseOutcome("conflict", "main", "abc1234", ("a.py",)),
    )
    with (
        patches[0],
        patches[1],
        patches[2],
        patches[3],
        patches[4] as mock_update,
        patches[5] as _mock_sleep,
        patches[6] as mock_fail,
        patch(_BRANCH_HEAD, return_value=(BRANCH_NAME, "abc1234")) as _mock_head,
        patch(f"{MODULE}.resolve_merge_issue_number") as mock_resolve,
        patch(f"{MODULE}.run_auto_merge") as mock_merge,
        patch(f"{MODULE}.finish_auto_merge") as mock_finish,
    ):
        result = run_fix_conflict_workflow(PROJECT_DIR, PROVIDER, auto_merge=True)

    assert result == 1
    mock_fail.assert_called_once()
    mock_update.assert_not_called()
    mock_resolve.assert_not_called()
    mock_merge.assert_not_called()
    mock_finish.assert_not_called()


def test_auto_merge_off_does_not_call_helper() -> None:
    patches, _ = _patch_all([[{"mergeable_state": "clean"}]])
    with (
        patches[0],
        patches[1],
        patches[2],
        patches[3],
        patches[4] as mock_update,
        patches[5] as _mock_sleep,
        patches[6] as _mock_fail,
        patch(f"{MODULE}.run_auto_merge") as mock_merge,
        patch(f"{MODULE}.finish_auto_merge") as mock_finish,
    ):
        result = run_fix_conflict_workflow(PROJECT_DIR, PROVIDER, auto_merge=False)

    assert result == 0
    mock_update.assert_called_once_with(
        PROJECT_DIR, "fixing_merge_conflict", "pr_created"
    )
    mock_merge.assert_not_called()
    mock_finish.assert_not_called()


def test_passes_llm_args_to_fallback_helper() -> None:
    patches, _ = _patch_all([[{"mergeable_state": "clean"}]])
    with (
        patches[0],
        patches[2],
        patches[3],
        patches[4],
        patches[5],
        patches[6],
        patches[1] as mock_rebase,
    ):
        result = run_fix_conflict_workflow(
            PROJECT_DIR, PROVIDER, "mcp.json", "settings.json"
        )

    assert result == 0
    mock_rebase.assert_called_once_with(
        PROJECT_DIR, PROVIDER, "mcp.json", "settings.json"
    )


def test_final_label_failure_returns_1_without_net() -> None:
    patches, _ = _patch_all([[{"mergeable_state": "clean"}]])
    with (
        patches[0],
        patches[1],
        patches[2],
        patches[3] as mock_net,
        patches[4] as mock_update,
        patches[5] as _mock_sleep,
        patches[6] as mock_fail,
    ):
        mock_update.return_value = 1
        result = run_fix_conflict_workflow(PROJECT_DIR, PROVIDER)

    assert result == 1
    mock_update.assert_called_once()
    mock_fail.assert_not_called()
    mock_net.assert_not_called()


def test_branch_moved_verdict_adds_next_step_without_second_comment() -> None:
    patches, _ = _patch_all([[{"mergeable_state": "dirty"}]], _BRANCH_MOVED_OUTCOME)
    with (
        patches[0],
        patches[1],
        patches[2],
        patches[3],
        patches[4],
        patches[5],
        patches[6] as mock_fail,
        patch(_BRANCH_HEAD, return_value=(BRANCH_NAME, "abc1234")),
        patch(f"{MODULE}.post_issue_comment") as mock_post,
    ):
        result = run_fix_conflict_workflow(PROJECT_DIR, PROVIDER)

    assert result == 1
    mock_fail.assert_called_once()
    assert f"**Next step:** {BRANCH_MOVED_NEXT_STEP}" in mock_fail.call_args[0][1]
    mock_post.assert_not_called()


def test_other_reason_verdict_has_no_next_step() -> None:
    patches, _ = _patch_all(
        [[{"mergeable_state": "dirty"}]],
        RebaseOutcome("conflict", "main", "abc1234", ("a.py",)),
    )
    with (
        patches[0],
        patches[1],
        patches[2],
        patches[3],
        patches[4],
        patches[5],
        patches[6] as mock_fail,
        patch(_BRANCH_HEAD, return_value=(BRANCH_NAME, "abc1234")),
        patch(f"{MODULE}.post_issue_comment") as mock_post,
    ):
        result = run_fix_conflict_workflow(PROJECT_DIR, PROVIDER)

    assert result == 1
    assert "**Next step:**" not in mock_fail.call_args[0][1]
    mock_post.assert_not_called()


def test_branch_moved_without_verdict_comments_and_goes_to_pr_created() -> None:
    llm_detail = "Branch check failed; nothing pushed; pre-rebase state restored"
    patches, _ = _patch_all(
        [[{"mergeable_state": "clean"}]],
        RebaseOutcome("branch_moved", "main", "abc1234", llm_detail=llm_detail),
    )
    with (
        patches[0],
        patches[1],
        patches[2],
        patches[3],
        patches[4] as mock_update,
        patches[5] as _mock_sleep,
        patches[6] as mock_fail,
        patch(_BRANCH_HEAD, return_value=(BRANCH_NAME, "abc1234")),
        patch(f"{MODULE}.post_issue_comment") as mock_post,
    ):
        result = run_fix_conflict_workflow(PROJECT_DIR, PROVIDER)

    assert result == 0
    mock_post.assert_called_once()
    project_dir, issue_number, comment = mock_post.call_args[0]
    assert project_dir == PROJECT_DIR
    assert issue_number == 123
    assert comment.splitlines()[0] == "## ❌ Fix Conflict Failed"
    assert "**Stage:** Rebase" in comment
    assert f"**Reason:** {BRANCH_MOVED_REASON}" in comment
    assert f"**LLM rebase:** {llm_detail}" in comment
    assert f"**Next step:** {BRANCH_MOVED_NEXT_STEP}" in comment
    mock_update.assert_called_once_with(
        PROJECT_DIR, "fixing_merge_conflict", "pr_created"
    )
    mock_fail.assert_not_called()


def test_branch_moved_without_verdict_comments_before_auto_merge() -> None:
    patches, _ = _patch_all([[{"mergeable_state": "clean"}]], _BRANCH_MOVED_OUTCOME)
    calls = MagicMock()
    with (
        patches[0],
        patches[1],
        patches[2],
        patches[3],
        patches[4],
        patches[5],
        patches[6],
        patch(_BRANCH_HEAD, return_value=(BRANCH_NAME, "abc1234")),
        patch(f"{MODULE}.post_issue_comment") as mock_post,
        patch(f"{MODULE}.resolve_merge_issue_number", return_value=123),
        patch(f"{MODULE}.run_auto_merge") as mock_merge,
        patch(f"{MODULE}.finish_auto_merge", return_value=0),
    ):
        calls.attach_mock(mock_post, "comment")
        calls.attach_mock(mock_merge, "merge")
        result = run_fix_conflict_workflow(PROJECT_DIR, PROVIDER, auto_merge=True)

    assert result == 0
    assert [c[0] for c in calls.mock_calls] == ["comment", "merge"]


def test_branch_moved_on_branch_without_issue_number_skips_comment() -> None:
    patches, _ = _patch_all([[{"mergeable_state": "clean"}]], _BRANCH_MOVED_OUTCOME)
    with (
        patch(f"{MODULE}.get_current_branch_name", return_value="no-number"),
        patches[1],
        patches[2],
        patches[3],
        patches[4] as mock_update,
        patches[5] as _mock_sleep,
        patches[6] as _mock_fail,
        patch(f"{MODULE}.post_issue_comment") as mock_post,
    ):
        result = run_fix_conflict_workflow(PROJECT_DIR, PROVIDER)

    assert result == 0
    mock_post.assert_not_called()
    mock_update.assert_called_once_with(
        PROJECT_DIR, "fixing_merge_conflict", "pr_created"
    )


def test_settled_ok_rebase_posts_no_comment() -> None:
    patches, _ = _patch_all([[{"mergeable_state": "clean"}]])
    with (
        patches[0],
        patches[1],
        patches[2],
        patches[3],
        patches[4],
        patches[5],
        patches[6],
        patch(f"{MODULE}.post_issue_comment") as mock_post,
    ):
        result = run_fix_conflict_workflow(PROJECT_DIR, PROVIDER)

    assert result == 0
    mock_post.assert_not_called()


def test_no_current_branch_returns_1_without_rebase() -> None:
    with (
        patch(f"{MODULE}.get_current_branch_name", return_value=None),
        patch(
            f"{MODULE}.rebase_with_llm_fallback",
            return_value=RebaseOutcome("ok", "main", "abc1234"),
        ) as mock_rebase,
    ):
        result = run_fix_conflict_workflow(PROJECT_DIR, PROVIDER)

    assert result == 1
    mock_rebase.assert_not_called()


def test_unexpected_exception_is_caught_and_returns_1() -> None:
    with (
        patch(f"{MODULE}.get_current_branch_name", side_effect=RuntimeError("boom")),
        patch(_SHARED_HANDLER) as mock_shared,
        patch(_BRANCH_HEAD, return_value=("feat", "abc1234")),
    ):
        result = run_fix_conflict_workflow(PROJECT_DIR, PROVIDER)

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
            run_fix_conflict_workflow(PROJECT_DIR, PROVIDER)

    mock_shared.assert_called_once()
    netted_failure = mock_shared.call_args[0][0]
    assert netted_failure.category == "merge_conflict_failed"
