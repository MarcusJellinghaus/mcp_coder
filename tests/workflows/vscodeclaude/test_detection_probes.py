from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.workflows.vscodeclaude import detection
from mcp_coder.workflows.vscodeclaude.detection import (
    VSCODE_PROCESS_NAMES,
    _get_vscode_processes,
    _get_vscode_window_titles,
    check_vscode_running,
    clear_vscode_process_cache,
    clear_vscode_window_cache,
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
            "mcp_coder.workflows.vscodeclaude.detection.psutil.pid_exists",
            lambda pid: True,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.detection.psutil.Process",
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
            "mcp_coder.workflows.vscodeclaude.detection.psutil.pid_exists",
            lambda pid: True,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.detection.psutil.Process",
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
            "mcp_coder.workflows.vscodeclaude.detection.psutil.pid_exists",
            lambda pid: True,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.detection.psutil.Process",
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
            "mcp_coder.workflows.vscodeclaude.detection.psutil.process_iter",
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
            "mcp_coder.workflows.vscodeclaude.detection.psutil.process_iter",
            return_value=[mock_insiders],
        ):
            processes = _get_vscode_processes(refresh=True)

        assert all(p["pid"] != 3003 for p in processes)


class TestGetVSCodeWindowTitles:
    """Tests for the _get_vscode_window_titles enumeration."""

    def test_get_vscode_window_titles_returns_pid_title_tuples(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """_get_vscode_window_titles returns list of (int, str) tuples."""
        clear_vscode_window_cache()

        # Force the Windows code path on
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.detection.HAS_WIN32GUI",
            True,
        )
        # PID lookup says pids 100 and 200 are VSCode
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.detection._get_vscode_pids",
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
            "mcp_coder.workflows.vscodeclaude.detection.win32gui",
            mock_win32gui,
            raising=False,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.detection.win32process",
            mock_win32process,
            raising=False,
        )

        result, ok = _get_vscode_window_titles(refresh=True)

        clear_vscode_window_cache()

        assert ok is True
        assert isinstance(result, list)
        assert len(result) == 2
        for entry in result:
            assert isinstance(entry, tuple)
            assert len(entry) == 2
            assert isinstance(entry[0], int)
            assert isinstance(entry[1], str)
        assert result[0][0] == 100
        assert result[1][0] == 200

    def test_enum_windows_failure_returns_not_ok(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """EnumWindows raising -> ([], False), and the failure is not cached."""
        clear_vscode_window_cache()
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.detection.HAS_WIN32GUI", True
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.detection._get_vscode_pids",
            lambda: {100},
        )
        mock_win32gui = MagicMock()
        mock_win32gui.EnumWindows.side_effect = RuntimeError("boom")
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.detection.win32gui",
            mock_win32gui,
            raising=False,
        )

        result = _get_vscode_window_titles(refresh=True)
        cache = detection._vscode_window_cache  # pylint: disable=protected-access

        clear_vscode_window_cache()

        assert result == ([], False)
        assert cache is None

    def test_without_win32gui_returns_not_ok(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """No win32gui -> ([], False)."""
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.detection.HAS_WIN32GUI", False
        )

        assert _get_vscode_window_titles(refresh=True) == ([], False)
