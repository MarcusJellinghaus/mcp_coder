from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.workflows.vscodeclaude.sessions import (
    VSCODE_PROCESS_NAMES,
    _get_vscode_processes,
    check_vscode_running,
    clear_vscode_process_cache,
    is_vscode_window_open_for_folder,
)


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
