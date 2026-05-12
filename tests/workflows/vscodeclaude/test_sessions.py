"""Test session management functions for VSCode Claude."""

import json
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.workflows.vscodeclaude.sessions import (
    VSCODE_PROCESS_NAMES,
    _get_vscode_processes,
    add_session,
    build_active_session_set,
    check_vscode_running,
    clear_vscode_process_cache,
    get_session_for_issue,
    get_sessions_file_path,
    is_session_active,
    is_vscode_window_open_for_folder,
    load_sessions,
    remove_session,
    save_sessions,
    session_has_artifacts,
    update_session_pid,
    update_session_status,
    warn_orphan_folders,
)
from mcp_coder.workflows.vscodeclaude.types import (
    VSCodeClaudeSession,
    VSCodeClaudeSessionStore,
)


class TestSessionManagement:
    """Test session load/save/check functions."""

    def test_get_sessions_file_path(self) -> None:
        """Sessions file is in .mcp_coder on all platforms."""
        path = get_sessions_file_path()
        assert ".mcp_coder" in str(path)
        assert "vscodeclaude_sessions.json" in str(path)

    def test_load_sessions_empty_when_no_file(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Returns empty store when file doesn't exist."""
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.get_sessions_file_path",
            lambda: tmp_path / "nonexistent.json",
        )
        store = load_sessions()
        assert store["sessions"] == []

    def test_save_and_load_roundtrip(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Sessions survive save/load cycle."""
        sessions_file = tmp_path / "sessions.json"
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.get_sessions_file_path",
            lambda: sessions_file,
        )

        session: VSCodeClaudeSession = {
            "folder": str(tmp_path / "test_123"),
            "repo": "owner/repo",
            "issue_number": 123,
            "status": "status-07:code-review",
            "vscode_pid": 1234,
            "vscode_pid_create_time": None,
            "started_at": "2024-01-22T10:30:00Z",
            "is_intervention": False,
        }

        store: VSCodeClaudeSessionStore = {
            "sessions": [session],
            "last_updated": "2024-01-22T10:30:00Z",
        }

        save_sessions(store)
        loaded = load_sessions()

        assert len(loaded["sessions"]) == 1
        assert loaded["sessions"][0]["issue_number"] == 123

    def test_check_vscode_running_none_pid(self) -> None:
        """None PID returns False."""
        assert check_vscode_running(None, None) is False

    def test_check_vscode_running_nonexistent_pid(self) -> None:
        """Nonexistent PID returns False."""
        # Use a PID that almost certainly doesn't exist
        assert check_vscode_running(999999999, None) is False

    def test_get_session_for_issue_found(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Finds session by repo and issue number."""
        # Setup session store with test data
        sessions_file = tmp_path / "sessions.json"
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.get_sessions_file_path",
            lambda: sessions_file,
        )

        session = {
            "folder": str(tmp_path / "test_folder"),
            "repo": "owner/repo",
            "issue_number": 123,
            "status": "status-07:code-review",
            "vscode_pid": None,
            "started_at": "2024-01-22T10:30:00Z",
            "is_intervention": False,
        }
        store = {"sessions": [session], "last_updated": "2024-01-22T10:30:00Z"}
        sessions_file.write_text(json.dumps(store))

        found = get_session_for_issue("owner/repo", 123, str(tmp_path))
        assert found is not None
        assert found["issue_number"] == 123  # pylint: disable=unsubscriptable-object

    def test_get_session_for_issue_not_found(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Returns None when no matching session."""
        sessions_file = tmp_path / "sessions.json"
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.get_sessions_file_path",
            lambda: sessions_file,
        )
        store = {"sessions": [], "last_updated": "2024-01-22T10:30:00Z"}
        sessions_file.write_text(json.dumps(store))

        found = get_session_for_issue("owner/repo", 999, str(tmp_path))
        assert found is None

    def test_add_session(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Adds session to store."""
        sessions_file = tmp_path / "sessions.json"
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.get_sessions_file_path",
            lambda: sessions_file,
        )

        session: VSCodeClaudeSession = {
            "folder": "/test/folder",
            "repo": "owner/repo",
            "issue_number": 456,
            "status": "status-04:plan-review",
            "vscode_pid": 5678,
            "vscode_pid_create_time": None,
            "started_at": "2024-01-22T11:00:00Z",
            "is_intervention": False,
        }

        add_session(session)

        loaded = load_sessions()
        assert len(loaded["sessions"]) == 1
        assert loaded["sessions"][0]["issue_number"] == 456

    def test_remove_session(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Removes session by folder path."""
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
            "vscode_pid": None,
            "started_at": "2024-01-22T10:30:00Z",
            "is_intervention": False,
        }
        store = {"sessions": [session], "last_updated": "2024-01-22T10:30:00Z"}
        sessions_file.write_text(json.dumps(store))

        result = remove_session("/test/folder")
        assert result is True

        loaded = load_sessions()
        assert len(loaded["sessions"]) == 0

    def test_remove_session_not_found(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Remove returns False when session not found."""
        sessions_file = tmp_path / "sessions.json"
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.get_sessions_file_path",
            lambda: sessions_file,
        )
        store = {"sessions": [], "last_updated": "2024-01-22T10:30:00Z"}
        sessions_file.write_text(json.dumps(store))

        result = remove_session("/nonexistent/folder")
        assert result is False

    def test_build_active_session_set(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Builds snapshot dict, calls is_session_active once per session, refreshes stale PID."""
        sessions_file = tmp_path / "sessions.json"
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.get_sessions_file_path",
            lambda: sessions_file,
        )

        # Track calls to is_session_active
        active_calls: list[str] = []

        def mock_is_session_active(session: VSCodeClaudeSession) -> bool:
            active_calls.append(session["folder"])
            # session_a (folder_a) is active, session_b is inactive
            return session["folder"] == str(tmp_path / "session_a")

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.is_session_active",
            mock_is_session_active,
        )

        # Track calls to is_vscode_open_for_folder for active sessions
        # Return a different PID than stored to trigger update_session_pid
        def mock_is_vscode_open_for_folder(folder: str) -> tuple[bool, int | None]:
            return True, 5555  # Different from stored 1111

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.is_vscode_open_for_folder",
            mock_is_vscode_open_for_folder,
        )

        # Track update_session_pid calls
        pid_updates: list[tuple[str, int]] = []

        def mock_update_session_pid(folder: str, pid: int) -> None:
            pid_updates.append((folder, pid))

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.update_session_pid",
            mock_update_session_pid,
        )

        # Persist a sessions store so update_session_pid would work if called
        store = {
            "sessions": [
                {
                    "folder": str(tmp_path / "session_a"),
                    "repo": "o/r",
                    "issue_number": 1,
                    "status": "s",
                    "vscode_pid": 1111,
                    "started_at": "2024-01-01T00:00:00Z",
                    "is_intervention": False,
                },
                {
                    "folder": str(tmp_path / "session_b"),
                    "repo": "o/r",
                    "issue_number": 2,
                    "status": "s",
                    "vscode_pid": 2222,
                    "started_at": "2024-01-01T00:00:00Z",
                    "is_intervention": False,
                },
            ],
            "last_updated": "2024-01-01T00:00:00Z",
        }
        sessions_file.write_text(json.dumps(store))

        sessions: list[VSCodeClaudeSession] = list(store["sessions"])  # type: ignore[arg-type]

        result = build_active_session_set(sessions)

        # Snapshot has one entry per session, keyed by folder
        assert set(result.keys()) == {
            str(tmp_path / "session_a"),
            str(tmp_path / "session_b"),
        }
        assert result[str(tmp_path / "session_a")] is True
        assert result[str(tmp_path / "session_b")] is False

        # is_session_active called exactly once per session
        assert len(active_calls) == 2

        # update_session_pid called only for the active session whose stored PID
        # differs from the detected PID
        assert pid_updates == [(str(tmp_path / "session_a"), 5555)]

    def test_update_session_pid(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Updates VSCode PID for existing session."""
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
            "vscode_pid": None,
            "started_at": "2024-01-22T10:30:00Z",
            "is_intervention": False,
        }
        store = {"sessions": [session], "last_updated": "2024-01-22T10:30:00Z"}
        sessions_file.write_text(json.dumps(store))

        update_session_pid("/test/folder", 9999)

        loaded = load_sessions()
        assert loaded["sessions"][0]["vscode_pid"] == 9999

    def test_load_sessions_with_invalid_json(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Returns empty store when JSON is invalid."""
        sessions_file = tmp_path / "sessions.json"
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.get_sessions_file_path",
            lambda: sessions_file,
        )
        sessions_file.write_text("not valid json")

        store = load_sessions()
        assert store["sessions"] == []

    def test_load_sessions_with_missing_fields(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Returns store with default fields when JSON is partial."""
        sessions_file = tmp_path / "sessions.json"
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.get_sessions_file_path",
            lambda: sessions_file,
        )
        sessions_file.write_text(json.dumps({}))

        store = load_sessions()
        assert store["sessions"] == []
        assert store["last_updated"] == ""

    def test_save_sessions_creates_directories(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Save creates parent directories if they don't exist."""
        sessions_file = tmp_path / "nested" / "dirs" / "sessions.json"
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.get_sessions_file_path",
            lambda: sessions_file,
        )

        store: VSCodeClaudeSessionStore = {
            "sessions": [],
            "last_updated": "2024-01-22T10:30:00Z",
        }
        save_sessions(store)

        assert sessions_file.exists()
        loaded = json.loads(sessions_file.read_text(encoding="utf-8"))
        assert "sessions" in loaded


class TestSessionHasArtifacts:
    """Tests for session_has_artifacts function."""

    def test_returns_true_when_folder_exists(self, tmp_path: Path) -> None:
        """Returns True when the session folder exists."""
        folder = tmp_path / "mcp_coder_123"
        folder.mkdir()
        assert session_has_artifacts(str(folder)) is True

    def test_returns_false_when_only_workspace_file_exists(
        self, tmp_path: Path
    ) -> None:
        """Returns False when folder is gone but workspace file lingers (orphan).

        The workspace file is a launcher pointing at the folder; without the
        folder it points at nothing. Treating the orphan as a live artifact
        was the bug that produced false-active sessions and blocked cleanup.
        """
        folder = tmp_path / "mcp_coder_123"
        # Don't create the folder, but create the workspace file
        workspace = tmp_path / "mcp_coder_123.code-workspace"
        workspace.write_text("{}")
        assert session_has_artifacts(str(folder)) is False

    def test_returns_false_when_neither_exists(self, tmp_path: Path) -> None:
        """Returns False when neither folder nor workspace file exists (zombie session)."""
        folder = tmp_path / "mcp_coder_123"
        # Neither folder nor workspace file created
        assert session_has_artifacts(str(folder)) is False

    def test_returns_true_when_both_exist(self, tmp_path: Path) -> None:
        """Returns True when both folder and workspace file exist."""
        folder = tmp_path / "mcp_coder_123"
        folder.mkdir()
        workspace = tmp_path / "mcp_coder_123.code-workspace"
        workspace.write_text("{}")
        assert session_has_artifacts(str(folder)) is True


class TestUpdateSessionStatus:
    """Tests for update_session_status function."""

    def test_updates_existing_session_status(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should update status for existing session."""
        # Setup: Create session store with one session
        sessions_file = tmp_path / "sessions.json"
        initial_store = {
            "sessions": [
                {
                    "folder": "/workspace/repo_123",
                    "repo": "owner/repo",
                    "issue_number": 123,
                    "status": "status-01:created",
                    "vscode_pid": 1234,
                    "started_at": "2024-01-01T00:00:00Z",
                    "is_intervention": False,
                }
            ],
            "last_updated": "",
        }
        sessions_file.write_text(json.dumps(initial_store))

        # Patch get_sessions_file_path to use tmp_path
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.get_sessions_file_path",
            lambda: sessions_file,
        )

        # Act
        result = update_session_status("/workspace/repo_123", "status-04:plan-review")

        # Assert
        assert result is True
        updated_store = json.loads(sessions_file.read_text())
        assert updated_store["sessions"][0]["status"] == "status-04:plan-review"

    def test_returns_false_for_nonexistent_session(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should return False when session not found."""
        sessions_file = tmp_path / "sessions.json"
        initial_store = {"sessions": [], "last_updated": ""}
        sessions_file.write_text(json.dumps(initial_store))

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.get_sessions_file_path",
            lambda: sessions_file,
        )

        result = update_session_status("/nonexistent/path", "status-04:plan-review")

        assert result is False

    def test_does_not_modify_other_sessions(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should only update the matching session."""
        sessions_file = tmp_path / "sessions.json"
        initial_store = {
            "sessions": [
                {
                    "folder": "/workspace/repo_123",
                    "repo": "owner/repo",
                    "issue_number": 123,
                    "status": "status-01:created",
                    "vscode_pid": 1234,
                    "started_at": "2024-01-01T00:00:00Z",
                    "is_intervention": False,
                },
                {
                    "folder": "/workspace/repo_456",
                    "repo": "owner/repo",
                    "issue_number": 456,
                    "status": "status-01:created",
                    "vscode_pid": 5678,
                    "started_at": "2024-01-01T00:00:00Z",
                    "is_intervention": False,
                },
            ],
            "last_updated": "",
        }
        sessions_file.write_text(json.dumps(initial_store))

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.get_sessions_file_path",
            lambda: sessions_file,
        )

        update_session_status("/workspace/repo_123", "status-04:plan-review")

        updated_store = json.loads(sessions_file.read_text())
        # First session updated
        assert updated_store["sessions"][0]["status"] == "status-04:plan-review"
        # Second session unchanged
        assert updated_store["sessions"][1]["status"] == "status-01:created"

    def test_updates_last_updated_timestamp(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should update the last_updated timestamp."""
        sessions_file = tmp_path / "sessions.json"
        initial_store = {
            "sessions": [
                {
                    "folder": "/workspace/repo_123",
                    "repo": "owner/repo",
                    "issue_number": 123,
                    "status": "status-01:created",
                    "vscode_pid": 1234,
                    "started_at": "2024-01-01T00:00:00Z",
                    "is_intervention": False,
                }
            ],
            "last_updated": "old-timestamp",
        }
        sessions_file.write_text(json.dumps(initial_store))

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.get_sessions_file_path",
            lambda: sessions_file,
        )

        update_session_status("/workspace/repo_123", "status-04:plan-review")

        updated_store = json.loads(sessions_file.read_text())
        assert updated_store["last_updated"] != "old-timestamp"


class TestVSCodeProcessNameMatching:
    """Tests that VSCode process detection uses exact name matching.

    Regression tests for the bug where VSCODE_PROCESS_NAME was a substring
    ("code"), causing processes like my-code-tool.exe to be mistakenly
    identified as VSCode and stored as session PIDs.
    """

    def test_vscode_process_names_contains_expected_values(self) -> None:
        """VSCODE_PROCESS_NAMES includes code.exe and code."""
        assert "code.exe" in VSCODE_PROCESS_NAMES
        assert "code" in VSCODE_PROCESS_NAMES

    def test_vscode_process_names_excludes_code_substring(self) -> None:
        """Process names containing 'code' as substring are not in VSCODE_PROCESS_NAMES."""
        assert "my-code-tool.exe" not in VSCODE_PROCESS_NAMES

    def test_check_vscode_running_rejects_code_substring(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """check_vscode_running returns False for processes with 'code' substring."""
        mock_process = MagicMock()
        mock_process.name.return_value = "my-code-tool.exe"

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.psutil.pid_exists",
            lambda pid: True,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.psutil.Process",
            lambda pid: mock_process,
        )

        assert check_vscode_running(12345, None) is False

    def test_check_vscode_running_accepts_code_exe(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """check_vscode_running returns True for Code.exe PIDs."""
        mock_process = MagicMock()
        mock_process.name.return_value = "Code.exe"

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.psutil.pid_exists",
            lambda pid: True,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.psutil.Process",
            lambda pid: mock_process,
        )

        assert check_vscode_running(12345, None) is True

    def test_check_vscode_running_accepts_code_linux(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """check_vscode_running returns True for 'code' (Linux/macOS process name)."""
        mock_process = MagicMock()
        mock_process.name.return_value = "code"

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.psutil.pid_exists",
            lambda pid: True,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.psutil.Process",
            lambda pid: mock_process,
        )

        assert check_vscode_running(12345, None) is True

    def test_get_vscode_processes_excludes_code_substring(self) -> None:
        """_get_vscode_processes does not include processes with 'code' substring."""
        # Build mock process entries: one real VSCode, one with 'code' substring
        mock_vscode = MagicMock()
        mock_vscode.info = {
            "pid": 1001,
            "name": "Code.exe",
            "cmdline": [
                r"C:\Program Files\VSCode\Code.exe",
                "workspace.code-workspace",
            ],
        }
        mock_checker = MagicMock()
        mock_checker.info = {
            "pid": 2002,
            "name": "my-code-tool.exe",
            "cmdline": [r"C:\tools\my-code-tool.exe", "--project", "my_repo_42"],
        }

        clear_vscode_process_cache()
        with patch(
            "mcp_coder.workflows.vscodeclaude.sessions.psutil.process_iter",
            return_value=[mock_vscode, mock_checker],
        ):
            processes = _get_vscode_processes(refresh=True)

        pids = [p["pid"] for p in processes]
        assert 1001 in pids  # real VSCode included
        assert 2002 not in pids  # 'code' substring process excluded

    def test_get_vscode_processes_excludes_code_insiders(
        self,
    ) -> None:
        """_get_vscode_processes does not include Code - Insiders.exe processes."""
        mock_insiders = MagicMock()
        mock_insiders.info = {
            "pid": 3003,
            "name": "Code - Insiders.exe",
            "cmdline": [r"C:\Program Files\VSCode Insiders\Code - Insiders.exe"],
        }

        clear_vscode_process_cache()
        with patch(
            "mcp_coder.workflows.vscodeclaude.sessions.psutil.process_iter",
            return_value=[mock_insiders],
        ):
            processes = _get_vscode_processes(refresh=True)

        assert all(p["pid"] != 3003 for p in processes)


class TestWindowTitleMatching:
    """Tests for is_vscode_window_open_for_folder function.

    These tests verify that window title matching correctly identifies
    workspace windows while avoiding false positives from main repo windows.
    """

    def test_matches_window_with_issue_number_and_repo(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should match window with issue number pattern and repo name."""
        # Mock window titles to return a workspace window owned by pid=100
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions._get_vscode_window_titles",
            lambda: [
                (100, "[#219 plan-review] Fix bug - mcp_coder - Visual Studio Code")
            ],
        )
        # That pid's cmdline references the folder so the title is bound to it
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions._get_vscode_processes",
            lambda: [
                {"pid": 100, "cmdline_lower": "code.exe /workspace/mcp_coder_219"}
            ],
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.HAS_WIN32GUI",
            True,
        )

        result = is_vscode_window_open_for_folder(
            folder_path="/workspace/mcp_coder_219",
            issue_number=219,
            repo="MarcusJellinghaus/mcp_coder",
        )

        assert result is True

    def test_does_not_match_main_repo_window(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should NOT match main repo window without issue number pattern."""
        # Mock window titles to return only main repo window (no issue number)
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions._get_vscode_window_titles",
            lambda: [(100, "mcp_coder - Visual Studio Code")],
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions._get_vscode_processes",
            lambda: [
                {"pid": 100, "cmdline_lower": "code.exe /workspace/mcp_coder_219"}
            ],
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.HAS_WIN32GUI",
            True,
        )

        result = is_vscode_window_open_for_folder(
            folder_path="/workspace/mcp_coder_219",
            issue_number=219,
            repo="MarcusJellinghaus/mcp_coder",
        )

        # This is the key test - should be False to avoid false positive
        assert result is False

    def test_does_not_match_different_issue_number(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should NOT match window for a different issue."""
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions._get_vscode_window_titles",
            lambda: [
                (100, "[#123 code-review] Other issue - mcp_coder - Visual Studio Code")
            ],
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions._get_vscode_processes",
            lambda: [
                {"pid": 100, "cmdline_lower": "code.exe /workspace/mcp_coder_219"}
            ],
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.HAS_WIN32GUI",
            True,
        )

        result = is_vscode_window_open_for_folder(
            folder_path="/workspace/mcp_coder_219",
            issue_number=219,
            repo="MarcusJellinghaus/mcp_coder",
        )

        assert result is False

    def test_matches_with_different_repo_format(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should extract repo name from owner/repo format."""
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions._get_vscode_window_titles",
            lambda: [(100, "[#219 created] New issue - my_repo - Visual Studio Code")],
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions._get_vscode_processes",
            lambda: [{"pid": 100, "cmdline_lower": "code.exe /workspace/my_repo_219"}],
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.HAS_WIN32GUI",
            True,
        )

        result = is_vscode_window_open_for_folder(
            folder_path="/workspace/my_repo_219",
            issue_number=219,
            repo="owner/my_repo",
        )

        assert result is True

    def test_case_insensitive_matching(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should match case-insensitively."""
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions._get_vscode_window_titles",
            lambda: [(100, "[#219 review] Title - MCP_CODER - Visual Studio Code")],
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions._get_vscode_processes",
            lambda: [
                {"pid": 100, "cmdline_lower": "code.exe /workspace/mcp_coder_219"}
            ],
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.HAS_WIN32GUI",
            True,
        )

        result = is_vscode_window_open_for_folder(
            folder_path="/workspace/mcp_coder_219",
            issue_number=219,
            repo="owner/mcp_coder",
        )

        assert result is True

    def test_returns_false_when_no_windows_open(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should return False when no VSCode windows exist."""
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions._get_vscode_window_titles",
            lambda: [],
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions._get_vscode_processes",
            lambda: [],
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.HAS_WIN32GUI",
            True,
        )

        result = is_vscode_window_open_for_folder(
            folder_path="/workspace/mcp_coder_219",
            issue_number=219,
            repo="owner/mcp_coder",
        )

        assert result is False

    def test_cross_process_title_leak_rejected(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Title from a VSCode that does not have the folder open -> False.

        Regression for the #946/#950 cross-process leak: two VSCode windows
        are open. Process A (pid=100) has folder mcp_coder_950 open and its
        title accidentally contains "[#946 ...]" (e.g. the user was browsing
        issue #946). Process B (pid=200) has folder mcp_coder_946 open but
        its current title does not match. A lookup for folder
        mcp_coder_946 must NOT match A's title.
        """
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions._get_vscode_processes",
            lambda: [
                {"pid": 100, "cmdline_lower": "code.exe /tmp/mcp_coder_950"},
                {"pid": 200, "cmdline_lower": "code.exe /tmp/mcp_coder_946"},
            ],
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions._get_vscode_window_titles",
            lambda: [(100, "[#946 stuff] - mcp_coder")],
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.HAS_WIN32GUI",
            True,
        )

        result = is_vscode_window_open_for_folder(
            folder_path="/tmp/mcp_coder_946",
            issue_number=946,
            repo="owner/mcp_coder",
        )

        assert result is False

    def test_positive_match_preserved_when_pid_matches(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Same scenario but matching window is on the PID that owns the folder."""
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions._get_vscode_processes",
            lambda: [
                {"pid": 100, "cmdline_lower": "code.exe /tmp/mcp_coder_950"},
                {"pid": 200, "cmdline_lower": "code.exe /tmp/mcp_coder_946"},
            ],
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions._get_vscode_window_titles",
            lambda: [(200, "[#946 stuff] - mcp_coder")],
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.HAS_WIN32GUI",
            True,
        )

        result = is_vscode_window_open_for_folder(
            folder_path="/tmp/mcp_coder_946",
            issue_number=946,
            repo="owner/mcp_coder",
        )

        assert result is True

    def test_get_vscode_window_titles_returns_pid_title_tuples(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """_get_vscode_window_titles returns list of (int, str) tuples."""
        from mcp_coder.workflows.vscodeclaude.sessions import (
            _get_vscode_window_titles,
            clear_vscode_window_cache,
        )

        clear_vscode_window_cache()

        # Force the Windows code path on
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.HAS_WIN32GUI",
            True,
        )
        # PID lookup says pids 100 and 200 are VSCode
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions._get_vscode_pids",
            lambda: {100, 200},
        )

        mock_win32gui = MagicMock()
        mock_win32process = MagicMock()

        # Two visible VSCode windows, one each on pid 100 and 200
        mock_win32gui.IsWindowVisible.return_value = True
        mock_win32gui.GetWindowText.side_effect = [
            "window-on-pid-100",
            "window-on-pid-200",
        ]
        mock_win32process.GetWindowThreadProcessId.side_effect = [(0, 100), (0, 200)]

        def enum_windows(callback: object, _: object) -> None:
            assert callable(callback)
            callback(1, None)
            callback(2, None)

        mock_win32gui.EnumWindows.side_effect = enum_windows

        # raising=False so the test works on non-Windows where these
        # attributes do not exist (the production code only imports them
        # when HAS_WIN32GUI is True).
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.win32gui",
            mock_win32gui,
            raising=False,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.win32process",
            mock_win32process,
            raising=False,
        )

        result = _get_vscode_window_titles(refresh=True)

        clear_vscode_window_cache()

        assert isinstance(result, list)
        assert len(result) == 2
        for entry in result:
            assert isinstance(entry, tuple)
            assert len(entry) == 2
            assert isinstance(entry[0], int)
            assert isinstance(entry[1], str)
        assert result[0][0] == 100
        assert result[1][0] == 200


class TestGetSessionForIssueSoftDelete:
    """Tests for get_session_for_issue with .to_be_deleted exclusion."""

    def test_excludes_soft_deleted(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Session found in JSON but folder in .to_be_deleted -> returns None."""
        sessions_file = tmp_path / "sessions.json"
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.get_sessions_file_path",
            lambda: sessions_file,
        )

        workspace_base = tmp_path / "workspace"
        workspace_base.mkdir()
        folder_name = "repo_42"

        session = {
            "folder": str(workspace_base / folder_name),
            "repo": "owner/repo",
            "issue_number": 42,
            "status": "status-07:code-review",
            "vscode_pid": None,
            "started_at": "2024-01-22T10:30:00Z",
            "is_intervention": False,
        }
        store = {"sessions": [session], "last_updated": "2024-01-22T10:30:00Z"}
        sessions_file.write_text(json.dumps(store))

        # Mark folder as soft-deleted
        (workspace_base / ".to_be_deleted").write_text(folder_name + "\n")

        found = get_session_for_issue("owner/repo", 42, str(workspace_base))
        assert found is None

    def test_returns_non_deleted(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Session found, folder not in .to_be_deleted -> returns session."""
        sessions_file = tmp_path / "sessions.json"
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.get_sessions_file_path",
            lambda: sessions_file,
        )

        workspace_base = tmp_path / "workspace"
        workspace_base.mkdir()
        folder_name = "repo_42"

        session = {
            "folder": str(workspace_base / folder_name),
            "repo": "owner/repo",
            "issue_number": 42,
            "status": "status-07:code-review",
            "vscode_pid": None,
            "started_at": "2024-01-22T10:30:00Z",
            "is_intervention": False,
        }
        store = {"sessions": [session], "last_updated": "2024-01-22T10:30:00Z"}
        sessions_file.write_text(json.dumps(store))

        # No .to_be_deleted file
        found = get_session_for_issue("owner/repo", 42, str(workspace_base))
        assert found is not None
        assert found["issue_number"] == 42  # pylint: disable=unsubscriptable-object

    def test_multiple_active_returns_none(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Two sessions for same issue, neither deleted -> log error, return None."""
        sessions_file = tmp_path / "sessions.json"
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.get_sessions_file_path",
            lambda: sessions_file,
        )

        workspace_base = tmp_path / "workspace"
        workspace_base.mkdir()

        session1 = {
            "folder": str(workspace_base / "repo_42"),
            "repo": "owner/repo",
            "issue_number": 42,
            "status": "status-07:code-review",
            "vscode_pid": None,
            "started_at": "2024-01-22T10:30:00Z",
            "is_intervention": False,
        }
        session2 = {
            "folder": str(workspace_base / "repo_42-folder1"),
            "repo": "owner/repo",
            "issue_number": 42,
            "status": "status-04:plan-review",
            "vscode_pid": None,
            "started_at": "2024-01-22T11:30:00Z",
            "is_intervention": False,
        }
        store = {
            "sessions": [session1, session2],
            "last_updated": "2024-01-22T10:30:00Z",
        }
        sessions_file.write_text(json.dumps(store))

        with caplog.at_level(
            logging.ERROR, logger="mcp_coder.workflows.vscodeclaude.sessions"
        ):
            found = get_session_for_issue("owner/repo", 42, str(workspace_base))

        assert found is None
        assert any(
            "Multiple active folders" in record.message for record in caplog.records
        )


class TestWarnOrphanFolders:
    """Tests for warn_orphan_folders function."""

    def test_logs_warning_for_untracked(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Folder on disk not in sessions.json or .to_be_deleted -> warning logged."""
        sessions_file = tmp_path / "sessions.json"
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.get_sessions_file_path",
            lambda: sessions_file,
        )
        store = {"sessions": [], "last_updated": ""}
        sessions_file.write_text(json.dumps(store))

        workspace_base = tmp_path / "workspace"
        workspace_base.mkdir()
        # Create orphan folder matching pattern
        (workspace_base / "repo_42").mkdir()

        with caplog.at_level(
            logging.WARNING, logger="mcp_coder.workflows.vscodeclaude.sessions"
        ):
            warn_orphan_folders(
                str(workspace_base),
                "owner/repo",
                42,
                session_folders=set(),
                to_be_deleted=set(),
            )

        assert any(
            "Orphan folder detected" in record.message for record in caplog.records
        )

    def test_ignores_tracked_sessions(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Folder on disk in sessions.json -> no warning."""
        sessions_file = tmp_path / "sessions.json"
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.get_sessions_file_path",
            lambda: sessions_file,
        )

        workspace_base = tmp_path / "workspace"
        workspace_base.mkdir()
        folder_name = "repo_42"
        (workspace_base / folder_name).mkdir()

        session = {
            "folder": str(workspace_base / folder_name),
            "repo": "owner/repo",
            "issue_number": 42,
            "status": "status-07:code-review",
            "vscode_pid": None,
            "started_at": "2024-01-22T10:30:00Z",
            "is_intervention": False,
        }
        store = {"sessions": [session], "last_updated": ""}
        sessions_file.write_text(json.dumps(store))

        with caplog.at_level(
            logging.WARNING, logger="mcp_coder.workflows.vscodeclaude.sessions"
        ):
            warn_orphan_folders(
                str(workspace_base),
                "owner/repo",
                42,
                session_folders={folder_name},
                to_be_deleted=set(),
            )

        assert not any(
            "Orphan folder detected" in record.message for record in caplog.records
        )

    def test_ignores_to_be_deleted(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Folder on disk in .to_be_deleted -> no warning."""
        sessions_file = tmp_path / "sessions.json"
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.get_sessions_file_path",
            lambda: sessions_file,
        )
        store = {"sessions": [], "last_updated": ""}
        sessions_file.write_text(json.dumps(store))

        workspace_base = tmp_path / "workspace"
        workspace_base.mkdir()
        folder_name = "repo_42"
        (workspace_base / folder_name).mkdir()
        (workspace_base / ".to_be_deleted").write_text(folder_name + "\n")

        with caplog.at_level(
            logging.WARNING, logger="mcp_coder.workflows.vscodeclaude.sessions"
        ):
            warn_orphan_folders(
                str(workspace_base),
                "owner/repo",
                42,
                session_folders=set(),
                to_be_deleted={folder_name},
            )

        assert not any(
            "Orphan folder detected" in record.message for record in caplog.records
        )

    def test_ignores_unrelated_folders(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Folder on disk not matching pattern -> no warning."""
        sessions_file = tmp_path / "sessions.json"
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.get_sessions_file_path",
            lambda: sessions_file,
        )
        store = {"sessions": [], "last_updated": ""}
        sessions_file.write_text(json.dumps(store))

        workspace_base = tmp_path / "workspace"
        workspace_base.mkdir()
        # Create folder that does NOT match the pattern for issue 42
        (workspace_base / "other_project").mkdir()
        (workspace_base / "repo_99").mkdir()

        with caplog.at_level(
            logging.WARNING, logger="mcp_coder.workflows.vscodeclaude.sessions"
        ):
            warn_orphan_folders(
                str(workspace_base),
                "owner/repo",
                42,
                session_folders=set(),
                to_be_deleted=set(),
            )

        assert not any(
            "Orphan folder detected" in record.message for record in caplog.records
        )


class TestIsSessionActiveFallbackChain:
    """Tests for is_session_active() fallback chain behaviour.

    Within the launch-grace window, is_session_active() skips the title
    check and runs the PID -> cmdline fallback chain. These tests use a
    recent ``started_at`` to stay inside the grace window so the fallback
    paths are exercised on the Windows path.
    """

    def test_windows_title_miss_pid_alive_returns_active(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Within grace, PID alive -> active (title check skipped)."""
        recent = (datetime.now(timezone.utc) - timedelta(seconds=5)).isoformat()
        folder = tmp_path / "mcp_coder_542"
        folder.mkdir()

        session: VSCodeClaudeSession = {
            "folder": str(folder),
            "repo": "owner/repo",
            "issue_number": 542,
            "status": "s",
            "vscode_pid": 28036,
            "vscode_pid_create_time": None,
            "started_at": recent,
            "is_intervention": False,
        }

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.HAS_WIN32GUI", True
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.session_has_artifacts",
            lambda f: True,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.check_vscode_running",
            lambda pid, expected_create_time: True,
        )

        with caplog.at_level(
            logging.DEBUG, logger="mcp_coder.workflows.vscodeclaude.sessions"
        ):
            result = is_session_active(session)

        assert result is True
        assert any(
            "active (PID 28036 alive)" in record.message for record in caplog.records
        )

    def test_windows_title_miss_cmdline_match_refreshes_pid(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Within grace, PID dead + cmdline match w/ new PID -> refresh + active."""
        recent = (datetime.now(timezone.utc) - timedelta(seconds=5)).isoformat()
        folder = tmp_path / "mcp_coder_542"
        folder.mkdir()

        session: VSCodeClaudeSession = {
            "folder": str(folder),
            "repo": "owner/repo",
            "issue_number": 542,
            "status": "s",
            "vscode_pid": 28036,
            "vscode_pid_create_time": None,
            "started_at": recent,
            "is_intervention": False,
        }

        update_mock = MagicMock()
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.HAS_WIN32GUI", True
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.session_has_artifacts",
            lambda f: True,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.check_vscode_running",
            lambda pid, expected_create_time: False,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.is_vscode_open_for_folder",
            lambda f: (True, 54321),
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.update_session_pid",
            update_mock,
        )

        with caplog.at_level(
            logging.DEBUG, logger="mcp_coder.workflows.vscodeclaude.sessions"
        ):
            result = is_session_active(session)

        assert result is True
        update_mock.assert_called_once_with(str(folder), 54321)
        assert any(
            "active (cmdline match PID=54321)" in record.message
            for record in caplog.records
        )
        assert any(
            "refreshing stored PID 28036 -> 54321" in record.message
            for record in caplog.records
        )

    def test_windows_all_miss_returns_inactive(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Within grace, PID dead + cmdline miss -> inactive with INFO summary."""
        recent = (datetime.now(timezone.utc) - timedelta(seconds=5)).isoformat()
        folder = tmp_path / "mcp_coder_542"
        folder.mkdir()

        session: VSCodeClaudeSession = {
            "folder": str(folder),
            "repo": "owner/repo",
            "issue_number": 542,
            "status": "s",
            "vscode_pid": 28036,
            "vscode_pid_create_time": None,
            "started_at": recent,
            "is_intervention": False,
        }

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.HAS_WIN32GUI", True
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.session_has_artifacts",
            lambda f: True,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.check_vscode_running",
            lambda pid, expected_create_time: False,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.is_vscode_open_for_folder",
            lambda f: (False, None),
        )

        with caplog.at_level(
            logging.DEBUG, logger="mcp_coder.workflows.vscodeclaude.sessions"
        ):
            result = is_session_active(session)

        assert result is False
        assert any(
            "inactive (PID 28036 gone / no cmdline match)" in record.message
            for record in caplog.records
        )

    def test_non_windows_pid_alive_info_format(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """HAS_WIN32GUI=False + PID alive -> 'active (PID 1234 alive)' only."""
        folder = tmp_path / "mcp_coder_100"
        folder.mkdir()

        session: VSCodeClaudeSession = {
            "folder": str(folder),
            "repo": "owner/repo",
            "issue_number": 100,
            "status": "s",
            "vscode_pid": 1234,
            "vscode_pid_create_time": None,
            "started_at": "2024-01-01T00:00:00Z",
            "is_intervention": False,
        }

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.HAS_WIN32GUI", False
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.session_has_artifacts",
            lambda f: True,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.check_vscode_running",
            lambda pid, expected_create_time: True,
        )

        with caplog.at_level(
            logging.DEBUG, logger="mcp_coder.workflows.vscodeclaude.sessions"
        ):
            result = is_session_active(session)

        assert result is True
        matching = [
            record
            for record in caplog.records
            if "active (PID 1234 alive)" in record.message
        ]
        assert matching, "Expected INFO line 'active (PID 1234 alive)'"
        assert "window-title" not in matching[0].message

    @pytest.mark.parametrize(
        "session_data",
        [
            {"issue_number": 100, "vscode_pid": 1234},
            {"repo": "owner/repo", "vscode_pid": 1234},
        ],
        ids=["missing_repo", "missing_issue_number"],
    )
    def test_guard_none_falls_through_to_pid_check(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        session_data: dict[str, object],
    ) -> None:
        """When repo or issue_number is None, falls through to PID check."""
        folder = tmp_path / "mcp_coder_session"
        folder.mkdir()

        session: dict[str, object] = {
            "folder": str(folder),
            "status": "s",
            "vscode_pid_create_time": None,
            "started_at": "2024-01-01T00:00:00Z",
            "is_intervention": False,
            **session_data,
        }

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.HAS_WIN32GUI", True
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.session_has_artifacts",
            lambda f: True,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.check_vscode_running",
            lambda pid, expected_create_time: True,
        )

        result = is_session_active(session)  # type: ignore[arg-type]

        assert result is True

    def test_non_windows_uses_pid_fallback(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """HAS_WIN32GUI=False preserves existing PID-based behavior."""
        folder = tmp_path / "mcp_coder_100"
        folder.mkdir()

        session: VSCodeClaudeSession = {
            "folder": str(folder),
            "repo": "owner/repo",
            "issue_number": 100,
            "status": "s",
            "vscode_pid": 1234,
            "vscode_pid_create_time": None,
            "started_at": "2024-01-01T00:00:00Z",
            "is_intervention": False,
        }

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.HAS_WIN32GUI", False
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.session_has_artifacts",
            lambda f: True,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.check_vscode_running",
            lambda pid, expected_create_time: True,
        )

        result = is_session_active(session)

        assert result is True

    def test_returns_false_on_non_windows(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should return False when win32gui not available."""
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.HAS_WIN32GUI",
            False,
        )

        result = is_vscode_window_open_for_folder(
            folder_path="/workspace/mcp_coder_219",
            issue_number=219,
            repo="owner/mcp_coder",
        )

        assert result is False

    def test_requires_both_issue_and_repo_in_title(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should require BOTH issue number AND repo name in title."""
        # Window has issue number but wrong repo
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions._get_vscode_window_titles",
            lambda: [
                (100, "[#219 review] Title - different_repo - Visual Studio Code")
            ],
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions._get_vscode_processes",
            lambda: [
                {"pid": 100, "cmdline_lower": "code.exe /workspace/mcp_coder_219"}
            ],
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.HAS_WIN32GUI",
            True,
        )

        result = is_vscode_window_open_for_folder(
            folder_path="/workspace/mcp_coder_219",
            issue_number=219,
            repo="owner/mcp_coder",
        )

        assert result is False

    def test_does_not_match_title_without_bracket_prefix(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should NOT match window where issue number appears without [ prefix.

        Regression test: GitHub extension can show e.g. '#219 - mcp_coder' in
        the window title when browsing an issue, which should NOT be treated as
        an active vscodeclaude workspace session.
        """
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions._get_vscode_window_titles",
            lambda: [(100, "#219 Fix the thing - mcp_coder - Visual Studio Code")],
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions._get_vscode_processes",
            lambda: [
                {"pid": 100, "cmdline_lower": "code.exe /workspace/mcp_coder_219"}
            ],
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.HAS_WIN32GUI",
            True,
        )

        result = is_vscode_window_open_for_folder(
            folder_path="/workspace/mcp_coder_219",
            issue_number=219,
            repo="owner/mcp_coder",
        )

        assert result is False


class TestLaunchGrace:
    """Tests for launch-grace handling in is_session_active().

    For sessions older than LAUNCH_GRACE_SECONDS, a negative window-title
    match is authoritative and short-circuits the PID/cmdline fallback.
    Within the grace window, the title check is skipped to cover VSCode
    cold-start and extension reinstall delays.
    """

    @staticmethod
    def _started_at(seconds_ago: float) -> str:
        return (datetime.now(timezone.utc) - timedelta(seconds=seconds_ago)).isoformat()

    def test_established_no_title_returns_false_no_fallback(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Age >= grace + title miss -> False, even when PID/cmdline would match."""
        folder = tmp_path / "mcp_coder_700"
        folder.mkdir()

        session: VSCodeClaudeSession = {
            "folder": str(folder),
            "repo": "owner/repo",
            "issue_number": 700,
            "status": "s",
            "vscode_pid": 12345,
            "vscode_pid_create_time": None,
            "started_at": self._started_at(120.0),
            "is_intervention": False,
        }

        check_pid_calls: list[int | None] = []
        cmdline_calls: list[str] = []

        def mock_check(pid: int | None, expected_create_time: float | None) -> bool:
            check_pid_calls.append(pid)
            return True

        def mock_open_for_folder(folder_path: str) -> tuple[bool, int | None]:
            cmdline_calls.append(folder_path)
            return True, 99999

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.HAS_WIN32GUI", True
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.session_has_artifacts",
            lambda f: True,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.is_vscode_window_open_for_folder",
            lambda folder_path, issue_number=None, repo=None: False,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.check_vscode_running",
            mock_check,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.is_vscode_open_for_folder",
            mock_open_for_folder,
        )

        result = is_session_active(session)

        assert result is False
        assert check_pid_calls == [], "PID fallback must not run beyond grace"
        assert cmdline_calls == [], "cmdline fallback must not run beyond grace"

    def test_grace_no_title_cmdline_match_returns_true(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Age < grace + title miss + cmdline match -> True (fallback engaged)."""
        folder = tmp_path / "mcp_coder_701"
        folder.mkdir()

        session: VSCodeClaudeSession = {
            "folder": str(folder),
            "repo": "owner/repo",
            "issue_number": 701,
            "status": "s",
            "vscode_pid": 12345,
            "vscode_pid_create_time": None,
            "started_at": self._started_at(10.0),
            "is_intervention": False,
        }

        title_calls: list[int] = []

        def mock_title(
            folder_path: str, issue_number: int | None = None, repo: str | None = None
        ) -> bool:
            title_calls.append(issue_number or 0)
            return False

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.HAS_WIN32GUI", True
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.session_has_artifacts",
            lambda f: True,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.is_vscode_window_open_for_folder",
            mock_title,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.check_vscode_running",
            lambda pid, expected_create_time: False,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.is_vscode_open_for_folder",
            lambda f: (True, 12345),
        )

        result = is_session_active(session)

        assert result is True
        assert title_calls == [], "title check must be skipped within grace"

    def test_established_title_match_returns_true(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Age >= grace + title hit -> True without consulting fallback."""
        folder = tmp_path / "mcp_coder_702"
        folder.mkdir()

        session: VSCodeClaudeSession = {
            "folder": str(folder),
            "repo": "owner/repo",
            "issue_number": 702,
            "status": "s",
            "vscode_pid": 12345,
            "vscode_pid_create_time": None,
            "started_at": self._started_at(120.0),
            "is_intervention": False,
        }

        check_pid_calls: list[int | None] = []

        def mock_check(pid: int | None, expected_create_time: float | None) -> bool:
            check_pid_calls.append(pid)
            return True

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.HAS_WIN32GUI", True
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.session_has_artifacts",
            lambda f: True,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.is_vscode_window_open_for_folder",
            lambda folder_path, issue_number=None, repo=None: True,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.check_vscode_running",
            mock_check,
        )

        result = is_session_active(session)

        assert result is True
        assert check_pid_calls == [], "PID fallback must not run on title match"

    def test_malformed_started_at_treated_as_established(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Unparseable started_at -> age=inf -> established branch (title authoritative)."""
        folder = tmp_path / "mcp_coder_703"
        folder.mkdir()

        session: VSCodeClaudeSession = {
            "folder": str(folder),
            "repo": "owner/repo",
            "issue_number": 703,
            "status": "s",
            "vscode_pid": 12345,
            "vscode_pid_create_time": None,
            "started_at": "not-a-date",
            "is_intervention": False,
        }

        check_pid_calls: list[int | None] = []

        def mock_check(pid: int | None, expected_create_time: float | None) -> bool:
            check_pid_calls.append(pid)
            return True

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.HAS_WIN32GUI", True
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.session_has_artifacts",
            lambda f: True,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.is_vscode_window_open_for_folder",
            lambda folder_path, issue_number=None, repo=None: False,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.check_vscode_running",
            mock_check,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.is_vscode_open_for_folder",
            lambda f: (True, 12345),
        )

        result = is_session_active(session)

        assert result is False
        assert check_pid_calls == [], "fallback must not run when title authoritative"

    def test_non_windows_path_unaffected_by_age(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """HAS_WIN32GUI=False: fallback chain runs regardless of session age."""
        folder = tmp_path / "mcp_coder_704"
        folder.mkdir()

        session: VSCodeClaudeSession = {
            "folder": str(folder),
            "repo": "owner/repo",
            "issue_number": 704,
            "status": "s",
            "vscode_pid": 12345,
            "vscode_pid_create_time": None,
            "started_at": self._started_at(120.0),
            "is_intervention": False,
        }

        title_calls: list[int] = []

        def mock_title(
            folder_path: str, issue_number: int | None = None, repo: str | None = None
        ) -> bool:
            title_calls.append(issue_number or 0)
            return False

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.HAS_WIN32GUI", False
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.session_has_artifacts",
            lambda f: True,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.is_vscode_window_open_for_folder",
            mock_title,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.check_vscode_running",
            lambda pid, expected_create_time: True,
        )

        result = is_session_active(session)

        assert result is True
        assert title_calls == [], "title check must be skipped on non-Windows"


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
