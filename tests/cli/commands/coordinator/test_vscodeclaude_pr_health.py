"""Test that execute_coordinator_vscodeclaude runs PR-health checks per repo.

Regression test for #1238: the checks must run even when all session slots
are used, i.e. outside the capacity gate of ``process_eligible_issues``.
"""

import argparse
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

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
