"""Test session management functions for VSCode Claude."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.workflows.vscodeclaude.sessions import (
    VSCODE_PROCESS_NAMES,
    _get_vscode_processes,
    add_session,
    check_vscode_running,
    clear_vscode_process_cache,
    get_active_session_count,
    get_session_for_issue,
    get_sessions_file_path,
    is_vscode_window_open_for_folder,
    load_sessions,
    remove_session,
    save_sessions,
    session_has_artifacts,
    update_session_pid,
    update_session_status,
)
from mcp_coder.workflows.vscodeclaude.types import (
    VSCodeClaudeSession,
    VSCodeClaudeSessionStore,
)


class TestSessionManagement:
    """Test session load/save/check functions."""

    def test_get_sessions_file_path_windows(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Sessions file is in .mcp_coder on Windows."""
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.platform.system",
            lambda: "Windows",
        )
        path = get_sessions_file_path()
        assert ".mcp_coder" in str(path)
        assert "vscodeclaude_sessions.json" in str(path)

    def test_get_sessions_file_path_linux(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Sessions file is in .config/mcp_coder on Linux."""
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.platform.system",
            lambda: "Linux",
        )
        path = get_sessions_file_path()
        # Check for either forward or back slashes
        path_str = str(path)
        assert ".config" in path_str
        assert "mcp_coder" in path_str

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
        assert check_vscode_running(None) is False

    def test_check_vscode_running_nonexistent_pid(self) -> None:
        """Nonexistent PID returns False."""
        # Use a PID that almost certainly doesn't exist
        assert check_vscode_running(999999999) is False

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

        found = get_session_for_issue("owner/repo", 123)
        assert found is not None
        assert found["issue_number"] == 123

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

        found = get_session_for_issue("owner/repo", 999)
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

    def test_get_active_session_count_with_mocked_pid_check(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Counts only sessions with running PIDs and existing artifacts."""
        sessions_file = tmp_path / "sessions.json"
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.get_sessions_file_path",
            lambda: sessions_file,
        )

        # Mock check_vscode_running to return True for specific PID
        def mock_check(pid: int | None) -> bool:
            return pid == 1111

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.check_vscode_running",
            mock_check,
        )

        # Create folder for the active session so its artifacts exist.
        # Session with PID 2222 has no folder — simulates a zombie VSCode.
        folder_a = tmp_path / "session_a"
        folder_a.mkdir()

        sessions = [
            {
                "folder": str(folder_a),
                "repo": "o/r",
                "issue_number": 1,
                "status": "s",
                "vscode_pid": 1111,
                "started_at": "2024-01-01T00:00:00Z",
                "is_intervention": False,
            },
            {
                "folder": str(tmp_path / "session_b"),  # folder not created
                "repo": "o/r",
                "issue_number": 2,
                "status": "s",
                "vscode_pid": 2222,
                "started_at": "2024-01-01T00:00:00Z",
                "is_intervention": False,
            },
        ]
        store = {"sessions": sessions, "last_updated": "2024-01-22T10:30:00Z"}
        sessions_file.write_text(json.dumps(store))

        count = get_active_session_count()
        assert count == 1  # Only session_a: PID 1111 running + folder exists

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

    def test_returns_true_when_workspace_file_exists(self, tmp_path: Path) -> None:
        """Returns True when only the .code-workspace file exists."""
        folder = tmp_path / "mcp_coder_123"
        # Don't create the folder, but create the workspace file
        workspace = tmp_path / "mcp_coder_123.code-workspace"
        workspace.write_text("{}")
        assert session_has_artifacts(str(folder)) is True

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
    ("code"), causing processes like mcp-code-checker.exe to be mistakenly
    identified as VSCode and stored as session PIDs.
    """

    def test_vscode_process_names_contains_expected_values(self) -> None:
        """VSCODE_PROCESS_NAMES includes code.exe and code."""
        assert "code.exe" in VSCODE_PROCESS_NAMES
        assert "code" in VSCODE_PROCESS_NAMES

    def test_vscode_process_names_excludes_code_checker(self) -> None:
        """mcp-code-checker.exe is not in VSCODE_PROCESS_NAMES (substring trap)."""
        assert "mcp-code-checker.exe" not in VSCODE_PROCESS_NAMES

    def test_check_vscode_running_rejects_mcp_code_checker(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """check_vscode_running returns False for mcp-code-checker.exe PIDs."""
        mock_process = MagicMock()
        mock_process.name.return_value = "mcp-code-checker.exe"

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.psutil.pid_exists",
            lambda pid: True,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.psutil.Process",
            lambda pid: mock_process,
        )

        assert check_vscode_running(12345) is False

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

        assert check_vscode_running(12345) is True

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

        assert check_vscode_running(12345) is True

    def test_get_vscode_processes_excludes_mcp_code_checker(self) -> None:
        """_get_vscode_processes does not include mcp-code-checker.exe processes."""
        # Build mock process entries: one real VSCode, one mcp-code-checker
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
            "name": "mcp-code-checker.exe",
            "cmdline": [r"C:\tools\mcp-code-checker.exe", "--project", "my_repo_42"],
        }

        clear_vscode_process_cache()
        with patch(
            "mcp_coder.workflows.vscodeclaude.sessions.psutil.process_iter",
            return_value=[mock_vscode, mock_checker],
        ):
            processes = _get_vscode_processes(refresh=True)

        pids = [p["pid"] for p in processes]
        assert 1001 in pids  # real VSCode included
        assert 2002 not in pids  # mcp-code-checker excluded

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
        # Mock window titles to return a workspace window
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions._get_vscode_window_titles",
            lambda: ["[#219 plan-review] Fix bug - mcp_coder - Visual Studio Code"],
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
            lambda: ["mcp_coder - Visual Studio Code"],
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
            lambda: ["[#123 code-review] Other issue - mcp_coder - Visual Studio Code"],
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
            lambda: ["[#219 created] New issue - my_repo - Visual Studio Code"],
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
            lambda: ["[#219 review] Title - MCP_CODER - Visual Studio Code"],
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
            "mcp_coder.workflows.vscodeclaude.sessions.HAS_WIN32GUI",
            True,
        )

        result = is_vscode_window_open_for_folder(
            folder_path="/workspace/mcp_coder_219",
            issue_number=219,
            repo="owner/mcp_coder",
        )

        assert result is False

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
            lambda: ["[#219 review] Title - different_repo - Visual Studio Code"],
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
            lambda: ["#219 Fix the thing - mcp_coder - Visual Studio Code"],
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
