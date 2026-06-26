"""Invariant tests: is_session_active is called exactly N_sessions times.

Verifies that both ``execute_coordinator_vscodeclaude`` (launch) and
``execute_coordinator_vscodeclaude_status`` (status) build a single
active-set snapshot at command entry — so each session is checked exactly
once per command, regardless of how many downstream consumers
(cleanup, restart, status table) need the result.
"""

import argparse
from pathlib import Path
from typing import Any
from unittest.mock import Mock

import pytest

from mcp_coder.cli.commands.coordinator.commands import (
    execute_coordinator_vscodeclaude,
    execute_coordinator_vscodeclaude_status,
)
from mcp_coder.workflows.vscodeclaude.types import VSCodeClaudeSession


def _build_sessions(tmp_path: Path, count: int) -> list[VSCodeClaudeSession]:
    """Build N mock sessions with on-disk folders so artifacts checks pass."""
    sessions: list[VSCodeClaudeSession] = []
    for i in range(count):
        folder = tmp_path / f"session_{i}"
        folder.mkdir()
        sessions.append(
            {
                "folder": str(folder),
                "repo": "owner/repo",
                "issue_number": 100 + i,
                "status": "status-07:code-review",
                "vscode_pid": 1000 + i,
                "vscode_pid_create_time": None,
                "last_active": None,
                "last_active_rule": None,
                "started_at": "2024-01-01T00:00:00Z",
                "is_intervention": False,
            }
        )
    return sessions


def _patch_common(
    monkeypatch: pytest.MonkeyPatch,
    sessions: list[VSCodeClaudeSession],
    tmp_path: Path,
) -> Mock:
    """Patch shared dependencies and return the is_session_active counter mock."""
    # Isolate sessions.json writes from update_session_pid side effects
    monkeypatch.setattr(
        "mcp_coder.workflows.vscodeclaude.sessions.get_sessions_file_path",
        lambda: tmp_path / "sessions.json",
    )
    monkeypatch.setattr(
        "mcp_coder.workflows.vscodeclaude.sessions.update_session_pid",
        Mock(),
    )

    # Counter to verify is_session_active call count
    call_counter = Mock(return_value=False)
    monkeypatch.setattr(
        "mcp_coder.workflows.vscodeclaude.sessions.is_session_active",
        call_counter,
    )

    # Fast-path build_active_session_set away from real VSCode detection;
    # is_vscode_open_for_folder is only called when is_session_active=True,
    # which our mock returns False, so no need to patch it.

    # Stub out load_sessions to return our fixture sessions
    monkeypatch.setattr(
        "mcp_coder.cli.commands.coordinator.commands.load_sessions",
        lambda: {"sessions": sessions, "last_updated": ""},
    )

    # Skip auto-config creation
    monkeypatch.setattr(
        "mcp_coder.cli.commands.coordinator.commands.create_default_config",
        lambda: False,
    )
    monkeypatch.setattr(
        "mcp_coder.cli.commands.coordinator.commands.load_vscodeclaude_config",
        lambda: {"workspace_base": str(tmp_path), "max_sessions": 10},
    )
    monkeypatch.setattr(
        "mcp_coder.cli.commands.coordinator.commands.load_config",
        lambda: {"coordinator": {"repos": {"myrepo": {}}}},
    )
    # Avoid cache builds that hit GitHub
    monkeypatch.setattr(
        "mcp_coder.cli.commands.coordinator.commands._build_cached_issues_by_repo",
        lambda repo_names, sessions=None: ({}, set()),
    )

    return call_counter


class TestActiveSetInvariant:
    """is_session_active is called exactly once per session per command."""

    def test_launch_calls_is_session_active_n_times(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Verify is_session_active is called exactly N_sessions times per launch."""
        sessions = _build_sessions(tmp_path, count=3)
        call_counter = _patch_common(monkeypatch, sessions, tmp_path)

        # Stub launch-only collaborators
        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.commands.cleanup_stale_sessions",
            Mock(),
        )
        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.commands.restart_closed_sessions",
            Mock(return_value=[]),
        )
        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.commands.process_eligible_issues",
            Mock(return_value=[]),
        )

        args = argparse.Namespace(
            repo=None,
            max_sessions=5,
            cleanup=False,
            intervene=False,
            issue=None,
            no_install_from_github=True,
        )
        result = execute_coordinator_vscodeclaude(args)

        assert result == 0
        assert call_counter.call_count == len(sessions)

    def test_status_calls_is_session_active_n_times(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Verify is_session_active is called exactly N_sessions times per status."""
        sessions = _build_sessions(tmp_path, count=4)
        call_counter = _patch_common(monkeypatch, sessions, tmp_path)

        # Stub status-only collaborators (imported lazily inside the function)
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.issues.build_eligible_issues_with_branch_check",
            lambda repo_names, cached_issues_by_repo=None: ([], set()),
        )

        captured: dict[str, Any] = {}

        def _fake_display(**kwargs: Any) -> None:
            captured.update(kwargs)

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.status.display_status_table",
            _fake_display,
        )

        args = argparse.Namespace(repo=None)
        result = execute_coordinator_vscodeclaude_status(args)

        assert result == 0
        assert call_counter.call_count == len(sessions)
        # Snapshot was threaded through to the display function
        assert "active_set" in captured
        assert set(captured["active_set"].keys()) == {s["folder"] for s in sessions}


class TestStatusPidRefresh:
    """Status now refreshes stale stored PIDs (parity with launch)."""

    def test_status_refreshes_stale_stored_pid(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """build_active_session_set updates stored PID when window detection finds a different one."""
        from mcp_coder.workflows.vscodeclaude.sessions import build_active_session_set

        # Sessions file isolation
        sessions_file = tmp_path / "sessions.json"
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.get_sessions_file_path",
            lambda: sessions_file,
        )

        update_pid_mock = Mock()
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.update_session_pid",
            update_pid_mock,
        )

        # Active in the snapshot
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.is_session_active",
            lambda session: True,
        )

        # Window-title detection finds a NEW PID different from the stored one
        new_pid = 9999
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.is_vscode_open_for_folder",
            lambda folder: (True, new_pid),
        )

        folder = tmp_path / "session_a"
        folder.mkdir()
        session: VSCodeClaudeSession = {
            "folder": str(folder),
            "repo": "owner/repo",
            "issue_number": 1,
            "status": "status-07:code-review",
            "vscode_pid": 1111,  # Stale
            "vscode_pid_create_time": None,
            "last_active": None,
            "last_active_rule": None,
            "started_at": "2024-01-01T00:00:00Z",
            "is_intervention": False,
        }

        build_active_session_set([session])

        update_pid_mock.assert_called_once_with(str(folder), new_pid)
