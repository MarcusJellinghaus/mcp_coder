"""Tests for finish_auto_merge."""

from collections.abc import Iterator
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.workflow_steps.merge import MergeOutcome, finish_auto_merge

_MOD = "mcp_coder.workflow_steps.merge"
_FIELDS = (("Stage", "Auto-merge"), ("Error", "refused"))


class _Mocks:
    """Patched collaborators of finish_auto_merge, sharing one call-order parent."""

    def __init__(self, parent: MagicMock) -> None:
        self.parent = parent
        self.apply_final_label: MagicMock = parent.apply_final_label
        self.build_failure_comment: MagicMock = parent.build_failure_comment
        self.post_issue_comment: MagicMock = parent.post_issue_comment


@pytest.fixture()
def mocks() -> Iterator[_Mocks]:
    parent = MagicMock()
    with (
        patch(f"{_MOD}.apply_final_label", parent.apply_final_label),
        patch(f"{_MOD}.build_failure_comment", parent.build_failure_comment),
        patch(f"{_MOD}.post_issue_comment", parent.post_issue_comment),
    ):
        parent.apply_final_label.return_value = 0
        parent.build_failure_comment.return_value = "comment body"
        yield _Mocks(parent)


def _finish(
    outcome: MergeOutcome,
    *,
    issue_number: int | None = 42,
    update_issue_labels: bool = True,
    post_issue_comments: bool = True,
) -> int:
    return finish_auto_merge(
        Path("/fake"),
        outcome,
        from_label_id="fixing_ci",
        issue_number=issue_number,
        update_issue_labels=update_issue_labels,
        post_issue_comments=post_issue_comments,
    )


@pytest.mark.parametrize(
    ("label_id", "expected"),
    [
        ("merged", 0),
        ("pr_created", 0),
        ("failing_ci", 0),
        ("pr_merge_conflict", 1),
        ("merge_failed", 1),
    ],
)
def test_exit_code_by_label(mocks: _Mocks, label_id: str, expected: int) -> None:
    assert _finish(MergeOutcome(label_id)) == expected
    mocks.apply_final_label.assert_called_once_with(
        Path("/fake"), "fixing_ci", label_id, 42
    )


def test_label_write_failure_exits_1_even_when_merged(mocks: _Mocks) -> None:
    mocks.apply_final_label.return_value = 1

    assert _finish(MergeOutcome("merged")) == 1


@pytest.mark.parametrize(("label_id", "expected"), [("merged", 0), ("merge_failed", 1)])
def test_update_labels_false_skips_label(
    mocks: _Mocks, label_id: str, expected: int
) -> None:
    assert _finish(MergeOutcome(label_id), update_issue_labels=False) == expected
    mocks.apply_final_label.assert_not_called()


@pytest.mark.parametrize(("label_id", "expected"), [("merged", 0), ("merge_failed", 1)])
def test_no_issue_number_skips_label_and_comment(
    mocks: _Mocks, label_id: str, expected: int
) -> None:
    outcome = MergeOutcome(label_id, _FIELDS)

    assert _finish(outcome, issue_number=None) == expected
    mocks.apply_final_label.assert_not_called()
    mocks.post_issue_comment.assert_not_called()


def test_comment_posted_when_fields_and_enabled(mocks: _Mocks) -> None:
    _finish(MergeOutcome("merge_failed", _FIELDS))

    mocks.build_failure_comment.assert_called_once_with(
        Path("/fake"), title="Auto-merge", kind="Failed", fields=_FIELDS
    )
    mocks.post_issue_comment.assert_called_once_with(Path("/fake"), 42, "comment body")


def test_no_comment_without_fields(mocks: _Mocks) -> None:
    _finish(MergeOutcome("merged"))

    mocks.post_issue_comment.assert_not_called()


def test_no_comment_when_comments_disabled(mocks: _Mocks) -> None:
    _finish(MergeOutcome("merge_failed", _FIELDS), post_issue_comments=False)

    mocks.post_issue_comment.assert_not_called()


def test_label_applied_before_comment(mocks: _Mocks) -> None:
    _finish(MergeOutcome("pr_merge_conflict", _FIELDS))

    names = [c[0] for c in mocks.parent.mock_calls]
    assert names.index("apply_final_label") < names.index("post_issue_comment")
