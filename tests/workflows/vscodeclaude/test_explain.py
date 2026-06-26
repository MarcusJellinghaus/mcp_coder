"""Tests for the ``--explain`` on-demand transparency surface (Step 10).

``--explain`` renders the already-built assessments via the shared
``SessionAssessment.to_explain()`` serializer. It is READ-ONLY: it must never
trigger ``apply_assessments`` (no PID refresh, no ``last_active`` advance, no
audit write), consistent with status being write-free.
"""

import argparse
from pathlib import Path
from typing import Any
from unittest.mock import Mock

import pytest

from mcp_coder.cli.commands.coordinator.commands import (
    execute_coordinator_vscodeclaude_status,
)
from mcp_coder.cli.main import create_parser
from mcp_coder.workflows.vscodeclaude.assessment import render_explain
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


def _make_assessment(folder: str = "/path/to/folder") -> SessionAssessment:
    """Build a sample assessment exercising every signal field and a winning rule."""
    return SessionAssessment(
        folder=folder,
        signals=DetectionSignals(
            folder_exists=True,
            title_match=True,
            cmdline_match=False,
            pid_alive=True,
            found_pid=4321,
            age_seconds=42.5,
            within_grace=False,
            directory_empty=False,
        ),
        verdict=LivenessVerdict(active=True, rule=LivenessRule.TITLE),
        issue_state=IssueState(
            is_open=True,
            is_stale=False,
            is_blocked=False,
            is_unassigned=False,
            is_eligible=True,
            stale_target=None,
        ),
        transition=Transition(flipped_to_inactive=False),
        decision=Decision(
            action=SessionAction.KEEP_ACTIVE,
            reason="vscode running",
            destructive=False,
        ),
        pid_needs_refresh=False,
        found_pid=4321,
    )


class TestRenderExplain:
    """render_explain dumps the full signals + winning rule per session."""

    def test_includes_every_signal_field_and_winning_rule(self) -> None:
        """Every DetectionSignals field and the winning rule appear in the dump."""
        text = render_explain({"/path/to/folder": _make_assessment()})

        for signal_field in (
            "folder_exists",
            "title_match",
            "cmdline_match",
            "pid_alive",
            "found_pid",
            "age_seconds",
            "within_grace",
            "directory_empty",
        ):
            assert signal_field in text

        # Winning liveness rule + the decided action are both rendered.
        assert "title" in text
        assert "keep_active" in text
        assert "/path/to/folder" in text

    def test_one_block_per_session(self) -> None:
        """Each session contributes its own to_explain() block."""
        assessments = {
            "/a": _make_assessment("/a"),
            "/b": _make_assessment("/b"),
        }

        text = render_explain(assessments)

        assert "folder: /a" in text
        assert "folder: /b" in text

    def test_empty_assessments_render_empty_string(self) -> None:
        """No sessions -> empty string (no crash)."""
        assert render_explain({}) == ""


class TestExplainParser:
    """The status subcommand accepts --explain (default False)."""

    def test_explain_flag_sets_true(self) -> None:
        parser = create_parser()
        args = parser.parse_args(["vscodeclaude", "status", "--explain"])
        assert args.explain is True

    def test_explain_defaults_false(self) -> None:
        parser = create_parser()
        args = parser.parse_args(["vscodeclaude", "status"])
        assert args.explain is False


class TestExplainIsWriteFree:
    """--explain on the status path performs no disk writes."""

    def test_status_explain_triggers_no_disk_write(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """--explain renders and returns 0 without writing sessions.json/audit."""
        sessions: list[VSCodeClaudeSession] = [
            {
                "folder": str(tmp_path / "session_0"),
                "repo": "owner/repo",
                "issue_number": 100,
                "status": "status-07:code-review",
                "vscode_pid": 1000,
                "vscode_pid_create_time": None,
                "last_active": None,
                "last_active_rule": None,
                "started_at": "2024-01-01T00:00:00Z",
                "is_intervention": False,
            }
        ]
        assessments = {s["folder"]: _make_assessment(s["folder"]) for s in sessions}

        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.commands.load_sessions",
            lambda: {"sessions": sessions, "last_updated": ""},
        )
        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.commands.load_config",
            lambda: {"coordinator": {"repos": {"myrepo": {}}}},
        )
        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.commands.load_vscodeclaude_config",
            lambda: {"workspace_base": str(tmp_path), "max_sessions": 3},
        )
        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.commands._build_cached_issues_by_repo",
            lambda repo_names, sessions=None: ({}, set()),
        )
        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.commands.build_assessments",
            lambda sess, cached=None: assessments,
        )

        # Sentinels for the write surfaces — must never fire under --explain.
        save_mock = Mock()
        append_mock = Mock()
        apply_mock = Mock()
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.save_sessions", save_mock
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.audit.append_run", append_mock
        )
        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.commands.apply_assessments", apply_mock
        )

        # The status table / branch-check path must be skipped entirely.
        display_mock = Mock()
        branch_check_mock = Mock(return_value=([], set()))
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.status.display_status_table", display_mock
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.issues.build_eligible_issues_with_branch_check",
            branch_check_mock,
        )

        args = argparse.Namespace(repo=None, explain=True)
        result = execute_coordinator_vscodeclaude_status(args)

        assert result == 0
        save_mock.assert_not_called()
        append_mock.assert_not_called()
        apply_mock.assert_not_called()
        display_mock.assert_not_called()
        branch_check_mock.assert_not_called()

    def test_status_without_explain_renders_table(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Without --explain the normal status table path runs (unchanged)."""
        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.commands.load_sessions",
            lambda: {"sessions": [], "last_updated": ""},
        )
        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.commands.load_config",
            lambda: {"coordinator": {"repos": {}}},
        )
        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.commands.load_vscodeclaude_config",
            lambda: {"workspace_base": str(tmp_path), "max_sessions": 3},
        )
        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.commands._build_cached_issues_by_repo",
            lambda repo_names, sessions=None: ({}, set()),
        )
        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.commands.build_assessments",
            lambda sess, cached=None: {},
        )

        display_mock = Mock()
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.status.display_status_table", display_mock
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.issues.build_eligible_issues_with_branch_check",
            lambda repo_names, cached_issues_by_repo=None: ([], set()),
        )

        args = argparse.Namespace(repo=None, explain=False)
        result = execute_coordinator_vscodeclaude_status(args)

        assert result == 0
        display_mock.assert_called_once()
