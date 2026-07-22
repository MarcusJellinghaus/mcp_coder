"""Static configuration for the two review workflows.

The shared review engine (Step 7) is driven by a :class:`ReviewConfig` instance
rather than branching on the workflow name. ``review-implementation`` and
``review-plan`` differ in only a handful of values (label ids, prompt headers,
log naming, and two behaviour booleans), so both are expressed as frozen
:class:`ReviewConfig` instances here.

The ``failure_labels`` mapping keeps per-workflow terminal labels as plain data
(``reason -> label internal_id``) so that ``handle_workflow_failure`` — which
already takes label-id strings — needs no per-workflow enum.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ReviewConfig:
    """Static description of one review workflow.

    Attributes:
        name: Workflow verb, ``"review-implementation"`` or ``"review-plan"``.
        log_stem: Stem for the per-run log file
            (``pr_info/{log_stem}_review_log_{n}.md``).
        session_dir_name: Directory name for persisted LLM sessions.
        reviewer_prompt_header: ``prompts.md`` header for the reviewer session.
        supervisor_prompt_header: ``prompts.md`` header for the supervisor
            session (shared across both workflows).
        busy_label_id: ``bot_busy`` label held while the workflow runs.
        success_label_id: Terminal label applied on a successful review.
        escalate_label_id: Label applied when the supervisor escalates to a
            human.
        inject_base_branch: Whether the reviewer prompt is given a base branch
            to diff against (implementation only).
        run_after_steps: Whether after-steps (rebase + CI) run (implementation
            only).
        failure_labels: Mapping of failure ``reason`` to terminal label
            ``internal_id``.
    """

    name: str
    log_stem: str
    session_dir_name: str
    reviewer_prompt_header: str
    supervisor_prompt_header: str
    busy_label_id: str
    success_label_id: str
    escalate_label_id: str
    inject_base_branch: bool
    run_after_steps: bool
    failure_labels: dict[str, str]


REVIEW_IMPLEMENTATION = ReviewConfig(
    name="review-implementation",
    log_stem="implementation",
    session_dir_name="review_implementation_sessions",
    reviewer_prompt_header="Review Implementation Reviewer",
    supervisor_prompt_header="Review Supervisor",
    busy_label_id="code_reviewing",
    success_label_id="ready_pr",
    escalate_label_id="code_review",
    inject_base_branch=True,
    run_after_steps=True,
    failure_labels={
        "general": "code_review_failed",
        "rounds": "code_review_rounds",
        "timeout": "code_review_timeout",
        "mcp": "code_review_mcp",
        "ci": "code_review_ci",
    },
)


REVIEW_PLAN = ReviewConfig(
    name="review-plan",
    log_stem="plan",
    session_dir_name="review_plan_sessions",
    reviewer_prompt_header="Review Plan Reviewer",
    supervisor_prompt_header="Review Supervisor",
    busy_label_id="plan_reviewing",
    success_label_id="plan_ready",
    escalate_label_id="plan_review",
    inject_base_branch=False,
    run_after_steps=False,
    failure_labels={
        "general": "plan_review_failed",
        "rounds": "plan_review_rounds",
        "timeout": "plan_review_timeout",
        "mcp": "plan_review_mcp",
    },
)
