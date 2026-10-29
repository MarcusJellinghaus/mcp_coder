"""Test that execute_coordinator_vscodeclaude runs PR-health checks per repo.

Regression test for #1238: the checks must run even when all session slots
are used, i.e. outside the capacity gate of ``process_eligible_issues``.
"""

import argparse
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

REPO_URLS = {
    "repo_a": "https://github.com/owner/repo_a.git",
    "repo_b": "https://github.com/owner/repo_b.git",
}


def _run(args_repo: str | None, mocks: dict[str, MagicMock]) -> None:
    """Configure the mocks for two repos at capacity and run the command."""
    mocks["create_config"].return_value = False
    mocks["load_vsc_config"].return_value = {
        "workspace_base": "/tmp",
        "max_sessions": 1,
    }
    mocks["load_config"].return_value = {
        "coordinator": {"repos": {"repo_a": {}, "repo_b": {}}}
    }
    mocks["load_sessions"].return_value = {"sessions": [], "last_updated": ""}
    mocks["build_cache"].return_value = (
        {
            "owner/repo_a": {1: {"number": 1}},
            "owner/repo_b": {2: {"number": 2}},
        },
        set(),
    )
    # One active session => at capacity for max_sessions=1.
    mocks["build_assess"].return_value = {
        "/tmp/repo_a_111": SimpleNamespace(verdict=SimpleNamespace(active=True)),
    }
    mocks["restart"].return_value = []
    mocks["load_repo"].side_effect = lambda name: {"repo_url": REPO_URLS[name]}
    mocks["process"].return_value = []

    args = argparse.Namespace(
        repo=args_repo,
        max_sessions=None,
        cleanup=False,
        intervene=False,
        issue=None,
        no_install_from_github=False,
    )

    from mcp_coder.cli.commands.coordinator.commands_vscodeclaude import (
        execute_coordinator_vscodeclaude,
    )

    assert execute_coordinator_vscodeclaude(args) == 0


_MODULE = "mcp_coder.cli.commands.coordinator.commands_vscodeclaude"


@patch(f"{_MODULE}.check_pr_health")
@patch(f"{_MODULE}.apply_assessments")
@patch(f"{_MODULE}.process_eligible_issues")
@patch(f"{_MODULE}.restart_closed_sessions")
@patch(f"{_MODULE}.cleanup_stale_sessions")
@patch(f"{_MODULE}.build_assessments")
@patch(f"{_MODULE}._build_cached_issues_by_repo")
@patch(f"{_MODULE}.load_sessions")
@patch(f"{_MODULE}.load_config")
@patch(f"{_MODULE}.load_vscodeclaude_config")
@patch(f"{_MODULE}.load_repo_config")
@patch(f"{_MODULE}.create_default_config")
class TestPrHealthOutsideCapacityGate:
    """check_pr_health runs once per repo, regardless of session capacity."""

    def test_called_for_every_repo_at_capacity(
        self,
        mock_create_config: MagicMock,
        mock_load_repo: MagicMock,
        mock_load_vsc_config: MagicMock,
        mock_load_config: MagicMock,
        mock_load_sessions: MagicMock,
        mock_build_cache: MagicMock,
        mock_build_assess: MagicMock,
        mock_cleanup: MagicMock,
        mock_restart: MagicMock,
        mock_process: MagicMock,
        mock_apply: MagicMock,
        mock_pr_health: MagicMock,
    ) -> None:
        """At capacity, both repos still get their PR-health checks."""
        _run(
            None,
            {
                "create_config": mock_create_config,
                "load_repo": mock_load_repo,
                "load_vsc_config": mock_load_vsc_config,
                "load_config": mock_load_config,
                "load_sessions": mock_load_sessions,
                "build_cache": mock_build_cache,
                "build_assess": mock_build_assess,
                "restart": mock_restart,
                "process": mock_process,
            },
        )

        assert mock_pr_health.call_count == 2
        calls = [c.args for c in mock_pr_health.call_args_list]
        assert calls[0] == (
            "repo_a",
            {"repo_url": REPO_URLS["repo_a"]},
            [{"number": 1}],
        )
        assert calls[1] == (
            "repo_b",
            {"repo_url": REPO_URLS["repo_b"]},
            [{"number": 2}],
        )

    def test_repo_filter_limits_to_one_repo(
        self,
        mock_create_config: MagicMock,
        mock_load_repo: MagicMock,
        mock_load_vsc_config: MagicMock,
        mock_load_config: MagicMock,
        mock_load_sessions: MagicMock,
        mock_build_cache: MagicMock,
        mock_build_assess: MagicMock,
        mock_cleanup: MagicMock,
        mock_restart: MagicMock,
        mock_process: MagicMock,
        mock_apply: MagicMock,
        mock_pr_health: MagicMock,
    ) -> None:
        """--repo repo_b runs the PR-health checks for repo_b only."""
        _run(
            "repo_b",
            {
                "create_config": mock_create_config,
                "load_repo": mock_load_repo,
                "load_vsc_config": mock_load_vsc_config,
                "load_config": mock_load_config,
                "load_sessions": mock_load_sessions,
                "build_cache": mock_build_cache,
                "build_assess": mock_build_assess,
                "restart": mock_restart,
                "process": mock_process,
            },
        )

        mock_pr_health.assert_called_once_with(
            "repo_b",
            {"repo_url": REPO_URLS["repo_b"]},
            [{"number": 2}],
        )


# ---------------------------------------------------------------------------
# Call-count acceptance: a warm second run makes almost no GitHub requests.
# ---------------------------------------------------------------------------

_CHECKS = "mcp_coder.workflows.vscodeclaude.checks"
_STORE = "mcp_workspace.github_operations.caching._store"
_EVENTS = "mcp_workspace.github_operations.issues.events_mixin.EventsMixin"
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
        from mcp_coder.mcp_workspace_github import (
            BranchLookup,
            IssueData,
            RepoIdentifier,
        )
        from mcp_coder.workflows.vscodeclaude.checks import check_pr_health
        from tests.github_factories import make_issue_data

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
        escalate = MagicMock()

        monkeypatch.setattr(f"{_EVENTS}.get_issue_events", get_issue_events)
        monkeypatch.setattr(f"{_CHECKS}.PullRequestManager", lambda **kw: pr_manager)
        monkeypatch.setattr(
            f"{_CHECKS}.IssueBranchManager", lambda **kw: branch_manager
        )
        monkeypatch.setattr(f"{_CHECKS}.CIResultsManager", lambda **kw: ci_manager)
        monkeypatch.setattr(f"{_CHECKS}.IssueManager", lambda **kw: MagicMock())
        monkeypatch.setattr(f"{_CHECKS}.get_github_username", lambda: "testuser")
        monkeypatch.setattr(f"{_CHECKS}.get_trusted_commenters", frozenset)
        monkeypatch.setattr(f"{_CHECKS}.update_workflow_label", escalate)

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
        (prs_file,) = (tmp_path / "coordinator_cache").glob("*.prs.json")
        assert len(list((tmp_path / "coordinator_cache").glob("*.branches.json"))) == 1
        data = json.loads(prs_file.read_text(encoding="utf-8"))
        data["snapshot"]["fetched_at"] = (
            datetime.now(UTC) - timedelta(minutes=5)
        ).isoformat()
        prs_file.write_text(json.dumps(data), encoding="utf-8")
        for mock in (repo, pr_manager, branch_manager, ci_manager, get_issue_events):
            mock.reset_mock()

        check_pr_health("repo", repo_config, issues)

        repo.get_pulls.assert_called_once_with(state="open")
        assert sorted(c.args[0] for c in repo.get_branch.call_args_list) == [
            "develop",
            "main",
        ]
        repo.get_pull.assert_not_called()
        repo.get_workflow_runs.assert_not_called()
        pr_manager._collect_pr_feedback.assert_not_called()
        branch_manager.resolve_branch_for_issue.assert_not_called()
        get_issue_events.assert_not_called()
        ci_manager.get_latest_ci_status.assert_called_once_with("4-fix")
        escalate.assert_not_called()
