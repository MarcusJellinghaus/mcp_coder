"""Lane-context resolution and the implementation-lane after-steps gates.

These are the non-loop helpers the shared review engine (:mod:`core`) delegates
to around the round loop:

* :func:`_resolve_context` — resolve the issue number and (implementation lane
  only) the base branch the reviewer diffs against, *before* the loop.
* :func:`_after_steps` — run the rebase + CI gates *after* a dismiss (final
  gate) or a ``tasks`` application (mid-loop), for ``review-implementation``.
* :func:`round_applied` — whether a ``tasks`` round changed anything besides
  the review logs.

They live outside ``core`` to keep that module under its line budget.
"""

import logging
import re
import sys
from pathlib import Path

from mcp_coder.llm.error_summary import comment_safe
from mcp_coder.mcp_workspace_git import (
    extract_issue_number_from_branch,
    get_current_branch_name,
    get_latest_commit_sha,
    git_diff,
)
from mcp_coder.workflow_steps.ci import check_and_fix_ci
from mcp_coder.workflow_steps.commit import PushRejectedError
from mcp_coder.workflow_steps.rebase import RebaseOutcome
from mcp_coder.workflow_utils.base_branch import detect_base_branch
from mcp_coder.workflow_utils.failure_handling import (
    exception_summary,
    llm_failure_reason,
)
from mcp_coder.workflows.rebase_automated import rebase_with_llm_fallback

from .config import ReviewConfig

logger = logging.getLogger(__name__)

# Review logs change on every round (and a formatter may rewrite them), so a
# change to one never makes a round "applied".
_REVIEW_LOG = re.compile(r"^pr_info/[^/]*_review_log_[^/]*\.md$")


def round_applied(project_dir: Path, sha_before: str | None) -> bool:
    """Return whether files other than review logs changed since ``sha_before``.

    Compares ``sha_before`` with the working tree (committed and uncommitted
    tracked changes). Untracked files need no check: commit_changes has just
    staged everything. An unknown SHA or a git error counts as applied.

    Args:
        project_dir: Repository root.
        sha_before: HEAD SHA captured at the start of the round, or ``None``.

    Returns:
        True when the round applied a change, False for a no-op round.
    """
    if sha_before is None:
        return True
    try:
        out = git_diff(
            project_dir,
            ["--name-only", sha_before],
            compact=False,
            max_lines=sys.maxsize,
        )
    except Exception as exc:  # pylint: disable=broad-exception-caught
        logger.warning("Could not diff the review round: %s", exc)
        return True
    if out.strip() == "No changes found":
        return False
    return any(
        line.strip() and not _REVIEW_LOG.match(line.strip())
        for line in out.splitlines()
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


def _after_steps(
    config: ReviewConfig,
    project_dir: Path,
    provider: str,
    mcp_config: str | None,
    settings_file: str | None,
    is_dismiss: bool,
) -> tuple[str | None, RebaseOutcome | None, str | None]:
    """Run the after-steps (rebase + CI) for the implementation lane.

    ``review-plan`` has ``run_after_steps=False`` so this is a no-op there. For
    ``review-implementation`` it enforces two gates in order:

    1. **Rebase gate (mandated — never success on an unresolved rebase):** the
       branch is rebased onto its base branch via ``rebase_with_llm_fallback``:
       a git-only rebase first, then the LLM rebase on ``conflict`` /
       ``rebase_failed`` (with the least-privilege rebase settings, not
       ``settings_file``). If that cannot complete cleanly the return is
       ``"rebase"``, which the caller routes to a needs-human handoff
       (``07:code-review``) — never a success and never a failure label.
    2. **CI gate:** ``check_and_fix_ci`` runs its own retries (reusing
       ``implement``'s prompt headers, overriding ``session_dir_name`` and
       pinning the first poll to local HEAD, which the rebase step left on
       origin). A green result returns ``None``. A red result returns
       ``"ci"``: on the final dismiss gate (``is_dismiss``) the caller treats
       that as a terminal ``17f-ci`` failure; mid-loop the caller instead
       carries it forward as a finding (see :data:`core._CI_NOTE`).

    Args:
        config: The review workflow config.
        project_dir: Repository root.
        provider: LLM provider (LLM rebase and CI fixes).
        mcp_config: Optional MCP config path (LLM rebase and CI fixes).
        settings_file: Optional Claude settings file, for the CI fixes only.
        is_dismiss: Whether this runs on the final dismiss gate (vs mid-loop).
            Logged for diagnostics; the caller owns the terminal-vs-finding
            interpretation of a red CI result.

    Returns:
        ``(reason, outcome, detail)``. ``reason`` is a failure reason
        (``"rebase"`` / ``"ci"`` / ``"branch_moved"`` / ``"timeout"`` /
        ``"mcp_unavailable"`` / ``"auth"`` / ``"general"``) or ``None`` when
        the after-steps are clean or there is nothing to do. ``outcome`` is the
        :class:`RebaseOutcome` of the rebase gate, or ``None`` when the lane has
        no after-steps. ``detail`` is a
        comment-ready summary of the exception the CI call raised, ``None``
        otherwise; callers pass it only to the failure comment, never to the
        committed round log. The broadened ``except`` scoped to the CI call
        logs the traceback and categorizes the exception (``"general"`` when
        unmapped) rather than letting it escape — but it does **not** wrap
        the rebase gate, so the ``"rebase"`` control-flow return is preserved.
    """
    if not config.run_after_steps:
        return None, None, None

    # --- rebase gate (mandated: never success on an unresolved rebase) ---
    outcome = rebase_with_llm_fallback(project_dir, provider, mcp_config)
    if not outcome.ok:
        logger.warning(
            "Rebase gate did not pass (%s); routing to needs-human", outcome.reason
        )
        return "rebase", outcome, None

    # --- CI gate ---
    branch = get_current_branch_name(project_dir)
    if not branch:
        return None, outcome, None
    # After the rebase step, origin/<branch> holds local HEAD (pushed by it, or
    # already there) - including the round-log commit the loop lands at its
    # entry, which on a dismiss round is the only thing pushed. Correlate the
    # CI poll with that SHA: the newest run on the branch is still the
    # *previous* commit's for the first seconds after a push, and taking its
    # green would hand check_ci_proven_gate a branch whose newest run is the
    # queued one it reads as PENDING -> "ci_unknown".
    pushed_sha = get_latest_commit_sha(project_dir)
    try:
        ci_ok = check_and_fix_ci(
            project_dir=project_dir,
            branch=branch,
            provider=provider,
            mcp_config=mcp_config,
            settings_file=settings_file,
            session_dir_name=config.session_dir_name,
            expected_sha=pushed_sha,
        )
    except PushRejectedError as exc:
        logger.error("CI fix push was rejected; failing the review: %s", exc)
        return "branch_moved", outcome, comment_safe(str(exc))
    except Exception as exc:  # pylint: disable=broad-exception-caught
        logger.error("CI gate raised; failing the review", exc_info=True)
        reason = llm_failure_reason(exc) or "general"
        return reason, outcome, comment_safe(exception_summary(exc))
    if ci_ok:
        return None, outcome, None
    if not is_dismiss:
        logger.info("CI is red mid-loop; carrying it forward as a review finding")
    return "ci", outcome, None
