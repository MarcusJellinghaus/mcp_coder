"""Read-only data layer for branch + linked-issue info.

Pure functions exposing a snapshot of the current branch's GitHub state for
UI/observability consumers (iCoder, vscodeclaude/web, future CLI commands).
GitHub-side errors are caught internally and result in partial data;
hard failures (e.g. ``get_pr_for_issue``) propagate to the caller.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

from mcp_coder.mcp_workspace_git import (
    extract_issue_number_from_branch,
    get_current_branch_name,
    get_repository_identifier,
    is_git_repository,
    is_working_directory_clean,
)
from mcp_coder.mcp_workspace_github import (
    IssueBranchManager,
    IssueManager,
    PullRequestManager,
    get_all_cached_issues,
    get_cache_file_path,
    load_cache_file,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class BranchInfo:
    """Snapshot of the local branch and its linked GitHub issue."""

    is_git_repo: bool
    branch_name: Optional[str]
    is_dirty: bool
    issue_number: Optional[int]
    issue_title: Optional[str]
    issue_status_label: Optional[str]
    cache_last_checked: Optional[datetime]


_EMPTY = BranchInfo(
    is_git_repo=False,
    branch_name=None,
    is_dirty=False,
    issue_number=None,
    issue_title=None,
    issue_status_label=None,
    cache_last_checked=None,
)


def _pick_status_label(labels: list[str]) -> Optional[str]:
    for name in labels:
        if name.startswith("status-"):
            return name
    return None


def _parse_iso(value: object) -> Optional[datetime]:
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def get_branch_info(project_dir: Path) -> BranchInfo:
    """Build a ``BranchInfo`` snapshot for ``project_dir``.

    GitHub-side errors are swallowed: branch/dirty fields stay populated and
    the issue fields fall back to ``None`` so the UI can still render.

    Returns:
        A ``BranchInfo`` snapshot. Outside a git repo, returns ``_EMPTY``.
    """
    if not is_git_repository(project_dir):
        return _EMPTY

    branch = get_current_branch_name(project_dir)
    is_dirty = not is_working_directory_clean(project_dir)
    issue_number = (
        extract_issue_number_from_branch(branch) if branch is not None else None
    )

    issue_title: Optional[str] = None
    status_label: Optional[str] = None
    last_checked: Optional[datetime] = None

    if issue_number is not None:
        try:
            repo_id = get_repository_identifier(project_dir)
            if repo_id is not None:
                cache_path = get_cache_file_path(repo_id)
                cache_data = load_cache_file(cache_path)
                last_checked = _parse_iso(cache_data.get("last_checked"))

                issue_mgr = IssueManager(project_dir=project_dir)
                for issue in get_all_cached_issues(repo_id, issue_manager=issue_mgr):
                    if issue.get("number") == issue_number:
                        issue_title = issue.get("title")
                        status_label = _pick_status_label(list(issue.get("labels", [])))
                        break
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logger.debug("Issue lookup failed: %s", exc)
            issue_title = None
            status_label = None
            last_checked = None

    return BranchInfo(
        is_git_repo=True,
        branch_name=branch,
        is_dirty=is_dirty,
        issue_number=issue_number,
        issue_title=issue_title,
        issue_status_label=status_label,
        cache_last_checked=last_checked,
    )


def get_branch_only(project_dir: Path) -> BranchInfo:
    """Return a cheap branch-only ``BranchInfo`` snapshot.

    Populates only the fields obtainable without GitHub or cache I/O:
    ``is_git_repo``, ``branch_name``, ``is_dirty``, and ``issue_number``
    (parsed from the branch name). The remaining three fields
    (``issue_title``, ``issue_status_label``, ``cache_last_checked``)
    are always ``None``.
    """
    if not is_git_repository(project_dir):
        return _EMPTY

    branch = get_current_branch_name(project_dir)
    is_dirty = not is_working_directory_clean(project_dir)
    issue_number = (
        extract_issue_number_from_branch(branch) if branch is not None else None
    )

    return BranchInfo(
        is_git_repo=True,
        branch_name=branch,
        is_dirty=is_dirty,
        issue_number=issue_number,
        issue_title=None,
        issue_status_label=None,
        cache_last_checked=None,
    )


def get_pr_for_issue(project_dir: Path, issue_number: int) -> Optional[int]:
    """Resolve the PR number linked to ``issue_number`` (issue → branch → PR).

    Returns:
        The PR number for the branch linked to ``issue_number``, or ``None``
        if no repository, branch, or PR can be resolved.
    """
    repo_id = get_repository_identifier(project_dir)
    if repo_id is None:
        return None

    branch_mgr = IssueBranchManager(project_dir=project_dir, repo_url=repo_id.https_url)
    branch_name = branch_mgr.get_branch_with_pr_fallback(
        issue_number, repo_id.owner, repo_id.repo_name
    )
    if branch_name is None:
        return None

    prs = PullRequestManager(project_dir).find_pull_request_by_head(branch_name)
    if not prs:
        return None
    return prs[0]["number"]
