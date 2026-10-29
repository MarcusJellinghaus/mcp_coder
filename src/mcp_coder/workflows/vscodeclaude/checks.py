"""PR health checks for status-10 issues: merge conflicts, CI, and review comments."""

import logging

from ...config.label_config import (
    build_label_lookups,
    get_labels_config_path,
    load_labels_config,
)
from ...mcp_workspace_github import (
    BranchLookupCache,
    CIResultsManager,
    EventData,
    IssueBranchManager,
    IssueData,
    IssueManager,
    OpenPullRequest,
    PullRequestCache,
    PullRequestManager,
    get_trusted_commenters,
    is_trusted_author,
)
from ...utils.log_utils import OUTPUT
from ...workflow_utils.label_transitions import update_workflow_label
from ...workflow_utils.rate_limit import raise_if_rate_limited
from .config import get_github_username, get_repo_full_name
from .helpers import get_issue_status, is_marked
from .issues import _filter_eligible_vscodeclaude_issues, lookup_branch

logger = logging.getLogger(__name__)


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
    branch_cache: BranchLookupCache,
    pr_cache: PullRequestCache,
) -> tuple[str | None, OpenPullRequest | None]:
    """Resolve an issue's branch and open PR once.

    Never raises, except ``GitHubRateLimitError``: any other branch-lookup
    failure skips the issue, any other PR-lookup failure degrades to the
    CI-only check.

    Returns:
        ``(None, None)`` when no branch could be resolved (skip the issue),
        ``(branch, None)`` when no PR was found (CI check only), otherwise
        ``(branch, pr)``.
    """
    branch = lookup_branch(branch_cache, issue)
    if branch is None:
        return None, None
    try:
        pr = pr_cache.find_pr(branch)
    except Exception as exc:  # pylint: disable=broad-exception-caught  # non-blocking by design
        raise_if_rate_limited(exc)
        logger.warning("Failed to look up PR for issue #%d: %s", issue["number"], exc)
        return branch, None
    return branch, pr


def _check_merge_conflict(
    issue: IssueData,
    pr: OpenPullRequest,
    pr_cache: PullRequestCache,
    issue_manager: IssueManager,
    repo_name: str,
    target_label_name: str,
) -> bool:
    """Escalate a status-10 PR to status-71 if GitHub reports it as "dirty".

    Never raises, except ``GitHubRateLimitError``: any other failure is
    logged and swallowed so one bad issue can't block the rest of the batch
    this poll.

    Returns:
        True iff a merge conflict was detected (label update attempted).
    """
    try:
        if pr_cache.mergeable_state(pr, issue) == "dirty":
            _escalate(
                issue, issue_manager, "merge_conflict", target_label_name, repo_name
            )
            return True
        return False
    except Exception as exc:  # pylint: disable=broad-exception-caught  # non-blocking by design
        raise_if_rate_limited(exc)
        logger.warning(
            "Failed to check merge conflict for issue #%d: %s",
            issue["number"],
            exc,
        )
        return False


def _check_ci(
    issue: IssueData,
    branch: str,
    pr: OpenPullRequest | None,
    pr_cache: PullRequestCache,
    ci_manager: CIResultsManager,
    issue_manager: IssueManager,
    repo_name: str,
    target_label_name: str,
) -> bool:
    """Escalate a status-10 PR to status-81 if its latest CI run failed.

    With an open PR the status comes from ``pr_cache``; without one it is
    fetched live for ``branch``.

    Never raises, except ``GitHubRateLimitError``: any other failure is
    logged and swallowed so one bad issue can't block the rest of the batch
    this poll.

    Returns:
        True iff a failed CI run was detected (label update attempted).
    """
    try:
        status = (
            pr_cache.ci_status(pr, issue)
            if pr is not None
            else ci_manager.get_latest_ci_status(branch)
        )
        run = status.get("run", {})
        if run.get("status") == "completed" and run.get("conclusion") != "success":
            _escalate(issue, issue_manager, "failing_ci", target_label_name, repo_name)
            return True
        return False
    except Exception as exc:  # pylint: disable=broad-exception-caught  # non-blocking by design
        raise_if_rate_limited(exc)
        logger.warning(
            "Failed to check CI status for issue #%d: %s",
            issue["number"],
            exc,
        )
        return False


def _check_review_comments(
    issue: IssueData,
    pr: OpenPullRequest,
    pr_cache: PullRequestCache,
    issue_manager: IssueManager,
    repo_name: str,
    review_label_name: str,
    created_label_name: str,
    trusted: frozenset[str],
) -> bool:
    """Escalate a status-10 PR to status-91 on outstanding review feedback.

    Only items by trusted authors (OWNER/MEMBER/COLLABORATOR or a login in
    ``trusted``) escalate, and only on a PR whose author is trusted.
    Unresolved threads always count. Changes-requested reviews and
    conversation comments count only if newer than the last status-91 →
    status-10 relabel; comments whose first line carries ❌ (automated
    mcp-coder notes) never count. Untrusted items that would otherwise
    count produce at most one OUTPUT line and no label change.

    Never raises, except ``GitHubRateLimitError``: any other failure is
    logged and swallowed so one bad issue can't block the rest of the batch
    this poll.

    Returns:
        True iff outstanding trusted review feedback was detected (label
        update attempted).
    """
    try:
        if not is_trusted_author(pr["user"], pr["author_association"], trusted):
            logger.log(
                OUTPUT,
                "PR-health: %s #%d: untrusted PR author @%s — review comments not checked",
                repo_name,
                issue["number"],
                pr["user"],
            )
            return False

        def ok(login: str | None, association: str | None) -> bool:
            return is_trusted_author(login, association, trusted)

        feedback = pr_cache.feedback(pr, issue)
        threads = feedback["unresolved_threads"]
        if any(ok(t["author"], t["author_association"]) for t in threads):
            _escalate(
                issue, issue_manager, "pr_review_comments", review_label_name, repo_name
            )
            return True

        items: list[tuple[str, str | None, str | None]] = [
            (r["author"], r["author_association"], r["submitted_at"])
            for r in feedback["changes_requested"]
        ] + [
            (c["author"], c["author_association"], c["created_at"])
            for c in feedback["conversation_comments"]
            if not is_marked(c["body"])
        ]
        watermark = (
            _review_comments_watermark(
                pr_cache.label_events(pr, issue),
                review_label_name,
                created_label_name,
            )
            if items
            else None
        )
        new = [
            item
            for item in items
            if item[2] is None or watermark is None or item[2] > watermark
        ]
        if any(ok(login, assoc) for login, assoc, _ in new):
            _escalate(
                issue, issue_manager, "pr_review_comments", review_label_name, repo_name
            )
            return True

        logins = dict.fromkeys(
            [
                t["author"]
                for t in threads
                if not ok(t["author"], t["author_association"])
            ]
            + [login for login, assoc, _ in new if not ok(login, assoc)]
        )
        if logins:
            logger.log(
                OUTPUT,
                "PR-health: %s #%d: untrusted PR feedback from %s — review manually",
                repo_name,
                issue["number"],
                ", ".join(f"@{login}" for login in logins),
            )
        return False
    except Exception as exc:  # pylint: disable=broad-exception-caught  # non-blocking by design
        raise_if_rate_limited(exc)
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
    """Run PR-health checks on the repo's status-10 issues.

    Never raises, except ``GitHubRateLimitError``, which propagates.

    Checks run in a fixed order — merge conflict, failing CI, review
    comments — and stop at the first hit, so each issue gets at most one
    label change per poll. All PR queries go through one run-scoped
    ``PullRequestCache`` and branch lookups through one ``BranchLookupCache``,
    each saved once after the loop (also when a rate limit ends it early).

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
        repo_url = f"https://github.com/{repo_full_name}"
        issue_manager = IssueManager(repo_url=repo_url)
        ci_manager = CIResultsManager(repo_url=repo_url)
        branch_cache = BranchLookupCache.load(IssueBranchManager(repo_url=repo_url))
        pr_cache = PullRequestCache.load(PullRequestManager(repo_url=repo_url))
        label_names = build_label_lookups(
            load_labels_config(get_labels_config_path(None))
        )["id_to_name"]
        trusted = get_trusted_commenters()
    except Exception as exc:  # pylint: disable=broad-exception-caught  # non-blocking by design
        raise_if_rate_limited(exc)
        logger.warning("PR-health: skipping repo %s: %s", repo_name, exc)
        return

    try:
        for issue in pr_issues:
            branch, pr = _resolve_pr_target(issue, branch_cache, pr_cache)
            if branch is None:
                continue
            _ = (
                (
                    pr is not None
                    and _check_merge_conflict(
                        issue,
                        pr,
                        pr_cache,
                        issue_manager,
                        repo_name,
                        label_names["merge_conflict"],
                    )
                )
                or _check_ci(
                    issue,
                    branch,
                    pr,
                    pr_cache,
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
                        pr_cache,
                        issue_manager,
                        repo_name,
                        label_names["pr_review_comments"],
                        label_names["pr_created"],
                        trusted,
                    )
                )
            )
    finally:
        # Keeps fetched results when a rate limit came from elsewhere; a
        # cache's own rate limit makes its save a no-op.
        try:
            pr_cache.save()
        finally:
            branch_cache.save()
