"""Tests for FailureCategory enum and WorkflowFailure dataclass."""

import dataclasses

import pytest

from mcp_coder.workflows.implement.constants import FailureCategory, WorkflowFailure


class TestFailureCategory:
    """Tests for FailureCategory enum."""

    def test_values_match_label_ids(self) -> None:
        """FailureCategory values must match labels.json internal_id values."""
        assert FailureCategory.GENERAL.value == "implementing_failed"
        assert FailureCategory.CI_FIX_EXHAUSTED.value == "ci_fix_needed"
        assert FailureCategory.LLM_TIMEOUT.value == "llm_timeout"


class TestWorkflowFailure:
    """Tests for WorkflowFailure frozen dataclass."""

    def test_frozen(self) -> None:
        """WorkflowFailure should be immutable."""
        wf = WorkflowFailure(
            category=FailureCategory.GENERAL, stage="test", message="msg"
        )
        with pytest.raises(dataclasses.FrozenInstanceError):
            wf.stage = "other"  # type: ignore[misc]

    def test_defaults(self) -> None:
        """Default task counts should be 0."""
        wf = WorkflowFailure(
            category=FailureCategory.GENERAL, stage="test", message="msg"
        )
        assert wf.tasks_completed == 0
        assert wf.tasks_total == 0

    def test_with_task_counts(self) -> None:
        """Task counts should be settable."""
        wf = WorkflowFailure(
            category=FailureCategory.LLM_TIMEOUT,
            stage="task impl",
            message="timed out",
            tasks_completed=2,
            tasks_total=5,
        )
        assert wf.tasks_completed == 2
        assert wf.tasks_total == 5
