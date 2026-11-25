"""Call-count acceptance: a warm second check_pr_health run makes almost no GitHub requests."""

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from mcp_coder.mcp_workspace_github import BranchLookup, IssueData, RepoIdentifier
from mcp_coder.workflows.pr_health.checks import check_pr_health
from tests.github_factories import make_issue_data

CHECKS = "mcp_coder.workflows.pr_health.checks"
_STORE = "mcp_workspace.github_operations.caching._store"
_EVENTS = "mcp_workspace.github_operations.issues.events_mixin.EventsMixin"
_FETCH_ALERTS = (
    "mcp_workspace.github_operations._pr_feedback_sources.fetch_code_scanning_alerts"
)
_ISSUE_UPDATED_AT = "2024-07-01T00:00:00+00:00"


def _gh_pr(number: int, base: str) -> SimpleNamespace:
    """A PyGithub-like open-PR list item."""
    return SimpleNamespace(
        number=number,
        head=SimpleNamespace(
            ref=f"{number}-fix", sha=f"sha{number}", label=f"owner:{number}-fix"
        ),
        base=SimpleNamespace(ref=base),
        updated_at=datetime(2024, 7, 1, tzinfo=UTC),
        user=SimpleNamespace(login="owner"),
        author_association="OWNER",
        draft=False,
    )


def _gh_run() -> SimpleNamespace:
    """A completed, successful PyGithub-like workflow run."""
    return SimpleNamespace(
        id=1,
        status="completed",
        conclusion="success",
        name="CI",
        event="pull_request",
        path=".github/workflows/ci.yml",
        created_at=datetime(2024, 7, 1, tzinfo=UTC),
        html_url="https://github.com/owner/repo/actions/runs/1",
    )


def _feedback() -> dict[str, object]:
    """Feedback with one untrusted comment: label events get read, no escalation."""
    return {
        "unresolved_threads": [],
        "resolved_thread_count": 0,
        "changes_requested": [],
        "conversation_comments": [
            {
                "author": "stranger",
                "body": "hi",
                "id": 1,
                "created_at": "2024-07-02T00:00:00+00:00",
                "author_association": "NONE",
            }
        ],
        "alerts": [],
        "unavailable": {},
    }


class TestPrHealthWarmCacheCallCount:
    """With warm PR and branch caches, check_pr_health barely touches GitHub."""

    def test_second_run_only_lists_prs_and_base_tips(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(f"{_STORE}.get_user_app_data_dir", lambda app: tmp_path)
        identifier = RepoIdentifier.from_full_name("owner/repo")

        # Three PRs over two base branches; issue 4 has a branch but no PR.
        repo = MagicMock()
        repo.get_pulls.return_value = [
            _gh_pr(1, "main"),
            _gh_pr(2, "main"),
            _gh_pr(3, "develop"),
        ]
        repo.get_branch.side_effect = lambda name: SimpleNamespace(
            commit=SimpleNamespace(sha=f"tip-{name}")
        )
        repo.get_pull.return_value = SimpleNamespace(mergeable_state="clean")
        repo.get_workflow_runs.return_value = [_gh_run()]

        pr_manager = MagicMock()
        pr_manager.repo_identifier = identifier
        pr_manager._get_repository.return_value = repo
        pr_manager._collect_pr_feedback.side_effect = lambda *a, **k: _feedback()

        branch_manager = MagicMock()
        branch_manager.repo_identifier = identifier
        branch_manager.resolve_branch_for_issue.side_effect = (
            lambda number, owner, name: BranchLookup("found", f"{number}-fix")
        )

        ci_manager = MagicMock()
        ci_manager.get_latest_ci_status.return_value = {"run": {}, "jobs": []}
        get_issue_events = MagicMock(return_value=[])
        fetch_alerts = MagicMock(return_value=[])
        escalate = MagicMock()

        monkeypatch.setattr(f"{_EVENTS}.get_issue_events", get_issue_events)
        monkeypatch.setattr(_FETCH_ALERTS, fetch_alerts)
        monkeypatch.setattr(f"{CHECKS}.PullRequestManager", lambda **kw: pr_manager)
        monkeypatch.setattr(f"{CHECKS}.IssueBranchManager", lambda **kw: branch_manager)
        monkeypatch.setattr(f"{CHECKS}.CIResultsManager", lambda **kw: ci_manager)
        monkeypatch.setattr(f"{CHECKS}.IssueManager", lambda **kw: MagicMock())
        monkeypatch.setattr(f"{CHECKS}.get_trusted_commenters", frozenset)
        monkeypatch.setattr(f"{CHECKS}.update_workflow_label", escalate)

        issues: list[IssueData] = [
            make_issue_data(
                number=n,
                labels=["status-10:pr-created"],
                assignees=["testuser"],
                updated_at=_ISSUE_UPDATED_AT,
            )
            for n in (1, 2, 3, 4)
        ]
        repo_config = {"repo_url": "https://github.com/owner/repo"}

        # Warm run, then age the PR snapshot past the duplicate-protection window.
        check_pr_health("repo", repo_config, issues)
        assert branch_manager.resolve_branch_for_issue.call_count == 4
        assert get_issue_events.call_count == 3
        assert repo.get_workflow_runs.call_count == 3
        assert fetch_alerts.call_count == 3
        (prs_file,) = (tmp_path / "coordinator_cache").glob("*.prs.json")
        assert len(list((tmp_path / "coordinator_cache").glob("*.branches.json"))) == 1
        data = json.loads(prs_file.read_text(encoding="utf-8"))
        data["snapshot"]["fetched_at"] = (
            datetime.now(UTC) - timedelta(minutes=5)
        ).isoformat()
        prs_file.write_text(json.dumps(data), encoding="utf-8")
        for mock in (
            repo,
            pr_manager,
            branch_manager,
            ci_manager,
            get_issue_events,
            fetch_alerts,
        ):
            mock.reset_mock()

        check_pr_health("repo", repo_config, issues)

        repo.get_pulls.assert_called_once_with(state="open")
        assert sorted(c.args[0] for c in repo.get_branch.call_args_list) == [
            "develop",
            "main",
        ]
        repo.get_pull.assert_not_called()
        repo.get_workflow_runs.assert_not_called()
        fetch_alerts.assert_not_called()
        pr_manager._collect_pr_feedback.assert_not_called()
        branch_manager.resolve_branch_for_issue.assert_not_called()
        get_issue_events.assert_not_called()
        ci_manager.get_latest_ci_status.assert_called_once_with("4-fix")
        escalate.assert_not_called()
