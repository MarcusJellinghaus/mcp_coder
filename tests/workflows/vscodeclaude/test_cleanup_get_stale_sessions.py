from pathlib import Path

import pytest

from mcp_coder.workflows.vscodeclaude.cleanup import get_stale_sessions
from mcp_coder.workflows.vscodeclaude.types import SessionAction
from tests.workflows.vscodeclaude.test_cleanup import (
    _assessment,
    _patch_sessions_file,
    _session,
)


class TestGetStaleSessions:
    """Thin filter over assessments: which sessions does cleanup act on?"""

    def test_returns_inactive_actionable_sessions(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Inactive DELETE session is returned with its assessment."""
        folder = tmp_path / "stale_folder"
        folder.mkdir()
        session = _session(folder)
        sessions_file = tmp_path / "sessions.json"
        _patch_sessions_file(monkeypatch, sessions_file, [session])

        assessment = _assessment(folder, action=SessionAction.DELETE)
        result = get_stale_sessions({str(folder): assessment})

        assert len(result) == 1
        returned_session, returned_assessment = result[0]
        assert returned_session["folder"] == str(folder)
        assert returned_assessment.decision.action == SessionAction.DELETE

    def test_skips_active_sessions(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """KEEP_ACTIVE (verdict.active) sessions are skipped — they stay tracked."""
        folder = tmp_path / "active_folder"
        folder.mkdir()
        session = _session(folder)
        sessions_file = tmp_path / "sessions.json"
        _patch_sessions_file(monkeypatch, sessions_file, [session])

        assessment = _assessment(
            folder, active=True, action=SessionAction.KEEP_ACTIVE, reason="active"
        )
        result = get_stale_sessions({str(folder): assessment})

        assert result == []

    def test_skips_zombie_sessions(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """INVESTIGATE_ZOMBIE is active (process alive, folder gone) -> skipped."""
        folder = tmp_path / "zombie_folder"  # not created (folder gone)
        session = _session(folder)
        sessions_file = tmp_path / "sessions.json"
        _patch_sessions_file(monkeypatch, sessions_file, [session])

        assessment = _assessment(
            folder,
            active=True,
            action=SessionAction.INVESTIGATE_ZOMBIE,
            reason="folder missing, process alive",
        )
        result = get_stale_sessions({str(folder): assessment})

        assert result == []

    def test_skips_restart_sessions(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """RESTART is the restart path's job — cleanup ignores it."""
        folder = tmp_path / "restart_folder"
        folder.mkdir()
        session = _session(folder)
        sessions_file = tmp_path / "sessions.json"
        _patch_sessions_file(monkeypatch, sessions_file, [session])

        assessment = _assessment(
            folder, action=SessionAction.RESTART, reason="restartable"
        )
        result = get_stale_sessions({str(folder): assessment})

        assert result == []

    def test_skips_sessions_without_assessment(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A session with no assessment entry is left untouched."""
        folder = tmp_path / "unassessed_folder"
        folder.mkdir()
        session = _session(folder)
        sessions_file = tmp_path / "sessions.json"
        _patch_sessions_file(monkeypatch, sessions_file, [session])

        result = get_stale_sessions({})

        assert result == []

    def test_returns_skip_and_remove_missing(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """SKIP and REMOVE_MISSING are actionable and returned."""
        skip_folder = tmp_path / "skip_folder"
        skip_folder.mkdir()
        missing_folder = tmp_path / "missing_folder"
        skip_session = _session(skip_folder, issue_number=1)
        missing_session = _session(missing_folder, issue_number=2)
        sessions_file = tmp_path / "sessions.json"
        _patch_sessions_file(
            monkeypatch, sessions_file, [skip_session, missing_session]
        )

        assessments = {
            str(skip_folder): _assessment(
                skip_folder, action=SessionAction.SKIP, reason="dirty"
            ),
            str(missing_folder): _assessment(
                missing_folder, action=SessionAction.REMOVE_MISSING
            ),
        }
        result = get_stale_sessions(assessments)

        returned_actions = {a.decision.action for _, a in result}
        assert returned_actions == {SessionAction.SKIP, SessionAction.REMOVE_MISSING}
