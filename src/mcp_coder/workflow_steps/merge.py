"""Auto-merge workflow step.

Squash-merges a branch's PR once CI has really passed on its HEAD commit,
with one mechanical rebase + retry when GitHub reports the PR ``dirty`` or
``behind``. LLM-free; shared by create-pr, fix-ci and fix-conflict.
"""

import logging
from dataclasses import dataclass
from pathlib import Path

from mcp_coder.mcp_workspace_git import (
    extract_issue_number_from_branch,
    get_latest_commit_sha,
)
from mcp_coder.mcp_workspace_github import (
    CIResultsManager,
    CIStatusData,
    GithubException,
    IssueBranchManager,
    MergeResult,
    PullRequestManager,
)
from mcp_coder.utils.log_utils import OUTPUT
from mcp_coder.workflow_steps.ci import _poll_for_ci_completion
from mcp_coder.workflow_steps.rebase import (
    RebaseOutcome,
    _attempt_rebase_and_push,
    _poll_mergeable_state,
    _reset_hard,
)
from mcp_coder.workflow_utils.branch_linkage import is_branch_linked_to_issue
from mcp_coder.workflow_utils.failure_handling import CommentField, exception_summary
from mcp_coder.workflow_utils.rate_limit import as_rate_limit, log_rate_limit_stop

logger = logging.getLogger(__name__)

__all__ = [
    "MergeOutcome",
    "is_real_green",
    "resolve_merge_issue_number",
    "run_auto_merge",
]


@dataclass(frozen=True)
class MergeOutcome:
    """Final label of an auto-merge attempt plus comment fields for 74 / 99f.

    Attributes:
        label_id: Internal id of the label the issue should end on.
        comment_fields: Fields for the failure comment; non-empty only for
            ``merge_failed`` and ``pr_merge_conflict``.
    """

    label_id: str
    comment_fields: tuple[CommentField, ...] = ()


def is_real_green(
    ci_status: CIStatusData | None, ci_ok: bool, expected_sha: str | None
) -> bool:
    """Return True only for a passed CI run on exactly ``expected_sha``.

    Args:
        ci_status: CI status from ``_poll_for_ci_completion`` (None = no CI found).
        ci_ok: Success flag from ``_poll_for_ci_completion``.
        expected_sha: Commit that must have been checked.

    Returns:
        True when CI passed and the run's ``commit_sha`` equals ``expected_sha``.
    """
    return (
        ci_status is not None
        and ci_ok
        and expected_sha is not None
        and ci_status.get("run", {}).get("commit_sha") == expected_sha
    )


def resolve_merge_issue_number(project_dir: Path, branch: str) -> int | None:
    """Resolve the issue whose label an auto-merge should write. Never raises.

    Args:
        project_dir: Path to the project directory.
        branch: Current branch name.

    Returns:
        The branch-name issue number when the branch is linked to it or the
        linkage lookup failed; None when the branch carries no number or is
        not linked (label write skipped).
    """
    number = extract_issue_number_from_branch(branch)
    if number is None:
        logger.warning(
            "No issue number in branch %s - auto-merge label write skipped", branch
        )
        return None
    try:
        linked = is_branch_linked_to_issue(
            IssueBranchManager(project_dir=project_dir), number, branch
        )
    except Exception:  # pylint: disable=broad-exception-caught
        linked = None
    if linked is False:
        logger.warning(
            "Branch %s is not linked to issue #%d - auto-merge label write skipped",
            branch,
            number,
        )
        return None
    return number


def _pr_head_sha(project_dir: Path, branch: str) -> str | None:
    """Re-read the branch's PR and return its head SHA.

    Args:
        project_dir: Path to the project directory.
        branch: Head branch of the PR.

    Returns:
        The single open PR's ``head_sha``, or None when not exactly one PR.
    """
    prs = PullRequestManager(project_dir).find_pull_request_by_head(branch)
    return prs[0]["head_sha"] if len(prs) == 1 else None


def _failed(
    result: MergeResult,
    state: str | None = None,
    rebase: RebaseOutcome | None = None,
) -> MergeOutcome:
    """Build a ``merge_failed`` outcome from the merge (and rebase) results.

    Args:
        result: The last merge attempt.
        state: The PR's mergeable_state, when it was polled.
        rebase: The failed rebase, if one was attempted.

    Returns:
        MergeOutcome with label ``merge_failed`` and its comment fields.
    """
    status = result["status"]
    fields: list[CommentField] = [
        ("Stage", "Auto-merge"),
        ("Error", result["message"]),
        ("Merge outcome", result["outcome"]),
        ("HTTP status", str(status) if status is not None else None),
        ("Mergeable state", state),
    ]
    if rebase is not None:
        fields += [("Reason", rebase.reason), ("Base", rebase.base_branch)]
    logger.warning(
        "Auto-merge failed: %s (outcome=%s, status=%s, mergeable_state=%s)",
        result["message"],
        result["outcome"],
        status,
        state,
    )
    return MergeOutcome("merge_failed", tuple(fields))


def _conflict_fields(rebase: RebaseOutcome) -> tuple[CommentField, ...]:
    """Build the ``pr_merge_conflict`` comment fields for a conflicting rebase.

    Args:
        rebase: The rebase outcome with reason ``conflict``.

    Returns:
        Comment fields naming the base and the likely conflicting files.
    """
    return (
        ("Stage", "Auto-merge rebase"),
        ("Reason", "conflict"),
        ("Base", rebase.base_branch),
        ("Likely conflicting files", ", ".join(rebase.files) or None),
    )


def run_auto_merge(  # pylint: disable=too-many-return-statements
    project_dir: Path, branch: str, *, verified_sha: str | None = None
) -> MergeOutcome:
    """Squash-merge the branch's PR once CI really passed on its HEAD.

    A GitHub rate limit or a 401/403 ``GithubException`` is mapped to an
    outcome; any other exception propagates to the caller.

    Args:
        project_dir: Path to the project directory.
        branch: Head branch of the PR.
        verified_sha: Commit the caller already saw really green; skips the
            first CI poll.

    Returns:
        MergeOutcome with label ``merged``, ``pr_created``, ``failing_ci``,
        ``pr_merge_conflict`` or ``merge_failed``.
    """
    try:
        prs = PullRequestManager(project_dir).find_pull_request_by_head(branch)
        if len(prs) != 1 or not prs[0]["head_sha"]:
            logger.warning(
                "Auto-merge skipped: expected one open PR with a head SHA for %s, "
                "found %d",
                branch,
                len(prs),
            )
            return MergeOutcome("pr_created")
        pr = prs[0]
        sha = verified_sha
        for attempt in (1, 2):
            if sha is None:
                sha = get_latest_commit_sha(project_dir)
                status, ok = _poll_for_ci_completion(
                    CIResultsManager(project_dir), branch, expected_sha=sha
                )
                if status is not None and not ok:
                    logger.log(OUTPUT, "Auto-merge: CI failed on %s", sha)
                    return MergeOutcome("failing_ci")
                if not is_real_green(status, ok, sha):
                    logger.warning(
                        "Auto-merge skipped: no passed CI run for %s (soft pass)", sha
                    )
                    return MergeOutcome("pr_created")
            if _pr_head_sha(project_dir, branch) != sha:
                logger.warning(
                    "Auto-merge skipped: PR head no longer matches verified %s", sha
                )
                return MergeOutcome("pr_created")

            logger.log(
                OUTPUT, "Auto-merge: squash-merging PR #%d at %s", pr["number"], sha
            )
            result = PullRequestManager(project_dir).merge_pull_request(
                pr["number"],
                "squash",
                sha=sha,
                commit_title=f"{pr['title']} (#{pr['number']})",
            )
            if result["outcome"] == "merged":
                logger.log(OUTPUT, "Auto-merge: PR #%d merged", pr["number"])
                return MergeOutcome("merged")
            if result["outcome"] == "error" and result["status"] == 429:
                logger.warning("Auto-merge stopped: GitHub returned 429")
                return MergeOutcome("pr_created")
            if result["outcome"] == "error" or result["status"] == 409 or attempt == 2:
                return _failed(result)

            state = _poll_mergeable_state(project_dir, branch)
            if state not in ("dirty", "behind"):
                return _failed(result, state)

            logger.log(OUTPUT, "Auto-merge: PR is %s, rebasing once", state)
            before = get_latest_commit_sha(project_dir)
            rebase = _attempt_rebase_and_push(project_dir)
            if rebase.reason == "conflict":
                logger.log(OUTPUT, "Auto-merge: rebase hit a conflict")
                return MergeOutcome("pr_merge_conflict", _conflict_fields(rebase))
            if not rebase.ok:
                if rebase.reason == "push_failed" and before:
                    _reset_hard(project_dir, before)
                return _failed(result, state, rebase)
            sha = None  # re-poll CI on the new HEAD
    except Exception as exc:
        rate_limit = as_rate_limit(exc)
        if rate_limit is not None:
            log_rate_limit_stop(rate_limit)
            return MergeOutcome("pr_created")
        status_code = exc.status if isinstance(exc, GithubException) else None
        if status_code in (401, 403):
            logger.warning("Auto-merge failed: %s", exception_summary(exc))
            return MergeOutcome(
                "merge_failed",
                (("Stage", "Auto-merge"), ("Error", exception_summary(exc))),
            )
        raise
    # Unreachable: attempt 2 always returns; kept for type checkers.
    return MergeOutcome("pr_created")  # pragma: no cover
