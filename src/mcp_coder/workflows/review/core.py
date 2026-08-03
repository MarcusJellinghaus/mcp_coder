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
import time
from pathlib import Path

from mcp_coder.checks.branch_status import (
    BranchStatusReport,
    CIStatus,
    collect_branch_status,
)
from mcp_coder.mcp_workspace_git import (
    extract_issue_number_from_branch,
    get_current_branch_name,
    get_latest_commit_sha,
    is_working_directory_clean,
)
from mcp_coder.workflow_steps.ci import check_and_fix_ci
from mcp_coder.workflow_steps.commit import commit_changes, push_changes, run_formatters
from mcp_coder.workflow_steps.rebase import _attempt_rebase_and_push
from mcp_coder.workflow_utils.base_branch import detect_base_branch
from mcp_coder.workflow_utils.failure_handling import (
    llm_failure_reason,
    run_guarded,
)

from . import reviewer
from .config import ReviewConfig
from .handoff import _fail, _flush_round_log, _route_to_human, _set_label
from .review_log import next_run_number, write_round_log
from .severity import max_severity
from .verdict import Verdict

logger = logging.getLogger(__name__)

REVIEW_MAX_ROUNDS = 5
# Bounded inner retry on a whitespace-only reviewer report: re-invokes the
# fresh reviewer without consuming a round; on exhaustion the run fails general.
EMPTY_REPORT_RETRIES = 3

# CI-as-finding note (implementation lane only): when a mid-loop `tasks` round
# leaves CI red, this text is carried into the *next* fresh reviewer prompt so
# the reviewer re-surfaces the failure and the supervisor triages it within the
# rounds cap (rather than failing the run immediately).
_CI_NOTE = (
    "NOTE — open CI finding: the most recent CI run on this branch is red and "
    "could not be auto-fixed. Treat this as a finding: investigate the CI "
    "failure yourself and include it in your structured report. Treat this CI "
    "failure as `critical` severity in your structured report."
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
        ``0`` on success or a needs-human handoff (escalate / rebase / rounds
        cap — all route to the escalate recovery label); ``1`` on any error
        (unparseable verdict, timeout, MCP down, an open CI finding at the cap,
        commit-failed, push-failed).
    """
    issue_number, base_branch = _resolve_context(config, project_dir)
    start_time = time.time()
    run_number = next_run_number(project_dir, config)
    supervisor_sid: str | None = None
    # Carries a red mid-loop CI result into the next reviewer prompt; when it is
    # still set at the rounds cap the terminal reason is "ci", not "rounds".
    pending_ci_note: str | None = None
    # Most recently parsed verdict; carried into the failure comment when set.
    last_verdict: Verdict | None = None

    def body() -> int:
        nonlocal supervisor_sid, pending_ci_note, last_verdict

        for round_number in range(1, REVIEW_MAX_ROUNDS + 1):
            sha_before = get_latest_commit_sha(project_dir)

            # PR review feedback (implementation lane only): fetch fresh
            # branch status each round so resolved comments drop out, and thread
            # the feedback into both the reviewer prompt and the supervisor
            # report. The plan lane skips this — no GitHub call.
            status: BranchStatusReport | None = None
            pr_note: str | None = None
            if config.thread_pr_feedback:
                status = collect_branch_status(project_dir)
                if (
                    status.pr_feedback_undeterminable
                    or status.ci_status is CIStatus.UNKNOWN
                ):
                    # Distinguish a failed fetch from "no open feedback" in the
                    # logs. A total collection failure upstream yields an empty
                    # report with ci_status=UNKNOWN and the undeterminable flag
                    # left at its default False, so both are checked.
                    # Informational only: the round proceeds unchanged.
                    logger.warning(
                        "Round %d: PR review feedback undeterminable "
                        "(feedback or status collection failed); reviewing "
                        "without it",
                        round_number,
                    )
                pr_note = reviewer._pr_feedback_note(status.pr_feedback_text)

            # Reviewer: a fresh session per round.
            logger.info(
                "%s round %d/%d: reviewer starting",
                config.name,
                round_number,
                REVIEW_MAX_ROUNDS,
            )
            # Fresh reviewer with a bounded empty-report retry (an inner loop
            # that consumes no round): re-invoke on a whitespace-only report and
            # fail general on exhaustion. Exceptions are never retried here — the
            # broadened `except` categorizes them and fails immediately.
            reviewer_sid: str | None = None
            report = ""
            for _ in range(EMPTY_REPORT_RETRIES):
                try:
                    report_response = reviewer._run_reviewer(
                        config,
                        project_dir,
                        provider,
                        mcp_config,
                        settings_file,
                        execution_dir,
                        issue_number,
                        base_branch,
                        round_number=round_number,
                        max_rounds=REVIEW_MAX_ROUNDS,
                        session_id=None,
                        tasks=None,
                        ci_note=pending_ci_note,
                        pr_note=pr_note,
                    )
                except Exception as exc:  # pylint: disable=broad-exception-caught
                    return _fail(
                        config,
                        project_dir,
                        llm_failure_reason(exc) or "general",
                        update_issue_labels=update_issue_labels,
                        post_issue_comments=post_issue_comments,
                        round_number=round_number,
                        verdict=last_verdict,
                        elapsed=time.time() - start_time,
                    )
                reviewer_sid = report_response["session_id"]
                report = report_response["text"]
                if report.strip():
                    break
            else:
                return _fail(
                    config,
                    project_dir,
                    "general",
                    update_issue_labels=update_issue_labels,
                    post_issue_comments=post_issue_comments,
                    round_number=round_number,
                    verdict=last_verdict,
                    elapsed=time.time() - start_time,
                )

            # Supervisor: persistent session, verdict parsed with repair retries.
            # Append the raw PR feedback section (impl lane only, non-empty) so
            # the supervisor triages it alongside the reviewer's own findings.
            supervisor_report = report
            if status is not None and status.pr_feedback_text:
                supervisor_report = (
                    f"{report}\n\n## PR review feedback\n\n"
                    f"{reviewer._quote_pr_feedback(status.pr_feedback_text)}"
                )
            logger.info("Round %d: supervisor triage starting", round_number)
            try:
                verdict, supervisor_sid = reviewer._get_verdict(
                    config,
                    project_dir,
                    provider,
                    mcp_config,
                    settings_file,
                    execution_dir,
                    supervisor_sid,
                    supervisor_report,
                    round_number=round_number,
                    max_rounds=REVIEW_MAX_ROUNDS,
                )
            except Exception as exc:  # pylint: disable=broad-exception-caught
                return _fail(
                    config,
                    project_dir,
                    llm_failure_reason(exc) or "general",
                    update_issue_labels=update_issue_labels,
                    post_issue_comments=post_issue_comments,
                    round_number=round_number,
                    verdict=last_verdict,
                    elapsed=time.time() - start_time,
                )
            if verdict is None:
                return _fail(
                    config,
                    project_dir,
                    "general",
                    update_issue_labels=update_issue_labels,
                    post_issue_comments=post_issue_comments,
                    round_number=round_number,
                    verdict=last_verdict,
                    elapsed=time.time() - start_time,
                )
            last_verdict = verdict

            # Severity backstop (Step 5): at/after the lane's strict round a
            # `tasks` verdict with no critical/high finding is rewritten to
            # `dismiss` so the existing dismiss branch converges the loop
            # (deterministic guarantee for when the supervisor ignores the
            # advisory prompt rule).
            verdict = _apply_severity_floor(
                verdict, report, round_number, config, pending_ci_note
            )

            logger.info("Round %d: verdict '%s'", round_number, verdict.decision)

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
                    return _route_to_human(
                        config,
                        project_dir,
                        issue_number=issue_number,
                        update_issue_labels=update_issue_labels,
                        post_issue_comments=post_issue_comments,
                        comment_body=(
                            "Branch could not be rebased cleanly — handing off."
                        ),
                    )
                if reason:
                    # Terminal after-steps failure on the dismiss gate (e.g. a
                    # red final CI → `ci`, or `timeout` / `general` /
                    # `mcp_unavailable`): write + flush the round so the last
                    # executed round lands in the committed log before failing.
                    write_round_log(
                        project_dir,
                        config,
                        run_number,
                        round_number,
                        findings=report,
                        decisions=str(verdict),
                        changes=reason,
                        escalate_reason=reason,
                    )
                    _flush_round_log(project_dir)
                    return _fail(
                        config,
                        project_dir,
                        reason,
                        update_issue_labels=update_issue_labels,
                        post_issue_comments=post_issue_comments,
                        round_number=round_number,
                        verdict=last_verdict,
                        elapsed=time.time() - start_time,
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
                _flush_round_log(project_dir)
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
                return _route_to_human(
                    config,
                    project_dir,
                    issue_number=issue_number,
                    update_issue_labels=update_issue_labels,
                    post_issue_comments=post_issue_comments,
                    comment_body=(
                        f"{config.name} review escalated to a human: "
                        f"{verdict.escalate_reason}"
                    ),
                )

            # decision == "tasks": resume the reviewer to apply the fixes.
            logger.info(
                "Round %d: applying %d fix task(s)",
                round_number,
                len(verdict.tasks),
            )
            try:
                reviewer._run_reviewer(
                    config,
                    project_dir,
                    provider,
                    mcp_config,
                    settings_file,
                    execution_dir,
                    issue_number,
                    base_branch,
                    round_number=round_number,
                    max_rounds=REVIEW_MAX_ROUNDS,
                    session_id=reviewer_sid,
                    tasks=verdict.tasks,
                    ci_note=None,
                )
            except Exception as exc:  # pylint: disable=broad-exception-caught
                # A real report + `tasks` verdict already exist; the reviewer
                # crashed only while applying the fixes. Land the executed round
                # in the committed log before failing (mirrors the after-steps
                # `_fail` sub-paths below).
                reason = llm_failure_reason(exc) or "general"
                write_round_log(
                    project_dir,
                    config,
                    run_number,
                    round_number,
                    findings=report,
                    decisions=str(verdict),
                    changes=reason,
                    escalate_reason=reason,
                )
                _flush_round_log(project_dir)
                return _fail(
                    config,
                    project_dir,
                    reason,
                    update_issue_labels=update_issue_labels,
                    post_issue_comments=post_issue_comments,
                    round_number=round_number,
                    verdict=last_verdict,
                    elapsed=time.time() - start_time,
                )
            run_formatters(project_dir)
            if not commit_changes(
                project_dir,
                provider,
                mcp_config=mcp_config,
                execution_dir=str(execution_dir) if execution_dir else None,
                settings_file=settings_file,
            ):
                # Looping over an uncommitted round would hide the state from CI
                # and reviewers — fail the run instead (falls back to the
                # `general` failure label; the reason names the failed step).
                write_round_log(
                    project_dir,
                    config,
                    run_number,
                    round_number,
                    findings=report,
                    decisions=str(verdict),
                    changes="commit-failed",
                    escalate_reason="commit-failed",
                )
                # Committing is what is broken, so the flush is best-effort by
                # design; it still lands the round log when only the LLM commit
                # step failed.
                _flush_round_log(project_dir)
                return _fail(
                    config,
                    project_dir,
                    "commit-failed",
                    update_issue_labels=update_issue_labels,
                    post_issue_comments=post_issue_comments,
                    round_number=round_number,
                    verdict=last_verdict,
                    elapsed=time.time() - start_time,
                )
            if not push_changes(project_dir):
                write_round_log(
                    project_dir,
                    config,
                    run_number,
                    round_number,
                    findings=report,
                    decisions=str(verdict),
                    changes="push-failed",
                    escalate_reason="push-failed",
                )
                # Pushing is what is broken, so this flush is best-effort too.
                _flush_round_log(project_dir)
                return _fail(
                    config,
                    project_dir,
                    "push-failed",
                    update_issue_labels=update_issue_labels,
                    post_issue_comments=post_issue_comments,
                    round_number=round_number,
                    verdict=last_verdict,
                    elapsed=time.time() - start_time,
                )

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
                return _route_to_human(
                    config,
                    project_dir,
                    issue_number=issue_number,
                    update_issue_labels=update_issue_labels,
                    post_issue_comments=post_issue_comments,
                    comment_body=("Branch could not be rebased cleanly — handing off."),
                )
            if reason == "ci":
                # Mid-loop red CI is a finding, not a terminal failure: carry it
                # into the next fresh reviewer prompt and keep looping (the
                # supervisor triages it within the rounds cap).
                pending_ci_note = _CI_NOTE
            elif reason:
                # Terminal after-steps failure (`timeout` / `general` /
                # `mcp_unavailable`) after a committed fix: write + flush the
                # round so it lands in the committed log before failing.
                write_round_log(
                    project_dir,
                    config,
                    run_number,
                    round_number,
                    findings=report,
                    decisions=str(verdict),
                    changes=reason,
                    escalate_reason=reason,
                )
                _flush_round_log(project_dir)
                return _fail(
                    config,
                    project_dir,
                    reason,
                    update_issue_labels=update_issue_labels,
                    post_issue_comments=post_issue_comments,
                    round_number=round_number,
                    verdict=last_verdict,
                    elapsed=time.time() - start_time,
                )
            else:
                # After-steps clean (CI green / nothing to do): clear stale note.
                pending_ci_note = None

            # Backstop (layer C): a `tasks` round that changed nothing is a
            # silent no-op — log it, but let the round count toward the cap and
            # keep going (the next fresh reviewer re-surfaces the finding).
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

        # Rounds cap. The last `tasks` round already wrote its log at the end of
        # the loop body, so do NOT write again here — only commit+push it.
        if pending_ci_note:
            # A still-open CI finding keeps the cap terminal (17f-ci): flush the
            # last round's log (best-effort, mirroring the commit/push-failed
            # paths) then fail, so the round still lands in the committed log.
            _flush_round_log(project_dir)
            return _fail(
                config,
                project_dir,
                "ci",
                update_issue_labels=update_issue_labels,
                post_issue_comments=post_issue_comments,
                round_number=REVIEW_MAX_ROUNDS,
                verdict=last_verdict,
                elapsed=time.time() - start_time,
            )
        # A plain rounds cap now hands off to a human (escalate label, RC=0)
        # rather than failing: the loop is converging toward the same recovery
        # label the escalate verdict routes to. `_route_to_human` flushes the
        # last round's log internally.
        return _route_to_human(
            config,
            project_dir,
            issue_number=issue_number,
            update_issue_labels=update_issue_labels,
            post_issue_comments=post_issue_comments,
            comment_body=(
                f"Automated {config.name} review reached the round limit "
                f"({REVIEW_MAX_ROUNDS} rounds) without converging — handing off "
                f"for human review."
            ),
        )

    return run_guarded(
        body,
        project_dir=project_dir,
        from_label_id=config.busy_label_id,
        general_category=config.failure_labels["general"],
        comment_header=f"❌ {config.name} review terminated unexpectedly",
        update_issue_labels=update_issue_labels,
        post_issue_comments=post_issue_comments,
        issue_number=issue_number,
    )


def _apply_severity_floor(
    verdict: Verdict,
    report: str,
    round_number: int,
    config: ReviewConfig,
    pending_ci_note: str | None,
) -> Verdict:
    """Downgrade a low-severity ``tasks`` verdict to ``dismiss`` at the floor.

    The deterministic backstop for the advisory severity prompt rule: from
    ``config.strict_from_round`` onward, a ``tasks`` verdict whose reviewer
    report carries no ``critical``/``high`` finding is rewritten to
    ``Verdict("dismiss")`` so the loop stops burning rounds on nitpicks. Two
    guards keep it conservative: it **fails open** (leaves the verdict
    unchanged) on an unparseable report, and it is **skipped entirely** while a
    CI finding is pending — red CI is a must-fix, exempt from the floor.

    Args:
        verdict: The freshly parsed supervisor verdict.
        report: The fresh reviewer report (not the supervisor text) whose
            anchored finding lines carry the severities.
        round_number: The current 1-based round number.
        config: The review workflow config (supplies ``strict_from_round``).
        pending_ci_note: The carried CI-as-finding note, or ``None``. When set,
            the round is exempt and never downgraded.

    Returns:
        ``Verdict("dismiss")`` when the floor applies, else ``verdict``
        unchanged.
    """
    if verdict.decision != "tasks":
        return verdict
    if pending_ci_note is not None:
        return verdict
    if round_number < config.strict_from_round:
        return verdict
    top = max_severity(report)
    if top is None:
        return verdict
    if top in ("critical", "high"):
        return verdict
    logger.info(
        "Round %d: severity floor: downgrading tasks -> dismiss (max=%s)",
        round_number,
        top,
    )
    return Verdict(decision="dismiss")


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
        A failure reason (``"rebase"`` / ``"ci"`` / ``"timeout"`` /
        ``"mcp_unavailable"`` / ``"general"``) or ``None`` when the after-steps
        are clean or there is nothing to do. The broadened ``except`` scoped to
        the CI call categorizes a generic exception as ``"general"`` rather than
        letting it escape — but it does **not** wrap the rebase gate, so the
        ``"rebase"`` control-flow return is preserved.
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
    except Exception as exc:  # pylint: disable=broad-exception-caught
        return llm_failure_reason(exc) or "general"
    if ci_ok:
        return None
    if not is_dismiss:
        logger.info("CI is red mid-loop; carrying it forward as a review finding")
    return "ci"
