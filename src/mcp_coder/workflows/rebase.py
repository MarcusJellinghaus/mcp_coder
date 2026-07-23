"""Automated ``mcp-coder rebase`` workflow — deterministic shell (Issue #1066).

Python owns the deterministic shell around a single LLM session: pre-flight
guards, the outcome→exit-code decision, the force-push, and a ``finally`` safety
net. This module currently holds only the two pure decision functions; git
helpers, guards, and the orchestrator are added in later steps.

The exit-code contract cross-checks two signals and never trusts either alone:
the LLM's self-reported outcome marker and the actual git repository state (git
is authoritative, worst-case-wins).
"""

import logging
import re
import subprocess
from pathlib import Path

from mcp_coder.constants import PROMPTS_FILE_PATH
from mcp_coder.llm.env import prepare_llm_environment
from mcp_coder.llm.interface import prompt_llm
from mcp_coder.mcp_workspace_git import (
    fetch_remote,
    get_current_branch_name,
    get_latest_commit_sha,
    git_push,
    is_working_directory_clean,
    needs_rebase,
)
from mcp_coder.prompt_manager import get_prompt
from mcp_coder.utils.git_utils import get_branch_name_for_logging
from mcp_coder.workflow_utils.base_branch import detect_base_branch

logger = logging.getLogger(__name__)

_OUTCOME_RE = re.compile(r"^\s*REBASE_OUTCOME:\s*(.+?)\s*$", re.MULTILINE)
_REASON_RE = re.compile(r"^\s*REBASE_REASON:\s*(.+?)\s*$", re.MULTILINE)

_VALID_OUTCOMES = {"success", "aborted"}


def _parse_outcome_marker(response_text: str) -> tuple[str | None, str | None]:
    """Extract ``(outcome, reason)`` from the LLM response.

    Last match wins for both markers.

    Returns:
        A ``(outcome, reason)`` tuple. ``outcome`` is ``"success"`` |
        ``"aborted"`` | ``None`` (unparseable or an unrecognized value).
        ``reason`` is the ``REBASE_REASON`` text, or ``None`` when absent or
        ``"n/a"``.
    """
    outcome: str | None = None
    outcome_matches = _OUTCOME_RE.findall(response_text)
    if outcome_matches:
        candidate = outcome_matches[-1].strip().lower()
        if candidate in _VALID_OUTCOMES:
            outcome = candidate

    reason: str | None = None
    reason_matches = _REASON_RE.findall(response_text)
    if reason_matches:
        candidate_reason = reason_matches[-1].strip()
        if candidate_reason and candidate_reason.lower() != "n/a":
            reason = candidate_reason

    return outcome, reason


def _evaluate_pre_push(
    *,
    mid_rebase: bool,
    marker_outcome: str | None,
    rebase_success_shape: bool,
) -> str:
    """Return ``"push"`` or ``"abort"`` (worst-case-wins, git is authoritative)."""
    if mid_rebase:
        return "abort"  # unfinished / crashed session
    if marker_outcome == "aborted":
        return "abort"  # trust the self-report
    if not rebase_success_shape:
        return "abort"  # git can't corroborate success
    return "push"  # marker success/unparseable AND git confirms


def _run_git(project_dir: Path, *args: str) -> "subprocess.CompletedProcess[str]":
    """Run ``git <args>`` in ``project_dir`` (list form, no shell, ``check=False``).

    Never raises on a non-zero git exit; the caller decides what a failure means.

    Returns:
        The completed process so callers can inspect ``.returncode``,
        ``.stdout`` and ``.stderr``.
    """
    # Fixed argv, no shell, trusted ``git`` CLI — bandit B603/B607 are inherent to
    # any subprocess call and accepted repo-wide (see workflows/vscodeclaude,
    # utils/mcp_verification), so no suppression is added here for consistency.
    return subprocess.run(
        ["git", *args],
        cwd=str(project_dir),
        capture_output=True,
        text=True,
        check=False,
    )


def _is_rebase_in_progress(project_dir: Path) -> bool:
    """Return True if a rebase is mid-flight.

    Detected purely from the filesystem: git creates ``.git/rebase-merge`` (merge
    backend) or ``.git/rebase-apply`` (apply backend) while a rebase is unfinished.
    """
    git_dir = project_dir / ".git"
    return (git_dir / "rebase-merge").exists() or (git_dir / "rebase-apply").exists()


def _abort_rebase(project_dir: Path) -> None:
    """Best-effort ``git rebase --abort`` (never raises).

    Used by the ``finally`` safety net; if no rebase is in progress git simply
    exits non-zero, which ``_run_git`` swallows.
    """
    _run_git(project_dir, "rebase", "--abort")


def _reset_hard(project_dir: Path, sha: str) -> None:
    """Restore pre-rebase state with ``git reset --hard <sha>``."""
    _run_git(project_dir, "reset", "--hard", sha)


def _rebase_success_shape(project_dir: Path, pre_sha: str) -> bool:
    """Return True iff HEAD moved off ``pre_sha``, tree is clean, and not mid-rebase.

    This is the git-side corroboration of a claimed rebase success: no rebase may
    be in progress, the working tree must be clean, and HEAD must differ from the
    pre-rebase commit.
    """
    if _is_rebase_in_progress(project_dir):
        return False
    if not is_working_directory_clean(project_dir):
        return False
    return get_latest_commit_sha(project_dir) != pre_sha


_STANDARD_BASES = {"main", "master"}


def _preflight(project_dir: Path) -> str | None:
    """Return ``None`` if the repo is safe to rebase, else an error message.

    Checks, in order: a clean working tree, no rebase/merge in progress, HEAD not
    on ``main``/``master``, and an ``origin`` remote present. Each failing check
    short-circuits with a human-readable reason (the caller maps this to exit
    code ``2``).
    """
    if not is_working_directory_clean(project_dir):
        return "Working tree not clean"

    merge_head = project_dir / ".git" / "MERGE_HEAD"
    if _is_rebase_in_progress(project_dir) or merge_head.exists():
        return "Repository is mid-rebase/merge"

    if get_current_branch_name(project_dir) in _STANDARD_BASES:
        return "Refusing to rebase main/master"

    if _run_git(project_dir, "remote", "get-url", "origin").returncode != 0:
        return "Remote 'origin' not found"

    return None


def _resolve_base_branch(
    project_dir: Path, base_branch_arg: str | None
) -> tuple[str | None, str | None]:
    """Return ``(base_branch, error)`` — exactly one side is non-``None``.

    An explicit ``base_branch_arg`` wins verbatim (no detection). Otherwise
    ``detect_base_branch`` runs and only the standard ``main``/``master`` bases
    are accepted automatically; a non-standard or undetectable base returns an
    error asking for an explicit ``--base-branch``.
    """
    if base_branch_arg:
        return (base_branch_arg, None)

    detected = detect_base_branch(project_dir)
    if detected is None:
        return (None, "Could not detect base branch; pass --base-branch")
    if detected in _STANDARD_BASES:
        return (detected, None)
    return (None, f"Non-standard base '{detected}'; pass --base-branch to confirm")


def _check_pr_info_absent_on_base(project_dir: Path, base_branch: str) -> str | None:
    """Return ``None`` if ``pr_info/`` is absent on ``origin/<base>``, else an error.

    Uses ``git ls-tree origin/<base> pr_info``: any non-empty stdout means the
    path exists on the base branch, which is refused (the base must not already
    carry ``pr_info/``).
    """
    result = _run_git(project_dir, "ls-tree", f"origin/{base_branch}", "pr_info")
    if result.stdout.strip():
        return f"pr_info/ present on origin/{base_branch}"
    return None


# --- LLM session + orchestrator ------------------------------------------------

# Inactivity budget (max seconds with no stdout line from the LLM, NOT total
# runtime), matching the create_plan prompts and kept below the CI step cap.
_SESSION_TIMEOUT = 600

_REBASE_PROMPT_HEADER = "Automated Rebase"


def _run_rebase_session(
    project_dir: Path,
    base_branch: str,
    provider: str,
    mcp_config: str | None,
    settings_file: str | None,
    execution_dir: Path | None,
) -> str:
    """Run the single LLM rebase session.

    Loads the ``Automated Rebase`` prompt, appends the resolved base branch as
    context (so the LLM rebases onto ``origin/<base>``), and issues exactly one
    ``prompt_llm`` call with a ~600s inactivity budget. Any LLM error/timeout is
    left to propagate to the orchestrator, which maps it to a needs-human exit.

    Returns:
        The LLM response text (empty string when the response carries no text).
    """
    env_vars = prepare_llm_environment(project_dir)
    branch_name = get_branch_name_for_logging(project_dir)
    prompt_template = get_prompt(str(PROMPTS_FILE_PATH), _REBASE_PROMPT_HEADER)
    prompt = (
        f"{prompt_template}\n\n"
        "---\n"
        "## Rebase context\n"
        f"Rebase the current branch onto `origin/{base_branch}`.\n"
    )
    response = prompt_llm(
        prompt,
        provider=provider,
        session_id=None,
        timeout=_SESSION_TIMEOUT,
        env_vars=env_vars,
        execution_dir=str(execution_dir) if execution_dir else None,
        mcp_config=mcp_config,
        settings_file=settings_file,
        branch_name=branch_name,
    )
    return response.get("text", "") or ""


def run_rebase_workflow(
    project_dir: Path,
    provider: str,
    base_branch: str | None = None,
    mcp_config: str | None = None,
    settings_file: str | None = None,
    execution_dir: Path | None = None,
) -> int:
    """Orchestrate the automated rebase.

    Composes the deterministic shell: pre-flight guards -> base-branch guard ->
    ``pr_info/``-on-base guard -> no-op short-circuit -> single LLM session ->
    worst-case-wins decision -> Python-owned force-push (with restore on
    rejection) -> ``finally`` abort safety net.

    See the exit-code contract in ``summary.md``.

    Returns:
        ``0`` (success or no-op), ``1`` (aborted -> needs-human), or ``2``
        (error / push rejected).
    """
    err = _preflight(project_dir)
    if err:
        logger.error("Pre-flight failed: %s", err)
        return 2

    base, base_err = _resolve_base_branch(project_dir, base_branch)
    if base_err:
        logger.error("Base-branch guard failed: %s", base_err)
        return 2
    assert base is not None  # nosec B101 — guaranteed by _resolve_base_branch

    fetch_remote(project_dir, "origin")

    pr_info_err = _check_pr_info_absent_on_base(project_dir, base)
    if pr_info_err:
        logger.error("pr_info/ guard failed: %s", pr_info_err)
        return 2

    needed, reason = needs_rebase(project_dir, base)
    if not needed:
        logger.info("Already current with origin/%s (%s); nothing to do", base, reason)
        return 0

    pre_sha = get_latest_commit_sha(project_dir)
    if pre_sha is None:
        logger.error("Could not resolve HEAD commit before rebase")
        return 2

    try:
        text = _run_rebase_session(
            project_dir, base, provider, mcp_config, settings_file, execution_dir
        )
        outcome, marker_reason = _parse_outcome_marker(text)
        decision = _evaluate_pre_push(
            mid_rebase=_is_rebase_in_progress(project_dir),
            marker_outcome=outcome,
            rebase_success_shape=_rebase_success_shape(project_dir, pre_sha),
        )
        if decision == "abort":
            logger.error("Rebase aborted (needs human): %s", marker_reason or reason)
            return 1

        result = git_push(project_dir, force_with_lease=True)
        if result["success"]:
            logger.info("Rebased and force-pushed onto origin/%s", base)
            return 0

        logger.error("Force-push rejected/failed: %s", result.get("error"))
        _reset_hard(project_dir, pre_sha)  # never leave unpushed rebased commits
        return 2
    except Exception as exc:  # pylint: disable=broad-exception-caught
        # LLMTimeoutError is a subclass, so one branch covers timeout + errors.
        logger.error("Rebase session failed: %s", exc)
        return 1  # needs-human; the finally net makes this retry-safe
    finally:
        if _is_rebase_in_progress(project_dir):
            _abort_rebase(project_dir)
