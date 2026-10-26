import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from mcp_coder.workflows.vscodeclaude.sessions import (
    check_vscode_running,
    load_sessions,
    update_session_pid,
)


class TestCreateTimeIdentityVerification:
    """Tests for create_time-based PID identity verification.

    Closes the PID-reuse hole where an unrelated live process with the same
    PID as a dead VSCode would falsely pin a session as active.
    """

    def test_load_sessions_backfills_missing_create_time(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Old payload without vscode_pid_create_time gets backfilled with None."""
        sessions_file = tmp_path / "sessions.json"
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.get_sessions_file_path",
            lambda: sessions_file,
        )
        # Write a payload missing the vscode_pid_create_time key
        legacy_payload = {
            "sessions": [
                {
                    "folder": "/legacy/folder",
                    "repo": "owner/repo",
                    "issue_number": 7,
                    "status": "status-01:created",
                    "vscode_pid": 1234,
                    "started_at": "2024-01-01T00:00:00Z",
                    "is_intervention": False,
                }
            ],
            "last_updated": "2024-01-01T00:00:00Z",
        }
        sessions_file.write_text(json.dumps(legacy_payload))

        store = load_sessions()

        assert len(store["sessions"]) == 1
        session = store["sessions"][0]
        assert "vscode_pid_create_time" in session
        assert session["vscode_pid_create_time"] is None

    def test_load_sessions_backfills_missing_last_active(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Old payload without last_active/last_active_rule gets backfilled None."""
        sessions_file = tmp_path / "sessions.json"
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.get_sessions_file_path",
            lambda: sessions_file,
        )
        legacy_payload = {
            "sessions": [
                {
                    "folder": "/legacy/folder",
                    "repo": "owner/repo",
                    "issue_number": 7,
                    "status": "status-01:created",
                    "vscode_pid": 1234,
                    "vscode_pid_create_time": None,
                    "started_at": "2024-01-01T00:00:00Z",
                    "is_intervention": False,
                }
            ],
            "last_updated": "2024-01-01T00:00:00Z",
        }
        sessions_file.write_text(json.dumps(legacy_payload))

        store = load_sessions()

        assert len(store["sessions"]) == 1
        session = store["sessions"][0]
        assert "last_active" in session
        assert session["last_active"] is None
        assert "last_active_rule" in session
        assert session["last_active_rule"] is None

    def test_check_vscode_running_create_time_mismatch_returns_false(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """create_time mismatch beyond tolerance -> False (PID-reuse case)."""
        mock_process = MagicMock()
        mock_process.name.return_value = "code.exe"
        mock_process.create_time.return_value = 2000.0

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.psutil.pid_exists",
            lambda pid: True,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.psutil.Process",
            lambda pid: mock_process,
        )

        assert check_vscode_running(12345, 1000.0) is False

    def test_check_vscode_running_create_time_match_within_tolerance(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """create_time within 1.0s tolerance -> True."""
        mock_process = MagicMock()
        mock_process.name.return_value = "code.exe"
        mock_process.create_time.return_value = 1000.5

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.psutil.pid_exists",
            lambda pid: True,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.psutil.Process",
            lambda pid: mock_process,
        )

        assert check_vscode_running(12345, 1000.0) is True

    def test_update_session_pid_writes_both_fields_atomically(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """update_session_pid persists vscode_pid AND vscode_pid_create_time together."""
        sessions_file = tmp_path / "sessions.json"
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.get_sessions_file_path",
            lambda: sessions_file,
        )

        session = {
            "folder": "/test/folder",
            "repo": "owner/repo",
            "issue_number": 123,
            "status": "status-07:code-review",
            "vscode_pid": 100,
            "vscode_pid_create_time": 500.0,
            "started_at": "2024-01-22T10:30:00Z",
            "is_intervention": False,
        }
        store = {"sessions": [session], "last_updated": "2024-01-22T10:30:00Z"}
        sessions_file.write_text(json.dumps(store))

        mock_process = MagicMock()
        mock_process.create_time.return_value = 999.0
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.psutil.Process",
            lambda pid: mock_process,
        )

        update_session_pid("/test/folder", 200)

        reloaded = load_sessions()
        assert reloaded["sessions"][0]["vscode_pid"] == 200
        assert reloaded["sessions"][0]["vscode_pid_create_time"] == 999.0

    def test_update_session_pid_dead_pid_stores_none_create_time(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """psutil.NoSuchProcess -> vscode_pid_create_time stored as None."""
        import psutil

        sessions_file = tmp_path / "sessions.json"
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.get_sessions_file_path",
            lambda: sessions_file,
        )

        session = {
            "folder": "/test/folder",
            "repo": "owner/repo",
            "issue_number": 123,
            "status": "status-07:code-review",
            "vscode_pid": 100,
            "vscode_pid_create_time": 500.0,
            "started_at": "2024-01-22T10:30:00Z",
            "is_intervention": False,
        }
        store = {"sessions": [session], "last_updated": "2024-01-22T10:30:00Z"}
        sessions_file.write_text(json.dumps(store))

        def raise_no_such(pid: int) -> MagicMock:
            raise psutil.NoSuchProcess(pid)

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.psutil.Process",
            raise_no_such,
        )

        update_session_pid("/test/folder", 200)

        reloaded = load_sessions()
        assert reloaded["sessions"][0]["vscode_pid"] == 200
        assert reloaded["sessions"][0]["vscode_pid_create_time"] is None

    def test_build_session_defaults_create_time_to_none(self) -> None:
        """build_session always sets vscode_pid_create_time to None."""
        from mcp_coder.workflows.vscodeclaude.helpers import build_session

        session = build_session(
            folder="/test/folder",
            repo="owner/repo",
            issue_number=42,
            status="status-01:created",
            vscode_pid=1234,
            is_intervention=False,
        )

        assert session["vscode_pid_create_time"] is None
        assert session["last_active"] is None
        assert session["last_active_rule"] is None
