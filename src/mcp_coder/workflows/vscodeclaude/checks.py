"""PR health checks for status-10 issues: merge conflicts, CI, and review comments."""

import logging

from ...config.label_config import (
    build_label_lookups,
    get_labels_config_path,
    load_labels_config,
)
from ...mcp_workspace_github import (
    BaseGitHubManager,
    CIResultsManager,
    EventData,
    IssueBranchManager,
    IssueData,
    IssueEventType,
    IssueManager,
    PullRequestData,
    PullRequestManager,
)
from ...utils.log_utils import OUTPUT
from ...workflow_utils.label_transitions import update_workflow_label
from .config import get_github_username, get_repo_full_name
from .helpers import get_issue_status, is_marked
from .issues import _filter_eligible_vscodeclaude_issues

logger = logging.getLogger(__name__)


def _build_pr_manager(repo_url: str) -> PullRequestManager:
    """Build a PullRequestManager from a repo URL only, no local checkout.

    Bypasses PullRequestManager.__init__ (which requires project_dir) the
    same way label_transitions.py already does for IssueBranchManager.

    Returns:
        A PullRequestManager instance backed by the given repo URL.
    """
    manager = PullRequestManager.__new__(PullRequestManager)
    BaseGitHubManager.__init__(manager, repo_url=repo_url)
    return manager


def _review_comments_watermark(
    events: list[EventData],
    review_label_name: str,
    created_label_name: str,
) -> str | None:
    """Derive the comment-watermark timestamp from an issue's label history.

    Returns:
        The ``created_at`` of the ``status-10`` relabel that followed the
        last ``status-91`` event, or ``None`` if there is no such event pair
        (first-ever arrival, or no relabel followed it) — meaning "no
        filter, every existing comment counts."
    """
    last_review_idx: int | None = None
    for idx, event in enumerate(events):
        if event["label"] == review_label_name:
            last_review_idx = idx

    if last_review_idx is None:
        return None

    for event in events[last_review_idx + 1 :]:
        if event["label"] == created_label_name:
            return event["created_at"]

    return None


def _escalate(
    issue: IssueData,
    issue_manager: IssueManager,
    to_label_id: str,
    to_label_name: str,
    repo_name: str,
) -> None:
    """Set the escalation label; log one OUTPUT line only if the update succeeded."""
    if update_workflow_label(
        issue_manager,
        "pr_created",
        to_label_id,
        validated_issue_number=issue["number"],
    ):
        logger.log(
            OUTPUT, "PR-health: %s #%d → %s", repo_name, issue["number"], to_label_name
        )


def _resolve_pr_target(
    issue: IssueData,
    branch_manager: IssueBranchManager,
    pr_manager: PullRequestManager,
    repo_owner: str,
    repo_gh_name: str,
) -> tuple[str | None, PullRequestData | None]:
    """Resolve an issue's branch and open PR once. Never raises.

    Returns:
        ``(None, None)`` when no branch could be resolved (skip the issue),
        ``(branch, None)`` when no PR was found (CI check only), otherwise
        ``(branch, pr)``.
    """
    try:
        branch = branch_manager.get_branch_with_pr_fallback(
            issue["number"], repo_owner, repo_gh_name
        )
    except Exception as exc:  # pylint: disable=broad-exception-caught  # non-blocking by design
        logger.warning(
            "Failed to resolve branch for issue #%d: %s", issue["number"], exc
        )
        return None, None
    if branch is None:
        return None, None
    try:
        prs = pr_manager.find_pull_request_by_head(branch)
    except Exception as exc:  # pylint: disable=broad-exception-caught  # non-blocking by design
        logger.warning("Failed to look up PR for issue #%d: %s", issue["number"], exc)
        return branch, None
    return branch, (prs[0] if prs else None)


def _check_merge_conflict(
    issue: IssueData,
    pr: PullRequestData,
    issue_manager: IssueManager,
    repo_name: str,
    target_label_name: str,
) -> bool:
    """Escalate a status-10 PR to status-71 if GitHub reports it as "dirty".

    Never raises: any failure is logged and swallowed so one bad issue
    can't block the rest of the batch this poll.

    Returns:
        True iff a merge conflict was detected (label update attempted).
    """
    try:
        if pr["mergeable_state"] == "dirty":
            _escalate(
                issue, issue_manager, "merge_conflict", target_label_name, repo_name
            )
            return True
        return False
    except Exception as exc:  # pylint: disable=broad-exception-caught  # non-blocking by design
        logger.warning(
            "Failed to check merge conflict for issue #%d: %s",
            issue["number"],
            exc,
        )
        return False


def _check_ci(
    issue: IssueData,
    branch: str,
    ci_manager: CIResultsManager,
    issue_manager: IssueManager,
    repo_name: str,
    target_label_name: str,
) -> bool:
    """Escalate a status-10 PR to status-81 if its latest CI run failed.

    Never raises: any failure is logged and swallowed so one bad issue
    can't block the rest of the batch this poll.

    Returns:
        True iff a failed CI run was detected (label update attempted).
    """
    try:
        status = ci_manager.get_latest_ci_status(branch)
        run = status.get("run", {})
        if run.get("status") == "completed" and run.get("conclusion") != "success":
            _escalate(issue, issue_manager, "failing_ci", target_label_name, repo_name)
            return True
        return False
    except Exception as exc:  # pylint: disable=broad-exception-caught  # non-blocking by design
        logger.warning(
            "Failed to check CI status for issue #%d: %s",
            issue["number"],
            exc,
        )
        return False


def _check_review_comments(
    issue: IssueData,
    pr: PullRequestData,
    pr_manager: PullRequestManager,
    issue_manager: IssueManager,
    repo_name: str,
    review_label_name: str,
    created_label_name: str,
) -> bool:
    """Escalate a status-10 PR to status-91 on outstanding review feedback.

    Unresolved threads always count. Changes-requested reviews and
    conversation comments count only if newer than the last status-91 →
    status-10 relabel; comments whose first line carries ❌ (automated
    mcp-coder notes) never count.

    Never raises: any failure is logged and swallowed so one bad issue
    can't block the rest of the batch this poll.

    Returns:
        True iff outstanding review feedback was detected (label update
        attempted).
    """
    try:
        feedback = pr_manager.get_pr_feedback(pr["number"])
        if feedback["unresolved_threads"]:
            triggered = True
        else:
            comments = [
                comment
                for comment in feedback["conversation_comments"]
                if not is_marked(comment["body"])
            ]
            timestamps = [
                review["submitted_at"] for review in feedback["changes_requested"]
            ] + [comment["created_at"] for comment in comments]
            if not timestamps:
                triggered = False
            else:
                events = issue_manager.get_issue_events(
                    issue["number"], IssueEventType.LABELED
                )
                watermark = _review_comments_watermark(
                    events, review_label_name, created_label_name
                )
                triggered = watermark is None or any(
                    ts is None or ts > watermark for ts in timestamps
                )
        if triggered:
            _escalate(
                issue,
                issue_manager,
                "pr_review_comments",
                review_label_name,
                repo_name,
            )
            return True
        return False
    except Exception as exc:  # pylint: disable=broad-exception-caught  # non-blocking by design
        logger.warning(
            "Failed to check review comments for issue #%d: %s",
            issue["number"],
            exc,
        )
        return False


def check_pr_health(
    repo_name: str,
    repo_config: dict[str, str],
    all_cached_issues: list[IssueData],
) -> None:
    """Run PR-health checks on the repo's status-10 issues. Never raises.

    Checks run in a fixed order — merge conflict, failing CI, review
    comments — and stop at the first hit, so each issue gets at most one
    label change per poll.

    Args:
        repo_name: Repository config name, used only in the OUTPUT line.
        repo_config: Repository config dict containing at minimum ``repo_url``.
        all_cached_issues: All cached issues for the repo.
    """
    try:
        github_username = get_github_username()
        pr_issues = [
            issue
            for issue in _filter_eligible_vscodeclaude_issues(
                all_cached_issues, github_username
            )
            if get_issue_status(issue) == "status-10:pr-created"
        ]
        if not pr_issues:
            return
        repo_full_name = get_repo_full_name(repo_config)
        repo_owner, repo_gh_name = repo_full_name.split("/", 1)
        repo_url = f"https://github.com/{repo_full_name}"
        issue_manager = IssueManager(repo_url=repo_url)
        branch_manager = IssueBranchManager(repo_url=repo_url)
        ci_manager = CIResultsManager(repo_url=repo_url)
        pr_manager = _build_pr_manager(repo_url)
        label_names = build_label_lookups(
            load_labels_config(get_labels_config_path(None))
        )["id_to_name"]
    except Exception as exc:  # pylint: disable=broad-exception-caught  # non-blocking by design
        logger.warning("PR-health: skipping repo %s: %s", repo_name, exc)
        return

    for issue in pr_issues:
        branch, pr = _resolve_pr_target(
            issue, branch_manager, pr_manager, repo_owner, repo_gh_name
        )
        if branch is None:
            continue
        _ = (
            (
                pr is not None
                and _check_merge_conflict(
                    issue, pr, issue_manager, repo_name, label_names["merge_conflict"]
                )
            )
            or _check_ci(
                issue,
                branch,
                ci_manager,
                issue_manager,
                repo_name,
                label_names["failing_ci"],
            )
            or (
                pr is not None
                and _check_review_comments(
                    issue,
                    pr,
                    pr_manager,
                    issue_manager,
                    repo_name,
                    label_names["pr_review_comments"],
                    label_names["pr_created"],
                )
            )
        )
