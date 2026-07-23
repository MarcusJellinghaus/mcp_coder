"""Shared review engine core loop.

One loop drives both review workflows; the differences (``review-plan`` vs
``review-implementation``) are carried entirely by the :class:`ReviewConfig`
instance passed in (label ids, prompt headers, log naming, and two behaviour
booleans). This module realizes **`review-plan`** fully (``run_after_steps`` is
``False``, so ``_after_steps`` is a no-op here); Step 8 fills the after-steps
hook to realize ``review-implementation``.

Sessions emulate the interactive supervisor→subagent pattern in pure Python:

* **Reviewer** — a *fresh* session per round (``prompt_llm(session_id=None)``).
  It self-fetches the diff / plan + issue + knowledge base via MCP tools and
  returns a structured report.
* **Supervisor** — a *persistent* session captured on round 1 and re-captured
  from each response (the discipline proven in Step 1), threaded via
  ``session_id=`` on every later turn.

``mcp_config`` is threaded into *both* calls (the reviewer edits via
``mcp-workspace`` tools). The supervisor's machine-readable verdict is parsed
by :func:`parse_verdict`; a ``None`` result is repaired up to
:data:`VERDICT_REPAIR_RETRIES` times before falling to the ``general`` failure.
"""

import logging
from pathlib import Path

from mcp_coder.constants import PROMPTS_FILE_PATH
from mcp_coder.llm.env import prepare_llm_environment
from mcp_coder.llm.interface import LLMTimeoutError, prompt_llm
from mcp_coder.llm.providers.claude.claude_code_cli import McpServersUnavailableError
from mcp_coder.llm.types import LLMResponseDict
from mcp_coder.mcp_workspace_git import (
    extract_issue_number_from_branch,
    get_current_branch_name,
    get_latest_commit_sha,
    is_working_directory_clean,
)
from mcp_coder.mcp_workspace_github import IssueManager
from mcp_coder.prompt_manager import get_prompt
from mcp_coder.workflow_steps.ci import check_and_fix_ci
from mcp_coder.workflow_steps.commit import commit_changes, push_changes, run_formatters
from mcp_coder.workflow_steps.constants import LLM_INACTIVITY_TIMEOUT_SECONDS
from mcp_coder.workflow_steps.rebase import _attempt_rebase_and_push
from mcp_coder.workflow_utils.base_branch import detect_base_branch
from mcp_coder.workflow_utils.failure_handling import (
    WorkflowFailure,
    handle_workflow_failure,
)
from mcp_coder.workflow_utils.label_transitions import update_workflow_label

from .config import ReviewConfig
from .review_log import next_run_number, write_round_log
from .verdict import Verdict, parse_verdict

logger = logging.getLogger(__name__)

REVIEW_MAX_ROUNDS = 5
VERDICT_REPAIR_RETRIES = 2

_REPAIR_PROMPT = (
    "Your previous response did not contain a valid verdict. Reply with ONLY a "
    "fenced ```json block containing an object with a `decision` field "
    '("dismiss", "tasks", or "escalate") and nothing else.'
)

# CI-as-finding note (implementation lane only): when a mid-loop `tasks` round
# leaves CI red, this text is carried into the *next* fresh reviewer prompt so
# the reviewer re-surfaces the failure and the supervisor triages it within the
# rounds cap (rather than failing the run immediately).
_CI_NOTE = (
    "NOTE — open CI finding: the most recent CI run on this branch is red and "
    "could not be auto-fixed. Treat this as a finding: investigate the CI "
    "failure yourself and include it in your structured report."
)


def run_review_workflow(
    config: ReviewConfig,
    project_dir: Path,
    provider: str,
    mcp_config: str | None = None,
    settings_file: str | None = None,
    execution_dir: Path | None = None,
    update_issue_labels: bool = False,
    post_issue_comments: bool = False,
) -> int:
    """Run the shared review loop and return a process exit code.

    Args:
        config: Static description of the review workflow to run.
        project_dir: Repository root; git ops and file writes target this.
        provider: LLM provider (e.g. ``"claude"``).
        mcp_config: Optional path to an MCP configuration file (threaded into
            both the reviewer and supervisor sessions).
        settings_file: Optional path to a Claude settings file.
        execution_dir: Optional working directory for the LLM subprocess.
        update_issue_labels: When True, apply GitHub label transitions.
        post_issue_comments: When True, post a failure comment on the error path.

    Returns:
        ``0`` on success or a needs-human handoff (escalate / rebase); ``1`` on
        any error (unparseable verdict, timeout, MCP down, rounds cap).
    """
    issue_number, base_branch = _resolve_context(config, project_dir)
    run_number = next_run_number(project_dir, config)
    supervisor_sid: str | None = None
    # Carries a red mid-loop CI result into the next reviewer prompt; when it is
    # still set at the rounds cap the terminal reason is "ci", not "rounds".
    pending_ci_note: str | None = None

    for round_number in range(1, REVIEW_MAX_ROUNDS + 1):
        sha_before = get_latest_commit_sha(project_dir)

        # Reviewer: a fresh session per round.
        try:
            report_response = _run_reviewer(
                config,
                project_dir,
                provider,
                mcp_config,
                settings_file,
                execution_dir,
                issue_number,
                base_branch,
                session_id=None,
                tasks=None,
                ci_note=pending_ci_note,
            )
        except (LLMTimeoutError, McpServersUnavailableError) as exc:
            return _fail(
                config,
                project_dir,
                _reason_for_exception(exc),
                update_issue_labels=update_issue_labels,
                post_issue_comments=post_issue_comments,
            )
        reviewer_sid = report_response["session_id"]
        report = report_response["text"]

        # Supervisor: persistent session, verdict parsed with repair retries.
        try:
            verdict, supervisor_sid = _get_verdict(
                config,
                project_dir,
                provider,
                mcp_config,
                settings_file,
                execution_dir,
                supervisor_sid,
                report,
            )
        except (LLMTimeoutError, McpServersUnavailableError) as exc:
            return _fail(
                config,
                project_dir,
                _reason_for_exception(exc),
                update_issue_labels=update_issue_labels,
                post_issue_comments=post_issue_comments,
            )
        if verdict is None:
            return _fail(
                config,
                project_dir,
                "general",
                update_issue_labels=update_issue_labels,
                post_issue_comments=post_issue_comments,
            )

        if verdict.decision == "dismiss":
            reason = _after_steps(
                config,
                project_dir,
                provider,
                mcp_config,
                settings_file,
                execution_dir,
                is_dismiss=True,
            )
            if reason == "rebase":
                write_round_log(
                    project_dir,
                    config,
                    run_number,
                    round_number,
                    findings=report,
                    decisions=str(verdict),
                    changes="rebase-needed",
                    escalate_reason="rebase",
                )
                _set_label(
                    config,
                    project_dir,
                    config.escalate_label_id,
                    update_issue_labels,
                )
                return 0
            if reason:
                return _fail(
                    config,
                    project_dir,
                    reason,
                    update_issue_labels=update_issue_labels,
                    post_issue_comments=post_issue_comments,
                )
            write_round_log(
                project_dir,
                config,
                run_number,
                round_number,
                findings=report,
                decisions=str(verdict),
                changes="dismiss",
            )
            _set_label(
                config, project_dir, config.success_label_id, update_issue_labels
            )
            return 0

        if verdict.decision == "escalate":
            write_round_log(
                project_dir,
                config,
                run_number,
                round_number,
                findings=report,
                decisions=str(verdict),
                changes="escalate",
                escalate_reason=verdict.escalate_reason,
            )
            _set_label(
                config, project_dir, config.escalate_label_id, update_issue_labels
            )
            return 0

        # decision == "tasks": resume the reviewer to apply the fixes.
        try:
            _run_reviewer(
                config,
                project_dir,
                provider,
                mcp_config,
                settings_file,
                execution_dir,
                issue_number,
                base_branch,
                session_id=reviewer_sid,
                tasks=verdict.tasks,
                ci_note=None,
            )
        except (LLMTimeoutError, McpServersUnavailableError) as exc:
            return _fail(
                config,
                project_dir,
                _reason_for_exception(exc),
                update_issue_labels=update_issue_labels,
                post_issue_comments=post_issue_comments,
            )
        run_formatters(project_dir)
        commit_changes(project_dir, provider)
        push_changes(project_dir)

        reason = _after_steps(
            config,
            project_dir,
            provider,
            mcp_config,
            settings_file,
            execution_dir,
            is_dismiss=False,
        )
        if reason == "rebase":
            write_round_log(
                project_dir,
                config,
                run_number,
                round_number,
                findings=report,
                decisions=str(verdict),
                changes="rebase-needed",
                escalate_reason="rebase",
            )
            _set_label(
                config, project_dir, config.escalate_label_id, update_issue_labels
            )
            return 0
        if reason == "ci":
            # Mid-loop red CI is a finding, not a terminal failure: carry it into
            # the next fresh reviewer prompt and keep looping (the supervisor
            # triages it within the rounds cap).
            pending_ci_note = _CI_NOTE
        elif reason:
            return _fail(
                config,
                project_dir,
                reason,
                update_issue_labels=update_issue_labels,
                post_issue_comments=post_issue_comments,
            )
        else:
            # After-steps clean (CI green / nothing to do): clear any stale note.
            pending_ci_note = None

        # Backstop (layer C): a `tasks` round that changed nothing is a silent
        # no-op — log it, but let the round count toward the cap and keep going
        # (the next fresh reviewer re-surfaces the unmet finding, layer A).
        changed = get_latest_commit_sha(
            project_dir
        ) != sha_before or not is_working_directory_clean(project_dir)
        write_round_log(
            project_dir,
            config,
            run_number,
            round_number,
            findings=report,
            decisions=str(verdict),
            changes="applied" if changed else "no-op",
        )

    # Rounds cap: a still-open CI finding wins over the plain rounds reason so
    # the terminal label is `17f-ci` rather than `17f-rounds`.
    cap_reason = "ci" if pending_ci_note else "rounds"
    return _fail(
        config,
        project_dir,
        cap_reason,
        update_issue_labels=update_issue_labels,
        post_issue_comments=post_issue_comments,
    )


def _resolve_context(
    config: ReviewConfig, project_dir: Path
) -> tuple[int | None, str | None]:
    """Resolve the issue number and (impl only) the base branch to diff against.

    Args:
        config: The review workflow config.
        project_dir: Repository root.

    Returns:
        ``(issue_number, base_branch)``. ``base_branch`` is ``None`` when the
        workflow does not inject one (``review-plan``); for
        ``review-implementation`` (``inject_base_branch``) it is the detected
        base branch the reviewer diffs the feature branch against.
    """
    issue_number: int | None = None
    branch_name = get_current_branch_name(project_dir)
    if branch_name:
        issue_number = extract_issue_number_from_branch(branch_name)

    base_branch: str | None = None
    if config.inject_base_branch:
        base_branch = detect_base_branch(project_dir)
    return issue_number, base_branch


def _run_reviewer(
    config: ReviewConfig,
    project_dir: Path,
    provider: str,
    mcp_config: str | None,
    settings_file: str | None,
    execution_dir: Path | None,
    issue_number: int | None,
    base_branch: str | None,
    session_id: str | None,
    tasks: list[str] | None,
    ci_note: str | None = None,
) -> LLMResponseDict:
    """Run one reviewer turn — a fresh review, or a resume that applies tasks.

    When ``tasks`` is ``None`` this is the fresh per-round review: the reviewer
    prompt header is loaded and its ``{issue_number}`` / ``{base_branch}``
    placeholders substituted. When ``tasks`` is provided, the existing reviewer
    session (``session_id``) is resumed with the concrete fix instructions.

    Args:
        config: The review workflow config.
        project_dir: Repository root.
        provider: LLM provider.
        mcp_config: Optional MCP config path (threaded to the reviewer session).
        settings_file: Optional Claude settings file.
        execution_dir: Optional LLM subprocess working directory.
        issue_number: Issue number injected into the reviewer prompt.
        base_branch: Base branch injected into the reviewer prompt (impl only).
        session_id: ``None`` for a fresh review, else the reviewer session to
            resume for task application.
        tasks: Fix instructions to apply, or ``None`` for a fresh review.
        ci_note: Optional CI-as-finding note appended to a *fresh* reviewer
            prompt (see :data:`_CI_NOTE`); ignored on a task-application resume.

    Returns:
        The reviewer's :class:`LLMResponseDict`.
    """
    env_vars = prepare_llm_environment(project_dir)
    cwd = str(execution_dir) if execution_dir else str(project_dir)

    if tasks is None:
        prompt = get_prompt(str(PROMPTS_FILE_PATH), config.reviewer_prompt_header)
        prompt = prompt.replace(
            "{issue_number}", str(issue_number) if issue_number is not None else "?"
        )
        prompt = prompt.replace("{base_branch}", base_branch or "")
        if ci_note:
            prompt = f"{prompt}\n\n{ci_note}"
    else:
        task_lines = "\n".join(f"- {task}" for task in tasks)
        prompt = (
            "Apply the following fixes now, editing the relevant files with the "
            "`mcp-workspace` edit tools, then re-emit your structured report:\n"
            f"{task_lines}"
        )

    return prompt_llm(
        prompt,
        provider=provider,
        session_id=session_id,
        timeout=LLM_INACTIVITY_TIMEOUT_SECONDS,
        env_vars=env_vars,
        execution_dir=cwd,
        mcp_config=mcp_config,
        settings_file=settings_file,
    )


def _get_verdict(
    config: ReviewConfig,
    project_dir: Path,
    provider: str,
    mcp_config: str | None,
    settings_file: str | None,
    execution_dir: Path | None,
    supervisor_sid: str | None,
    report: str,
) -> tuple[Verdict | None, str | None]:
    """Ask the supervisor to triage the report, repairing an unparseable verdict.

    The supervisor is a persistent session: it is resumed with
    ``supervisor_sid`` and its returned session id is re-captured for the next
    turn. A ``None`` parse is repaired up to :data:`VERDICT_REPAIR_RETRIES`
    times before giving up.

    Args:
        config: The review workflow config.
        project_dir: Repository root.
        provider: LLM provider.
        mcp_config: Optional MCP config path (threaded to the supervisor).
        settings_file: Optional Claude settings file.
        execution_dir: Optional LLM subprocess working directory.
        supervisor_sid: Supervisor session id to resume, or ``None`` on round 1.
        report: The reviewer's structured findings text.

    Returns:
        ``(verdict, next_supervisor_sid)`` where ``verdict`` is ``None`` if it
        could not be parsed after all repair retries.
    """
    env_vars = prepare_llm_environment(project_dir)
    cwd = str(execution_dir) if execution_dir else str(project_dir)

    header = get_prompt(str(PROMPTS_FILE_PATH), config.supervisor_prompt_header)
    prompt = f"{header}\n\n## Reviewer report\n\n{report}"

    current_sid = supervisor_sid
    attempts = 0
    while True:
        response = prompt_llm(
            prompt,
            provider=provider,
            session_id=current_sid,
            timeout=LLM_INACTIVITY_TIMEOUT_SECONDS,
            env_vars=env_vars,
            execution_dir=cwd,
            mcp_config=mcp_config,
            settings_file=settings_file,
        )
        current_sid = response["session_id"] or current_sid
        verdict = parse_verdict(response["text"])
        if verdict is not None:
            return verdict, current_sid
        if attempts >= VERDICT_REPAIR_RETRIES:
            return None, current_sid
        attempts += 1
        prompt = _REPAIR_PROMPT


def _after_steps(
    config: ReviewConfig,
    project_dir: Path,
    provider: str,
    mcp_config: str | None,
    settings_file: str | None,
    execution_dir: Path | None,
    is_dismiss: bool,
) -> str | None:
    """Run the after-steps (rebase + CI) for the implementation lane.

    ``review-plan`` has ``run_after_steps=False`` so this is a no-op there. For
    ``review-implementation`` it enforces two gates in order:

    1. **Rebase gate (mandated — never success on an unresolved rebase):** the
       branch is rebased onto its base branch via ``_attempt_rebase_and_push``.
       If that cannot complete cleanly (e.g. a merge conflict) the return is
       ``"rebase"``, which the caller routes to a needs-human handoff
       (``07:code-review``) — never a success and never a failure label.
    2. **CI gate:** ``check_and_fix_ci`` runs its own retries (reusing
       ``implement``'s prompt headers, overriding only ``session_dir_name``). A
       green result returns ``None``. A red result returns ``"ci"``: on the
       final dismiss gate (``is_dismiss``) the caller treats that as a terminal
       ``17f-ci`` failure; mid-loop the caller instead carries it forward as a
       finding (see :data:`_CI_NOTE`).

    Args:
        config: The review workflow config.
        project_dir: Repository root.
        provider: LLM provider.
        mcp_config: Optional MCP config path.
        settings_file: Optional Claude settings file.
        execution_dir: Optional LLM subprocess working directory.
        is_dismiss: Whether this runs on the final dismiss gate (vs mid-loop).
            Logged for diagnostics; the caller owns the terminal-vs-finding
            interpretation of a red CI result.

    Returns:
        A failure reason (``"rebase"`` / ``"ci"`` / ``"timeout"`` / ``"mcp"``)
        or ``None`` when the after-steps are clean or there is nothing to do.
    """
    if not config.run_after_steps:
        return None

    # --- rebase gate (mandated: never success on an unresolved rebase) ---
    if not _attempt_rebase_and_push(project_dir):
        # NotYetImplemented (#1066): a conflict-resolving automatic
        # ``mcp-coder git-tool rebase`` attempt slots in HERE once #1066 ships
        # (before the needs-human fallback). Until then a needs-rebase /
        # unresolvable-conflict outcome simply routes to needs-human
        # (``07:code-review``) and is never a success.
        logger.info("Rebase could not complete cleanly; routing to needs-human")
        return "rebase"

    # --- CI gate ---
    branch = get_current_branch_name(project_dir)
    if not branch:
        return None
    try:
        ci_ok = check_and_fix_ci(
            project_dir=project_dir,
            branch=branch,
            provider=provider,
            mcp_config=mcp_config,
            settings_file=settings_file,
            execution_dir=execution_dir,
            session_dir_name=config.session_dir_name,
        )
    except LLMTimeoutError:
        return "timeout"
    except McpServersUnavailableError:
        return "mcp"
    if ci_ok:
        return None
    if not is_dismiss:
        logger.info("CI is red mid-loop; carrying it forward as a review finding")
    return "ci"


def _set_label(
    config: ReviewConfig,
    project_dir: Path,
    to_label_id: str,
    update_issue_labels: bool,
) -> None:
    """Apply a workflow label transition from the busy label, if gating allows.

    Mirrors ``implement/core.py``: gated on ``update_issue_labels`` and given a
    fresh ``IssueManager`` as its first arg, wrapped so a label failure never
    breaks the workflow.

    Args:
        config: The review workflow config (provides ``busy_label_id``).
        project_dir: Repository root.
        to_label_id: Terminal label id to transition to.
        update_issue_labels: When False, this is a no-op.
    """
    if not update_issue_labels:
        return
    try:
        issue_manager = IssueManager(project_dir)
        update_workflow_label(
            issue_manager,
            from_label_id=config.busy_label_id,
            to_label_id=to_label_id,
        )
    except Exception as exc:  # pylint: disable=broad-exception-caught
        logger.warning("Failed to update issue label to '%s': %s", to_label_id, exc)


def _fail(
    config: ReviewConfig,
    project_dir: Path,
    reason: str,
    *,
    update_issue_labels: bool,
    post_issue_comments: bool,
) -> int:
    """Route a terminal error through the shared failure handler; return ``1``.

    Args:
        config: The review workflow config (provides busy + failure labels).
        project_dir: Repository root.
        reason: Failure reason key into ``config.failure_labels``.
        update_issue_labels: Whether to apply the failure label transition.
        post_issue_comments: Whether to post a failure comment on the issue.

    Returns:
        Always ``1``.
    """
    category = config.failure_labels.get(reason, config.failure_labels["general"])
    message = f"{config.name} review failed: {reason}"
    failure = WorkflowFailure(
        category=category,
        stage="Review",
        message=message,
    )
    comment_body = f"❌ {message}"
    handle_workflow_failure(
        failure,
        comment_body,
        project_dir,
        from_label_id=config.busy_label_id,
        update_issue_labels=update_issue_labels,
        post_issue_comments=post_issue_comments,
    )
    return 1


def _reason_for_exception(exc: Exception) -> str:
    """Map an LLM exception to a local failure reason (no cross-workflow import).

    Args:
        exc: The exception raised by an ``prompt_llm`` call.

    Returns:
        ``"timeout"`` for :class:`LLMTimeoutError`, ``"mcp"`` for
        :class:`McpServersUnavailableError`, else ``"general"``.
    """
    if isinstance(exc, LLMTimeoutError):
        return "timeout"
    if isinstance(exc, McpServersUnavailableError):
        return "mcp"
    return "general"
