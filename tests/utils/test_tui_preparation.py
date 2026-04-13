"""Tests for TUI pre-flight terminal checks."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.utils.tui_preparation import TuiChecker, TuiPreflightAbort


class TestTuiPreflightAbort:
    def test_tui_preflight_abort_attributes(self) -> None:
        exc = TuiPreflightAbort("test error", exit_code=42)
        assert exc.message == "test error"
        assert exc.exit_code == 42

    def test_tui_preflight_abort_default_exit_code(self) -> None:
        exc = TuiPreflightAbort("test error")
        assert exc.exit_code == 1


class TestTuiCheckerSkeleton:
    def test_run_all_checks_empty(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """No issues detected, no errors raised."""
        monkeypatch.setenv("TERM", "xterm-256color")
        monkeypatch.delenv("TMUX", raising=False)
        monkeypatch.delenv("STY", raising=False)
        monkeypatch.delenv("LANG", raising=False)
        monkeypatch.delenv("LC_ALL", raising=False)
        monkeypatch.setattr("sys.platform", "linux")
        checker = TuiChecker()
        checker.run_all_checks()

    def test_presentation_order(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Silent fixes run before warnings before prompts."""
        monkeypatch.setenv("TERM", "xterm-256color")
        monkeypatch.delenv("TMUX", raising=False)
        monkeypatch.delenv("STY", raising=False)
        monkeypatch.delenv("LANG", raising=False)
        monkeypatch.delenv("LC_ALL", raising=False)
        monkeypatch.setattr("sys.platform", "linux")

        order: list[str] = []
        checker = TuiChecker()
        checker._silent_fixes.append(("fix applied", lambda: order.append("fix")))
        checker._warnings.append("warning msg")
        checker._prompts.append(("prompt text", "instruction text"))

        with patch("mcp_coder.utils.tui_preparation.logger") as mock_logger:

            def log_side_effect(_level: int, msg: str) -> None:
                if msg == "fix applied":
                    order.append("fix_logged")
                elif msg == "warning msg":
                    order.append("warning")
                elif msg == "prompt text":
                    order.append("prompt")

            mock_logger.log.side_effect = log_side_effect

            with patch("builtins.input", return_value="a"):
                with pytest.raises(TuiPreflightAbort):
                    checker.run_all_checks()

        assert order == ["fix", "fix_logged", "warning", "prompt"]


class TestPresentPrompt:
    def test_present_prompt_instructions_raises(self) -> None:
        checker = TuiChecker()
        with patch("builtins.input", return_value="i"):
            with pytest.raises(TuiPreflightAbort):
                checker._present_prompt("prompt", "instructions")

    def test_present_prompt_abort_raises(self) -> None:
        checker = TuiChecker()
        with patch("builtins.input", return_value="a"):
            with pytest.raises(TuiPreflightAbort):
                checker._present_prompt("prompt", "instructions")

    def test_present_prompt_default_aborts(self) -> None:
        checker = TuiChecker()
        with patch("builtins.input", return_value="x"):
            with pytest.raises(TuiPreflightAbort):
                checker._present_prompt("prompt", "instructions")

    def test_present_prompt_eof_aborts(self) -> None:
        checker = TuiChecker()
        with patch("builtins.input", side_effect=EOFError):
            with pytest.raises(TuiPreflightAbort):
                checker._present_prompt("prompt", "instructions")


class TestCheckSshDumbTerminal:
    def test_check_ssh_dumb_terminal_detected(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("TERM", "dumb")
        checker = TuiChecker()
        checker._check_ssh_dumb_terminal()
        assert len(checker._warnings) == 1
        assert "dumb" in checker._warnings[0]

    def test_check_ssh_dumb_terminal_unset(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("TERM", raising=False)
        checker = TuiChecker()
        checker._check_ssh_dumb_terminal()
        assert len(checker._warnings) == 1

    def test_check_ssh_dumb_terminal_ok(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("TERM", "xterm-256color")
        checker = TuiChecker()
        checker._check_ssh_dumb_terminal()
        assert len(checker._warnings) == 0


class TestCheckNonUtf8Locale:
    def test_check_non_utf8_locale_detected(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("LANG", "C")
        monkeypatch.delenv("LC_ALL", raising=False)
        checker = TuiChecker()
        checker._check_non_utf8_locale()
        assert len(checker._warnings) == 1
        assert "UTF-8" in checker._warnings[0]

    def test_check_non_utf8_locale_ok(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("LANG", "en_US.UTF-8")
        monkeypatch.delenv("LC_ALL", raising=False)
        checker = TuiChecker()
        checker._check_non_utf8_locale()
        assert len(checker._warnings) == 0

    def test_check_non_utf8_locale_unset(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("LANG", raising=False)
        monkeypatch.delenv("LC_ALL", raising=False)
        checker = TuiChecker()
        checker._check_non_utf8_locale()
        assert len(checker._warnings) == 0

    def test_check_non_utf8_locale_lc_all_overrides(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("LANG", "C")
        monkeypatch.setenv("LC_ALL", "en_US.UTF-8")
        checker = TuiChecker()
        checker._check_non_utf8_locale()
        assert len(checker._warnings) == 0


class TestCheckTmuxScreen:
    def test_check_tmux_detected(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("TMUX", "/tmp/tmux-1000/default,12345,0")
        monkeypatch.delenv("STY", raising=False)
        checker = TuiChecker()
        checker._check_tmux_screen()
        assert len(checker._warnings) == 1
        assert "tmux" in checker._warnings[0]

    def test_check_screen_detected(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("TMUX", raising=False)
        monkeypatch.setenv("STY", "12345.pts-0")
        checker = TuiChecker()
        checker._check_tmux_screen()
        assert len(checker._warnings) == 1

    def test_check_tmux_screen_not_detected(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("TMUX", raising=False)
        monkeypatch.delenv("STY", raising=False)
        checker = TuiChecker()
        checker._check_tmux_screen()
        assert len(checker._warnings) == 0


class TestCheckMacosTerminalApp:
    def test_check_macos_terminal_app_detected(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr("sys.platform", "darwin")
        monkeypatch.setenv("TERM_PROGRAM", "Apple_Terminal")
        checker = TuiChecker()
        checker._check_macos_terminal_app()
        assert len(checker._warnings) == 1
        assert "Terminal.app" in checker._warnings[0]

    def test_check_macos_terminal_app_wrong_platform(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr("sys.platform", "win32")
        monkeypatch.setenv("TERM_PROGRAM", "Apple_Terminal")
        checker = TuiChecker()
        checker._check_macos_terminal_app()
        assert len(checker._warnings) == 0

    def test_check_macos_terminal_app_different_terminal(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr("sys.platform", "darwin")
        monkeypatch.setenv("TERM_PROGRAM", "iTerm.app")
        checker = TuiChecker()
        checker._check_macos_terminal_app()
        assert len(checker._warnings) == 0


class TestCheckWindowsTerminal:
    def test_check_windows_terminal_noop(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("sys.platform", "win32")
        checker = TuiChecker()
        checker._check_windows_terminal()
        assert len(checker._warnings) == 0
        assert len(checker._silent_fixes) == 0
        assert len(checker._prompts) == 0


class TestCheckWindowsCmdCodepage:
    @staticmethod
    def _mock_windll(monkeypatch: pytest.MonkeyPatch, codepage: int = 437) -> MagicMock:
        mock_kernel32 = MagicMock()
        mock_kernel32.GetConsoleOutputCP.return_value = codepage
        mock_kernel32.SetConsoleOutputCP.return_value = 1
        mock_windll = MagicMock()
        mock_windll.kernel32 = mock_kernel32
        monkeypatch.setattr("ctypes.windll", mock_windll, raising=False)
        return mock_windll

    def test_check_cmd_codepage_non_utf8(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("sys.platform", "win32")
        self._mock_windll(monkeypatch, codepage=437)
        checker = TuiChecker()
        checker._check_windows_cmd_codepage()
        assert len(checker._silent_fixes) == 1
        assert "437" in checker._silent_fixes[0][0]

    def test_check_cmd_codepage_already_utf8(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr("sys.platform", "win32")
        self._mock_windll(monkeypatch, codepage=65001)
        checker = TuiChecker()
        checker._check_windows_cmd_codepage()
        assert len(checker._silent_fixes) == 0

    def test_check_cmd_codepage_wrong_platform(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr("sys.platform", "linux")
        checker = TuiChecker()
        checker._check_windows_cmd_codepage()
        assert len(checker._silent_fixes) == 0

    def test_check_cmd_codepage_fix_calls_set(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr("sys.platform", "win32")
        mock_windll = self._mock_windll(monkeypatch, codepage=437)
        checker = TuiChecker()
        checker._check_windows_cmd_codepage()
        _, fix_fn = checker._silent_fixes[0]
        with patch("atexit.register"):
            fix_fn()
        mock_windll.kernel32.SetConsoleOutputCP.assert_called_once_with(65001)

    def test_check_cmd_codepage_atexit_registered(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr("sys.platform", "win32")
        mock_windll = self._mock_windll(monkeypatch, codepage=437)
        checker = TuiChecker()
        checker._check_windows_cmd_codepage()
        _, fix_fn = checker._silent_fixes[0]
        with patch("atexit.register") as mock_atexit:
            fix_fn()
        mock_atexit.assert_called_once_with(
            mock_windll.kernel32.SetConsoleOutputCP, 437
        )

    def test_silent_fix_logged_via_run_all_checks(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr("sys.platform", "win32")
        monkeypatch.setenv("TERM", "xterm-256color")
        monkeypatch.delenv("TMUX", raising=False)
        monkeypatch.delenv("STY", raising=False)
        monkeypatch.delenv("LANG", raising=False)
        monkeypatch.delenv("LC_ALL", raising=False)
        self._mock_windll(monkeypatch, codepage=437)

        with patch("mcp_coder.utils.tui_preparation.logger") as mock_logger:
            with patch("atexit.register"):
                checker = TuiChecker()
                checker.run_all_checks()
            log_messages = [
                call.args[1]
                for call in mock_logger.log.call_args_list
                if len(call.args) > 1
            ]
            assert any("codepage" in msg.lower() for msg in log_messages)


class TestCheckVscodeGpuAcceleration:
    @staticmethod
    def _create_settings(
        tmp_path: Path, content: str = '{"terminal.integrated.gpuAcceleration": "off"}'
    ) -> None:
        settings_dir = tmp_path / "Code" / "User"
        settings_dir.mkdir(parents=True, exist_ok=True)
        (settings_dir / "settings.json").write_text(content, encoding="utf-8")

    def test_vscode_gpu_detected(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        monkeypatch.setattr("sys.platform", "win32")
        monkeypatch.setenv("TERM_PROGRAM", "vscode")
        monkeypatch.delenv("SSH_CONNECTION", raising=False)
        monkeypatch.setenv("APPDATA", str(tmp_path))
        self._create_settings(tmp_path)
        checker = TuiChecker()
        checker._check_vscode_gpu_acceleration()
        assert len(checker._prompts) == 1
        assert "gpuAcceleration" in checker._prompts[0][0]

    def test_vscode_gpu_not_off(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        monkeypatch.setattr("sys.platform", "win32")
        monkeypatch.setenv("TERM_PROGRAM", "vscode")
        monkeypatch.delenv("SSH_CONNECTION", raising=False)
        monkeypatch.setenv("APPDATA", str(tmp_path))
        self._create_settings(
            tmp_path, '{"terminal.integrated.gpuAcceleration": "auto"}'
        )
        checker = TuiChecker()
        checker._check_vscode_gpu_acceleration()
        assert len(checker._prompts) == 0

    def test_vscode_gpu_no_setting(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        monkeypatch.setattr("sys.platform", "win32")
        monkeypatch.setenv("TERM_PROGRAM", "vscode")
        monkeypatch.delenv("SSH_CONNECTION", raising=False)
        monkeypatch.setenv("APPDATA", str(tmp_path))
        self._create_settings(tmp_path, '{"editor.fontSize": 14}')
        checker = TuiChecker()
        checker._check_vscode_gpu_acceleration()
        assert len(checker._prompts) == 0

    def test_vscode_gpu_no_settings_file(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        monkeypatch.setattr("sys.platform", "win32")
        monkeypatch.setenv("TERM_PROGRAM", "vscode")
        monkeypatch.delenv("SSH_CONNECTION", raising=False)
        monkeypatch.setenv("APPDATA", str(tmp_path))
        checker = TuiChecker()
        checker._check_vscode_gpu_acceleration()
        assert len(checker._prompts) == 0

    def test_vscode_gpu_wrong_platform(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        monkeypatch.setattr("sys.platform", "linux")
        monkeypatch.setenv("TERM_PROGRAM", "vscode")
        monkeypatch.delenv("SSH_CONNECTION", raising=False)
        monkeypatch.setenv("APPDATA", str(tmp_path))
        self._create_settings(tmp_path)
        checker = TuiChecker()
        checker._check_vscode_gpu_acceleration()
        assert len(checker._prompts) == 0

    def test_vscode_gpu_ssh_connection_skips(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        monkeypatch.setattr("sys.platform", "win32")
        monkeypatch.setenv("TERM_PROGRAM", "vscode")
        monkeypatch.setenv("SSH_CONNECTION", "192.168.1.1 22 192.168.1.2 54321")
        monkeypatch.setenv("APPDATA", str(tmp_path))
        self._create_settings(tmp_path)
        checker = TuiChecker()
        checker._check_vscode_gpu_acceleration()
        assert len(checker._prompts) == 0

    def test_vscode_gpu_not_vscode_terminal(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        monkeypatch.setattr("sys.platform", "win32")
        monkeypatch.setenv("TERM_PROGRAM", "xterm")
        monkeypatch.delenv("SSH_CONNECTION", raising=False)
        monkeypatch.setenv("APPDATA", str(tmp_path))
        self._create_settings(tmp_path)
        checker = TuiChecker()
        checker._check_vscode_gpu_acceleration()
        assert len(checker._prompts) == 0

    def test_vscode_gpu_prompt_instructions_flow(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        monkeypatch.setattr("sys.platform", "win32")
        monkeypatch.setenv("TERM_PROGRAM", "vscode")
        monkeypatch.delenv("SSH_CONNECTION", raising=False)
        monkeypatch.setenv("APPDATA", str(tmp_path))
        monkeypatch.setenv("TERM", "xterm-256color")
        monkeypatch.delenv("TMUX", raising=False)
        monkeypatch.delenv("STY", raising=False)
        monkeypatch.delenv("LANG", raising=False)
        monkeypatch.delenv("LC_ALL", raising=False)
        self._create_settings(tmp_path)
        mock_windll = MagicMock()
        mock_windll.kernel32.GetConsoleOutputCP.return_value = 65001
        monkeypatch.setattr("ctypes.windll", mock_windll, raising=False)

        with patch("mcp_coder.utils.tui_preparation.logger") as mock_logger:
            with patch("builtins.input", return_value="i"):
                with pytest.raises(
                    TuiPreflightAbort,
                    match="Aborted after viewing instructions",
                ):
                    checker = TuiChecker()
                    checker.run_all_checks()
            log_messages = [
                call.args[1]
                for call in mock_logger.log.call_args_list
                if len(call.args) > 1
            ]
            assert any("gpuAcceleration" in msg for msg in log_messages)
            assert any("Settings" in msg for msg in log_messages)

    def test_vscode_gpu_prompt_abort_flow(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        monkeypatch.setattr("sys.platform", "win32")
        monkeypatch.setenv("TERM_PROGRAM", "vscode")
        monkeypatch.delenv("SSH_CONNECTION", raising=False)
        monkeypatch.setenv("APPDATA", str(tmp_path))
        monkeypatch.setenv("TERM", "xterm-256color")
        monkeypatch.delenv("TMUX", raising=False)
        monkeypatch.delenv("STY", raising=False)
        monkeypatch.delenv("LANG", raising=False)
        monkeypatch.delenv("LC_ALL", raising=False)
        self._create_settings(tmp_path)
        mock_windll = MagicMock()
        mock_windll.kernel32.GetConsoleOutputCP.return_value = 65001
        monkeypatch.setattr("ctypes.windll", mock_windll, raising=False)

        with patch("builtins.input", return_value="a"):
            with pytest.raises(TuiPreflightAbort, match="Aborted by user"):
                checker = TuiChecker()
                checker.run_all_checks()


class TestWarningsLoggedViaRunAllChecks:
    def test_warnings_logged_via_run_all_checks(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("TERM", "dumb")
        monkeypatch.delenv("TMUX", raising=False)
        monkeypatch.delenv("STY", raising=False)
        monkeypatch.delenv("LANG", raising=False)
        monkeypatch.delenv("LC_ALL", raising=False)
        monkeypatch.setattr("sys.platform", "linux")

        with patch("mcp_coder.utils.tui_preparation.logger") as mock_logger:
            checker = TuiChecker()
            checker.run_all_checks()
            mock_logger.log.assert_called()
            args = mock_logger.log.call_args_list
            assert any(call.args[0] == 25 for call in args)
