"""Tests for status rendering of prebuilt session assessments."""

import json
from pathlib import Path
from unittest.mock import Mock

import pytest

from mcp_coder.workflows.vscodeclaude.status import (
    display_status_table,
)
from mcp_coder.workflows.vscodeclaude.types import (
    SessionAction,
    VSCodeClaudeSession,
)
from tests.workflows.vscodeclaude.conftest import _build_assessment


class TestStatusAssessmentConsumer:
    """Status renders the prebuilt assessment (enriched columns, write-free).

    These tests exercise the Step 8 migration directly: the ``VSCode``/``Next
    Action`` columns are derived from the embedded ``verdict``/``decision`` and
    nothing on the status path writes ``sessions.json``.
    """

    def _session(self, folder: Path) -> VSCodeClaudeSession:
        return {
            "folder": str(folder),
            "repo": "owner/repo",
            "issue_number": 321,
            "status": "status-07:code-review",
            "vscode_pid": None,
            "vscode_pid_create_time": None,
            "last_active": None,
            "last_active_rule": None,
            "started_at": "2024-01-01T00:00:00Z",
            "is_intervention": False,
        }

    def test_vscode_column_enriched_with_running_title(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Active session (rule=TITLE) renders ``Running (title)``."""
        folder = tmp_path / "live"
        folder.mkdir()
        session = self._session(folder)

        display_status_table(
            sessions=[session],
            eligible_issues=[],
            workspace_base=str(tmp_path),
            assessments={
                session["folder"]: _build_assessment(session, is_running=True)
            },
            repo_filter=None,
        )

        captured = capsys.readouterr()
        assert "Running (title)" in captured.out

    def test_vscode_column_enriched_with_closed_no_match(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Inactive session with no detection match renders ``Closed (no_match)``."""
        folder = tmp_path / "idle"
        folder.mkdir()
        session = self._session(folder)

        display_status_table(
            sessions=[session],
            eligible_issues=[],
            workspace_base=str(tmp_path),
            assessments={session["folder"]: _build_assessment(session)},
            repo_filter=None,
        )

        captured = capsys.readouterr()
        assert "Closed (no_match)" in captured.out

    def test_status_path_performs_no_disk_writes(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Rendering the table never writes the session store (R2)."""
        save_mock = Mock()
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.save_sessions", save_mock
        )

        folder = tmp_path / "live"
        folder.mkdir()
        session = self._session(folder)
        # An active session would trigger a PID refresh on the apply path; the
        # status path must still leave the store untouched.
        display_status_table(
            sessions=[session],
            eligible_issues=[],
            workspace_base=str(tmp_path),
            assessments={
                session["folder"]: _build_assessment(session, is_running=True)
            },
            repo_filter=None,
        )

        capsys.readouterr()
        save_mock.assert_not_called()

    def test_status_and_cleanup_agree_on_same_assessment(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """One assessment object drives both status and cleanup identically.

        The SAME ``SessionAssessment`` (action=DELETE) is handed to both
        consumers: status renders the Delete label and cleanup's dry-run reports
        the same delete. Neither recomputes the decision, so they cannot drift.
        """
        from mcp_coder.workflows.vscodeclaude.cleanup import cleanup_stale_sessions

        sessions_file = tmp_path / "sessions.json"
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.get_sessions_file_path",
            lambda: sessions_file,
        )

        folder = tmp_path / "stale"
        folder.mkdir()
        session = self._session(folder)
        sessions_file.write_text(
            json.dumps({"sessions": [session], "last_updated": "2024-01-01T00:00:00Z"})
        )

        # Closed + clean folder -> a single shared DELETE assessment.
        assessment = _build_assessment(session, is_closed=True)
        assert assessment.decision.action is SessionAction.DELETE
        assessments = {session["folder"]: assessment}

        # Status consumer.
        display_status_table(
            sessions=[session],
            eligible_issues=[],
            workspace_base=str(tmp_path),
            assessments=assessments,
            repo_filter=None,
        )
        status_out = capsys.readouterr().out
        assert "-> Delete (with --cleanup)" in status_out

        # Cleanup consumer reading the SAME assessment object.
        result = cleanup_stale_sessions(
            workspace_base=str(tmp_path),
            assessments=assessments,
            dry_run=True,
        )
        cleanup_out = capsys.readouterr().out
        assert "Add --cleanup to delete" in cleanup_out
        assert result["deleted"] == []
