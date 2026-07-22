"""Tests for the review workflow config instances (Step 6)."""

import dataclasses

import pytest

from mcp_coder.workflows.review.config import (
    REVIEW_IMPLEMENTATION,
    REVIEW_PLAN,
    ReviewConfig,
)


class TestReviewImplementation:
    """Field values for the ``review-implementation`` config."""

    def test_identity_and_naming(self) -> None:
        assert REVIEW_IMPLEMENTATION.name == "review-implementation"
        assert REVIEW_IMPLEMENTATION.log_stem == "implementation"
        assert (
            REVIEW_IMPLEMENTATION.session_dir_name == "review_implementation_sessions"
        )

    def test_prompt_headers(self) -> None:
        assert (
            REVIEW_IMPLEMENTATION.reviewer_prompt_header
            == "Review Implementation Reviewer"
        )
        assert REVIEW_IMPLEMENTATION.supervisor_prompt_header == "Review Supervisor"

    def test_label_ids_match_step_2(self) -> None:
        assert REVIEW_IMPLEMENTATION.busy_label_id == "code_reviewing"
        assert REVIEW_IMPLEMENTATION.success_label_id == "ready_pr"
        assert REVIEW_IMPLEMENTATION.escalate_label_id == "code_review"

    def test_behaviour_flags(self) -> None:
        assert REVIEW_IMPLEMENTATION.inject_base_branch is True
        assert REVIEW_IMPLEMENTATION.run_after_steps is True

    def test_failure_labels(self) -> None:
        assert REVIEW_IMPLEMENTATION.failure_labels == {
            "general": "code_review_failed",
            "rounds": "code_review_rounds",
            "timeout": "code_review_timeout",
            "mcp": "code_review_mcp",
            "ci": "code_review_ci",
        }

    def test_has_ci_failure_key(self) -> None:
        assert REVIEW_IMPLEMENTATION.failure_labels["ci"] == "code_review_ci"


class TestReviewPlan:
    """Field values for the ``review-plan`` config."""

    def test_identity_and_naming(self) -> None:
        assert REVIEW_PLAN.name == "review-plan"
        assert REVIEW_PLAN.log_stem == "plan"
        assert REVIEW_PLAN.session_dir_name == "review_plan_sessions"

    def test_prompt_headers(self) -> None:
        assert REVIEW_PLAN.reviewer_prompt_header == "Review Plan Reviewer"
        assert REVIEW_PLAN.supervisor_prompt_header == "Review Supervisor"

    def test_label_ids_match_step_2(self) -> None:
        assert REVIEW_PLAN.busy_label_id == "plan_reviewing"
        assert REVIEW_PLAN.success_label_id == "plan_ready"
        assert REVIEW_PLAN.escalate_label_id == "plan_review"

    def test_behaviour_flags(self) -> None:
        assert REVIEW_PLAN.inject_base_branch is False
        assert REVIEW_PLAN.run_after_steps is False

    def test_failure_labels(self) -> None:
        assert REVIEW_PLAN.failure_labels == {
            "general": "plan_review_failed",
            "rounds": "plan_review_rounds",
            "timeout": "plan_review_timeout",
            "mcp": "plan_review_mcp",
        }

    def test_has_no_ci_failure_key(self) -> None:
        assert "ci" not in REVIEW_PLAN.failure_labels


class TestReviewConfigDataclass:
    """The dataclass itself is frozen."""

    def test_frozen(self) -> None:
        with pytest.raises(dataclasses.FrozenInstanceError):
            REVIEW_IMPLEMENTATION.name = "other"  # type: ignore[misc]

    def test_shared_supervisor_header(self) -> None:
        assert (
            REVIEW_IMPLEMENTATION.supervisor_prompt_header
            == REVIEW_PLAN.supervisor_prompt_header
        )

    def test_is_review_config_instances(self) -> None:
        assert isinstance(REVIEW_IMPLEMENTATION, ReviewConfig)
        assert isinstance(REVIEW_PLAN, ReviewConfig)
