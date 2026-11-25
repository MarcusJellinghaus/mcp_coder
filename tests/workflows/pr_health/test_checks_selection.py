"""Which cached issues check_pr_health checks.

Selection: open, ``status-10:pr-created`` label, no ``ignore_labels`` label —
regardless of assignee and other ``status-*`` labels. "Checked" means the
issue's branch is looked up.
"""

import pytest

from mcp_coder.mcp_workspace_github import IssueData
from mcp_coder.workflows.pr_health.checks import check_pr_health
from tests.workflows.pr_health.test_checks import REPO_CONFIG, _make_pr_issue, _setup


def _checked(monkeypatch: pytest.MonkeyPatch, issue: IssueData) -> bool:
    _, branch_cache, _, _ = _setup(monkeypatch)
    check_pr_health("test-repo", REPO_CONFIG, [issue])
    return any(call.args == (issue,) for call in branch_cache.lookup.call_args_list)


class TestCheckPrHealthSelection:
    """Selection of status-10 issues from the cached issue list."""

    def test_unassigned_issue_is_checked(self, monkeypatch: pytest.MonkeyPatch) -> None:
        issue = _make_pr_issue(1)
        issue["assignees"] = []

        assert _checked(monkeypatch, issue)

    def test_issue_with_other_status_label_is_checked(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        issue = _make_pr_issue(2, labels=["status-10:pr-created", "status-08:ready-pr"])

        assert _checked(monkeypatch, issue)

    def test_closed_issue_is_not_checked(self, monkeypatch: pytest.MonkeyPatch) -> None:
        issue = _make_pr_issue(3)
        issue["state"] = "closed"

        assert not _checked(monkeypatch, issue)

    def test_issue_with_ignore_label_is_not_checked(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        issue = _make_pr_issue(4, labels=["status-10:pr-created", "blocked"])

        assert not _checked(monkeypatch, issue)
