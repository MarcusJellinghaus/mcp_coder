"""Tests for the layout of ``TASK_TRACKER_TEMPLATE``."""

from mcp_coder.workflow_utils.task_tracker import TASK_TRACKER_TEMPLATE
from mcp_coder.workflow_utils.task_tracker_classify import (
    TrackerState,
    classify_tracker_content,
)


def test_bold_labels_are_followed_by_a_blank_line() -> None:
    """A markdown formatter leaves the template unchanged only with these gaps."""
    lines = TASK_TRACKER_TEMPLATE.splitlines()
    label_indices = [
        i
        for i, line in enumerate(lines)
        if line.startswith("**") and line.endswith(":**")
    ]

    assert len(label_indices) == 2
    for i in label_indices:
        assert lines[i + 1] == "", f"no blank line after {lines[i]!r}"


def test_template_still_classifies_as_empty() -> None:
    """The template is the empty tracker that preparation fills in."""
    state, violations = classify_tracker_content(TASK_TRACKER_TEMPLATE)

    assert state is TrackerState.EMPTY
    assert violations == []
