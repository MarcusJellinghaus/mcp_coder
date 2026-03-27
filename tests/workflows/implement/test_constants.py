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

    def test_build_url_default_none(self) -> None:
        """build_url defaults to None."""
        failure = WorkflowFailure(
            category=FailureCategory.GENERAL, stage="test", message="msg"
        )
        assert failure.build_url is None

    def test_elapsed_time_default_none(self) -> None:
        """elapsed_time defaults to None."""
        failure = WorkflowFailure(
            category=FailureCategory.GENERAL, stage="test", message="msg"
        )
        assert failure.elapsed_time is None

    def test_build_url_set(self) -> None:
        """build_url can be set."""
        failure = WorkflowFailure(
            category=FailureCategory.GENERAL,
            stage="test",
            message="msg",
            build_url="https://jenkins.example.com/job/123/console",
        )
        assert failure.build_url == "https://jenkins.example.com/job/123/console"

    def test_elapsed_time_set(self) -> None:
        """elapsed_time can be set."""
        failure = WorkflowFailure(
            category=FailureCategory.GENERAL,
            stage="test",
            message="msg",
            elapsed_time=754.3,
        )
        assert failure.elapsed_time == 754.3

    def test_frozen_new_fields(self) -> None:
        """New fields are also frozen."""
        failure = WorkflowFailure(
            category=FailureCategory.GENERAL,
            stage="test",
            message="msg",
            build_url="url",
            elapsed_time=1.0,
        )
        with pytest.raises(dataclasses.FrozenInstanceError):
            failure.build_url = "other"  # type: ignore[misc]
