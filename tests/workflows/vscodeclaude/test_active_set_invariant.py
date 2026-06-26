"""Invariant tests: the assessment is built once per command at entry.

Verifies the observe/apply split (Step 5b):
- both ``execute_coordinator_vscodeclaude`` (launch) and
  ``execute_coordinator_vscodeclaude_status`` (status) build the per-session
  assessment exactly once at command entry via ``build_assessments`` (one
  ``DetectionSnapshot`` per command), regardless of how many downstream
  consumers (cleanup, restart, status table) read the result;
- launch applies the assessment exactly once (``apply_assessments`` — the single
  mutation point); status is WRITE-FREE and never applies.
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
from mcp_coder.workflows.vscodeclaude.types import (
    Decision,
    DetectionSignals,
    IssueState,
    LivenessRule,
    LivenessVerdict,
    SessionAction,
    SessionAssessment,
    Transition,
    VSCodeClaudeSession,
)


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


def _assessment(folder: str, *, active: bool = False) -> SessionAssessment:
    """Build a minimal SessionAssessment for the active_set projection."""
    rule = LivenessRule.TITLE if active else LivenessRule.NO_MATCH
    return SessionAssessment(
        folder=folder,
        signals=DetectionSignals(
            folder_exists=True,
            title_match=active,
            cmdline_match=False,
            pid_alive=False,
            found_pid=None,
            age_seconds=0.0,
            within_grace=False,
            directory_empty=False,
        ),
        verdict=LivenessVerdict(active=active, rule=rule),
        issue_state=IssueState(
            is_open=True,
            is_stale=False,
            is_blocked=False,
            is_unassigned=False,
            is_eligible=True,
        ),
        transition=Transition(flipped_to_inactive=False),
        decision=Decision(action=SessionAction.SKIP, reason="", destructive=False),
        pid_needs_refresh=False,
        found_pid=None,
    )


def _patch_common(
    monkeypatch: pytest.MonkeyPatch,
    sessions: list[VSCodeClaudeSession],
    tmp_path: Path,
) -> tuple[Mock, Mock]:
    """Patch shared dependencies; return (build_assessments, apply_assessments) mocks."""
    # Isolate sessions.json writes
    monkeypatch.setattr(
        "mcp_coder.workflows.vscodeclaude.sessions.get_sessions_file_path",
        lambda: tmp_path / "sessions.json",
    )

    # One assessment per session at command entry (the read-only build).
    build_mock = Mock(
        side_effect=lambda sess, cached=None: {
            s["folder"]: _assessment(s["folder"]) for s in sess
        }
    )
    monkeypatch.setattr(
        "mcp_coder.cli.commands.coordinator.commands.build_assessments",
        build_mock,
    )

    # The single mutation point — patched so we can assert call counts without
    # touching disk.
    apply_mock = Mock()
    monkeypatch.setattr(
        "mcp_coder.cli.commands.coordinator.commands.apply_assessments",
        apply_mock,
    )

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

    return build_mock, apply_mock


class TestBuildOnceInvariant:
    """build_assessments runs exactly once per command (one snapshot per command)."""

    def test_launch_builds_once_and_applies_once(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Launch builds the assessment once and applies it once (mutation point)."""
        sessions = _build_sessions(tmp_path, count=3)
        build_mock, apply_mock = _patch_common(monkeypatch, sessions, tmp_path)

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
        assert build_mock.call_count == 1
        apply_mock.assert_called_once()

    def test_status_builds_once_and_never_applies(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Status builds the assessment once and is write-free (no apply)."""
        sessions = _build_sessions(tmp_path, count=4)
        build_mock, apply_mock = _patch_common(monkeypatch, sessions, tmp_path)

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
        assert build_mock.call_count == 1
        apply_mock.assert_not_called()
        # The prebuilt assessments were threaded through to the display function
        assert "assessments" in captured
        assert set(captured["assessments"].keys()) == {s["folder"] for s in sessions}
