"""Rebase-and-push workflow step.

Detects the parent/base branch and attempts to rebase the current feature
branch onto it before pushing, without ever blocking the workflow. Moved here
from ``implement/rebase.py`` so multiple workflows can share it.
"""

import logging
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from mcp_coder.mcp_workspace_git import (
    commit_paths,
    get_current_branch_name,
    get_full_status,
    get_latest_commit_sha,
    get_remote_branch_commit_sha,
    git_diff,
    git_merge_base,
    has_staged_changes,
    is_staged_diff_cr_only,
    probe_rebase_conflicts,
    rebase_onto_branch,
    renormalize_paths,
    reset_hard,
    unstage_paths,
)
from mcp_coder.mcp_workspace_github import PullRequestManager
from mcp_coder.workflow_steps.commit import push_changes
from mcp_coder.workflow_utils.base_branch import (
    check_base_branch_on_origin,
    detect_base_branch,
)
from mcp_coder.workflow_utils.failure_handling import SHORT_SHA_LENGTH

logger = logging.getLogger(__name__)

RebaseReason = Literal[
    "ok",
    "dirty_tree",
    "no_base",
    "base_missing",
    "conflict",
    "rebase_failed",
    "push_failed",
    "branch_moved",
]

BranchCheck = Literal["passed", "moved", "skipped", "error"]

BRANCH_MOVED_REASON = "`origin/<branch>` has commits this checkout does not have"
BRANCH_MOVED_NEXT_STEP = (
    "Check `origin/<branch>` for new commits, update or discard the local "
    "checkout, then re-run"
)
_COULD_NOT_VERIFY = "Could not verify `origin/<branch>`; not pushing"

_POLL_ATTEMPTS = 6
_POLL_INTERVAL_SECONDS = 5


@dataclass(frozen=True)
class RebaseOutcome:
    """Result of a rebase-and-push attempt.

    Always truthy - callers must check ``.ok``, never ``if outcome:``.

    Attributes:
        reason: Why the attempt ended (``"ok"`` on success).
        base_branch: Branch rebased onto, when one was detected.
        base_sha: Short SHA of ``origin/<base_branch>`` after the attempt.
        files: Uncommitted files (``dirty_tree``) or likely conflicting
            files (``conflict``); empty otherwise.
        llm_detail: What the LLM rebase fallback did, or why it was skipped;
            None when it did not run.
    """

    reason: RebaseReason
    base_branch: str | None = None
    base_sha: str | None = None
    files: tuple[str, ...] = ()
    llm_detail: str | None = None

    @property
    def ok(self) -> bool:
        """Return True only when the rebase and push both succeeded."""
        return self.reason == "ok"


def _get_rebase_target_branch(project_dir: Path) -> str | None:
    """Determine the target branch for rebasing the current feature branch.

    Uses shared detect_base_branch() function for detection.

    Args:
        project_dir: Path to the project directory

    Returns:
        Branch name to rebase onto, or None if detection fails
    """
    return detect_base_branch(project_dir)  # Now returns None directly on failure


def _uncommitted_tracked_files(project_dir: Path) -> list[str]:
    """List uncommitted changes that would make git refuse a rebase.

    Args:
        project_dir: Path to the project directory

    Returns:
        Sorted tracked entries that are staged or modified (deletions
        included); empty when the tree is clean.
    """
    # get_full_status never raises: it returns empty lists for a non-git-repo
    # and swallows unexpected errors into the same empty result.
    status = get_full_status(project_dir)
    # Untracked files are NOT blocking - git rebase tolerates them.
    # DEFAULT_IGNORED_BUILD_ARTIFACTS is NOT filtered - git refuses on a
    # modified uv.lock like any other tracked modification.
    return sorted(set(status["staged"] + status["modified"]))


def _staged_diff_adds_cr(project_dir: Path) -> bool:
    """Return True if the staged diff adds a line ending in CR.

    ``is_staged_diff_cr_only`` passes in both directions; this tells CRLF -> LF
    (a normalization) from LF -> CRLF (no ``text`` attribute, so the CRLF working
    copy would be committed as is). The whole index is inspected: everything
    staged is among the dirty files handled together.

    Args:
        project_dir: Path to the project directory

    Returns:
        True if any added line of the staged diff ends in CR.
    """
    diff = git_diff(
        project_dir, args=["--cached"], compact=False, max_lines=sys.maxsize
    )
    return any(
        line.startswith("+") and line.endswith("\r") for line in diff.split("\n")
    )


def _clear_line_ending_dirt(project_dir: Path, files: list[str]) -> bool:
    """Renormalize ``files``; commit if anything is staged. All-or-nothing.

    Args:
        project_dir: Path to the project directory
        files: Dirty tracked files, relative to ``project_dir``

    Returns:
        True when the tree no longer blocks the rebase; False (paths unstaged
        again) when any file has a real change, is deleted, would gain CRs in
        the commit, or git fails.
    """
    # git cannot stage a deletion through --renormalize, and a deletion is a
    # real change anyway.
    if any(not (project_dir / f).exists() for f in files):
        return False

    paths = [project_dir / f for f in files]
    try:
        renormalized = renormalize_paths(paths, project_dir)["success"]
        if (
            renormalized
            and is_staged_diff_cr_only(paths, project_dir)
            and not _staged_diff_adds_cr(project_dir)
        ):
            if not has_staged_changes(project_dir):
                return True  # Stat-only dirt: nothing to commit.
            commit = commit_paths("chore: renormalize line endings", paths, project_dir)
            if commit["success"]:
                return True
            logger.warning("Renormalize commit failed: %s", commit["error"])
    except Exception:  # pylint: disable=broad-exception-caught
        # has_staged_changes raises on a git failure; this must not fail the workflow.
        logger.warning("Could not clear line-ending dirt", exc_info=True)
    unstage_paths(paths, project_dir)
    return False


def _base_sha(project_dir: Path, base: str) -> str | None:
    """Return the short SHA of ``origin/<base>``, or None if it cannot be read.

    Args:
        project_dir: Path to the project directory
        base: Base branch name

    Returns:
        SHA truncated to ``SHORT_SHA_LENGTH``, or None on any failure.
    """
    sha = get_remote_branch_commit_sha(project_dir, base)
    return sha[:SHORT_SHA_LENGTH] if sha else None


def _classify_failed_rebase(
    project_dir: Path, base: str
) -> tuple[RebaseReason, tuple[str, ...]]:
    """Classify a failed rebase with a read-only rebase conflict probe.

    Args:
        project_dir: Path to the project directory
        base: Base branch name

    Returns:
        ``("conflict", files)`` when the probe's ``status`` is ``"conflict"``,
        else ``("rebase_failed", ())`` - for ``"clean"``, ``"unsupported"``
        (git older than 2.38), ``"error"`` and an exception from the probe.
    """
    try:
        probe = probe_rebase_conflicts(project_dir, f"origin/{base}")
    except Exception:  # pylint: disable=broad-exception-caught
        return "rebase_failed", ()
    if probe["status"] == "conflict":
        return "conflict", tuple(probe["files"])
    return "rebase_failed", ()


def _check_branch_not_moved(project_dir: Path, pre_sha: str) -> BranchCheck:
    """Check that ``origin/<branch>`` holds nothing this checkout lacks. Never raises.

    The fetch inside a rebase refreshes ``origin/<branch>``, which lets a later
    ``--force-with-lease`` overwrite someone else's commits. This needs no network
    call. It compares the ref's SHA, because a tag named ``origin/<branch>`` would
    make a comparison by name pass wrongly. All logging happens here, so callers
    only branch on the status.

    Args:
        project_dir: Path to the project directory
        pre_sha: HEAD before the rebase; a normal rebase rewrites the later HEAD

    Returns:
        ``"passed"`` when the remote SHA is an ancestor of ``pre_sha``, ``"moved"``
        when it is not, ``"skipped"`` when the remote ref is absent (the lease
        remains the backstop) and ``"error"`` when the check could not run.
    """
    try:
        branch = get_current_branch_name(project_dir)
        if branch is None:
            logger.warning(_COULD_NOT_VERIFY)
            return "error"
        remote_sha = get_remote_branch_commit_sha(project_dir, branch)
        if remote_sha is None:
            logger.debug("No origin/%s to check; relying on the lease", branch)
            return "skipped"
        result = git_merge_base(project_dir, ["--is-ancestor", remote_sha, pre_sha])
    except Exception:  # pylint: disable=broad-exception-caught
        logger.warning(_COULD_NOT_VERIFY, exc_info=True)
        return "error"
    if result == "true":
        return "passed"
    if result == "false":
        logger.warning("%s. %s", BRANCH_MOVED_REASON, BRANCH_MOVED_NEXT_STEP)
        return "moved"
    logger.warning(_COULD_NOT_VERIFY)
    return "error"


def _attempt_rebase_and_push(project_dir: Path) -> RebaseOutcome:
    """Attempt to rebase onto parent branch and push. Never fails workflow.

    Line-ending-only dirt does not block the rebase: it is renormalized and
    committed first, and the push carries that commit to origin.

    Args:
        project_dir: Path to the project directory

    Returns:
        RebaseOutcome with reason ``"ok"`` if rebase and push succeeded.
        Otherwise the reason is ``"dirty_tree"`` (staged or modified tracked
        files with more than line-ending changes; untracked files alone do
        not count), ``"no_base"`` (no target
        detected), ``"base_missing"`` (base not on origin), ``"conflict"`` /
        ``"rebase_failed"`` (rebase did not complete), ``"branch_moved"``
        (``origin/<branch>`` has commits this checkout does not have; rebase
        undone, nothing pushed) or ``"push_failed"`` (the push failed, or the
        branch check could not run; in that case rebase undone, nothing pushed).
    """
    # Checked before target detection: detect_base_branch fetches from the
    # remote, and there is no point paying for it when the rebase cannot start.
    dirty = _uncommitted_tracked_files(project_dir)
    if dirty and _clear_line_ending_dirt(project_dir, dirty):
        dirty = _uncommitted_tracked_files(project_dir)
    if dirty:
        logger.warning(
            "Skipping rebase: the working tree has staged or modified tracked "
            "files, which git refuses to rebase over - commit or discard them "
            "and re-run: %s",
            ", ".join(dirty),
        )
        return RebaseOutcome("dirty_tree", files=tuple(dirty))

    target = _get_rebase_target_branch(project_dir)
    if not target:
        logger.debug("Could not detect parent branch for rebase")
        return RebaseOutcome("no_base")

    missing_err = check_base_branch_on_origin(project_dir, target)
    if missing_err:
        logger.warning("Skipping rebase: %s", missing_err)
        return RebaseOutcome("base_missing", target)

    pre_sha = get_latest_commit_sha(project_dir)
    if pre_sha is None:
        logger.warning("Skipping rebase: could not read HEAD")
        return RebaseOutcome("rebase_failed", target, _base_sha(project_dir, target))

    logger.info("Rebasing onto origin/%s...", target)
    rebased = rebase_onto_branch(project_dir, target)
    sha = _base_sha(project_dir, target)
    if not rebased:
        reason, files = _classify_failed_rebase(project_dir, target)
        return RebaseOutcome(reason, target, sha, files)

    # Checked after the rebase, whose own fetch could outdate an earlier check.
    status = _check_branch_not_moved(project_dir, pre_sha)
    if status in ("moved", "error"):
        # Reset here: implement, fix-conflict and review do not on a failed outcome.
        _reset_hard(project_dir, pre_sha)
        return RebaseOutcome(
            "branch_moved" if status == "moved" else "push_failed", target, sha
        )

    # Push rebased branch with force_with_lease
    if not push_changes(project_dir, force_with_lease=True):
        logger.warning(
            "Rebase succeeded but push failed - check origin/<branch> before "
            "re-running; do not fetch and push with --force-with-lease"
        )
        return RebaseOutcome("push_failed", target, sha)
    return RebaseOutcome("ok", target, sha)


def _reset_hard(project_dir: Path, sha: str) -> bool:
    """Reset the current branch to ``sha`` (``git reset --hard``). Never raises.

    Used to undo a rebase whose push failed or that the branch check stopped,
    so local HEAD matches its state before the rebase again.

    Args:
        project_dir: Path to the project directory
        sha: Commit to reset to

    Returns:
        True if the reset succeeded.
    """
    try:
        result = reset_hard(project_dir, sha)
    except Exception:  # pylint: disable=broad-exception-caught
        logger.error("git reset --hard %s failed", sha, exc_info=True)
        return False
    if not result["success"]:
        logger.error(
            "git reset --hard %s failed: %s", sha, result["stderr"] or result["error"]
        )
        return False
    return True


def _poll_mergeable_state(project_dir: Path, branch_name: str) -> str | None:
    """Poll ``find_pull_request_by_head`` for a settled mergeable_state.

    Returns:
        The last observed mergeable_state (may be "unknown" or None if the
        PR disappeared) after the loop ends.
    """
    state: str | None = None
    for attempt in range(_POLL_ATTEMPTS):
        prs = PullRequestManager(project_dir).find_pull_request_by_head(branch_name)
        state = prs[0]["mergeable_state"] if prs else None
        # "unknown" is GitHub's not-yet-computed placeholder - keep polling.
        if state not in (None, "unknown"):
            return state
        if attempt < _POLL_ATTEMPTS - 1:
            time.sleep(_POLL_INTERVAL_SECONDS)
    return state
