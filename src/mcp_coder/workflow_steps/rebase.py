"""Rebase-and-push workflow step.

Detects the parent/base branch and attempts to rebase the current feature
branch onto it before pushing, without ever blocking the workflow. Moved here
from ``implement/rebase.py`` so multiple workflows can share it.
"""

import logging
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from mcp_coder.mcp_workspace_git import (
    get_full_status,
    get_remote_branch_commit_sha,
    rebase_onto_branch,
)
from mcp_coder.mcp_workspace_github import PullRequestManager
from mcp_coder.utils.subprocess_runner import execute_command
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
]

# First line of `git merge-tree --write-tree` output: a SHA-1 or SHA-256 tree OID.
_TREE_OID = re.compile(r"[0-9a-f]{40}|[0-9a-f]{64}")

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
    """

    reason: RebaseReason
    base_branch: str | None = None
    base_sha: str | None = None
    files: tuple[str, ...] = ()

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
    """Classify a failed rebase with a read-only ``git merge-tree`` probe.

    Args:
        project_dir: Path to the project directory
        base: Base branch name

    Returns:
        ``("conflict", files)`` when merge-tree reports conflicts, else
        ``("rebase_failed", ())`` - including exit 0, timeouts, missing git
        and git older than 2.38.
    """
    try:
        result = execute_command(
            [
                "git",
                "merge-tree",
                "--write-tree",
                "--name-only",
                "--no-messages",
                f"origin/{base}",
                "HEAD",
            ],
            cwd=str(project_dir),
        )
    except Exception:  # pylint: disable=broad-exception-caught
        return "rebase_failed", ()
    lines = [ln.strip() for ln in result.stdout.splitlines() if ln.strip()]
    if (
        result.return_code == 1
        and not result.execution_error
        and lines
        and _TREE_OID.fullmatch(lines[0])
    ):
        return "conflict", tuple(lines[1:])
    return "rebase_failed", ()


def _attempt_rebase_and_push(project_dir: Path) -> RebaseOutcome:
    """Attempt to rebase onto parent branch and push. Never fails workflow.

    Args:
        project_dir: Path to the project directory

    Returns:
        RebaseOutcome with reason ``"ok"`` if rebase and push succeeded.
        Otherwise the reason is ``"dirty_tree"`` (staged or modified tracked
        files; untracked files alone do not count), ``"no_base"`` (no target
        detected), ``"base_missing"`` (base not on origin), ``"conflict"`` /
        ``"rebase_failed"`` (rebase did not complete) or ``"push_failed"``.
    """
    # Checked before target detection: detect_base_branch fetches from the
    # remote, and there is no point paying for it when the rebase cannot start.
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

    logger.info("Rebasing onto origin/%s...", target)
    rebased = rebase_onto_branch(project_dir, target)
    sha = _base_sha(project_dir, target)
    if not rebased:
        reason, files = _classify_failed_rebase(project_dir, target)
        return RebaseOutcome(reason, target, sha, files)

    # Push rebased branch with force_with_lease
    if not push_changes(project_dir, force_with_lease=True):
        logger.warning(
            "Rebase succeeded but push failed - "
            "manual push with --force-with-lease may be required"
        )
        return RebaseOutcome("push_failed", target, sha)
    return RebaseOutcome("ok", target, sha)


def _reset_hard(project_dir: Path, sha: str) -> bool:
    """Reset the current branch to ``sha`` (``git reset --hard``). Never raises.

    Used to undo a rebase whose push failed, so local HEAD matches the
    remote again.

    Args:
        project_dir: Path to the project directory
        sha: Commit to reset to

    Returns:
        True if the reset succeeded.
    """
    try:
        result = execute_command(["git", "reset", "--hard", sha], cwd=str(project_dir))
    except Exception:  # pylint: disable=broad-exception-caught
        logger.warning("git reset --hard %s failed", sha, exc_info=True)
        return False
    if result.return_code != 0:
        logger.warning("git reset --hard %s failed: %s", sha, result.stderr.strip())
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
