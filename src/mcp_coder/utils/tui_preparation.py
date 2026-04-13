"""TUI pre-flight terminal checks.

Detects terminal-specific issues before launching TUI apps and either
auto-fixes them silently, warns, or prompts the user to abort.
"""

import atexit
import ctypes
import logging
import os
import re
import sys
from collections.abc import Callable
from pathlib import Path

from mcp_coder.utils.log_utils import OUTPUT

logger = logging.getLogger(__name__)

_VSCODE_GPU_PROMPT = "VS Code terminal gpuAcceleration is set to 'off', which breaks TUI mouse/rendering."
_VSCODE_GPU_INSTRUCTIONS = (
    "To fix: Open VS Code Settings → search 'gpuAcceleration' "
    "→ change to 'auto' or remove the setting → restart the terminal."
)


class TuiPreflightAbort(Exception):
    """Raised when the TUI cannot launch due to terminal issues."""

    def __init__(self, message: str, exit_code: int = 1) -> None:
        super().__init__(message)
        self.message = message
        self.exit_code = exit_code


class TuiChecker:
    """Runs pre-flight terminal checks before launching a TUI app."""

    def __init__(self) -> None:
        self._silent_fixes: list[tuple[str, Callable[[], None]]] = []
        self._warnings: list[str] = []
        self._prompts: list[tuple[str, str]] = []

    def run_all_checks(self) -> None:
        """Run all checks, apply fixes, log warnings, and present prompts."""
        self._check_windows_cmd_codepage()
        self._check_vscode_gpu_acceleration()
        self._check_ssh_dumb_terminal()
        self._check_non_utf8_locale()
        self._check_tmux_screen()
        self._check_macos_terminal_app()
        self._check_windows_terminal()

        for msg, fix_fn in self._silent_fixes:
            fix_fn()
            logger.log(OUTPUT, msg)

        for msg in self._warnings:
            logger.log(OUTPUT, msg)

        for prompt_text, instruction_text in self._prompts:
            self._present_prompt(prompt_text, instruction_text)

    def _present_prompt(self, prompt_text: str, instruction_text: str) -> None:
        """Present a prompt to the user. Both choices result in abort.

        Raises:
            TuiPreflightAbort: Always raised — after viewing instructions or on abort.
        """
        logger.log(OUTPUT, prompt_text)
        try:
            choice = input("(I)nstructions or (A)bort: ").strip().lower()
        except EOFError:
            raise TuiPreflightAbort("Aborted by user (EOF).") from None
        if choice.startswith("i"):
            logger.log(OUTPUT, instruction_text)
            try:
                input("Press Enter to exit...")
            except EOFError:
                pass
            raise TuiPreflightAbort("Aborted after viewing instructions.")
        raise TuiPreflightAbort("Aborted by user.")

    def _check_ssh_dumb_terminal(self) -> None:
        """Warn if TERM is 'dumb' or unset."""
        term = os.environ.get("TERM")
        if term is None or term == "dumb":
            self._warnings.append(
                "Terminal type is 'dumb' or unset — TUI may not render correctly."
                " Fix: export TERM=xterm-256color"
            )

    def _check_non_utf8_locale(self) -> None:
        """Warn if locale is set but not UTF-8."""
        lang = os.environ.get("LANG")
        lc_all = os.environ.get("LC_ALL")
        if lang is None and lc_all is None:
            return
        for val in (lc_all, lang):
            if val and "utf-8" in val.lower():
                return
        self._warnings.append(
            "System locale is not UTF-8 — Unicode rendering may break."
            " Fix: export LANG=en_US.UTF-8"
        )

    def _check_tmux_screen(self) -> None:
        """Warn if running inside tmux or screen."""
        if os.environ.get("TMUX") or os.environ.get("STY"):
            self._warnings.append(
                "Running inside tmux/screen — mouse forwarding may be disabled."
                " Fix: set -g mouse on (tmux)"
            )

    def _check_macos_terminal_app(self) -> None:
        """Warn if running in macOS Terminal.app."""
        if sys.platform != "darwin":
            return
        if os.environ.get("TERM_PROGRAM") == "Apple_Terminal":
            self._warnings.append(
                "macOS Terminal.app has limited mouse reporting"
                " — consider iTerm2 or Kitty for full TUI support."
            )

    def _check_windows_cmd_codepage(self) -> None:
        """Silently fix non-UTF-8 console codepage on Windows."""
        if sys.platform != "win32":
            return
        if not hasattr(ctypes, "windll"):
            return
        current_cp = ctypes.windll.kernel32.GetConsoleOutputCP()
        if current_cp == 65001:
            return

        def fix_fn() -> None:
            ctypes.windll.kernel32.SetConsoleOutputCP(65001)
            atexit.register(ctypes.windll.kernel32.SetConsoleOutputCP, current_cp)

        self._silent_fixes.append(
            (f"Console codepage set to UTF-8 (was {current_cp})", fix_fn)
        )

    def _check_vscode_gpu_acceleration(self) -> None:
        """Prompt if VS Code gpuAcceleration is set to 'off'."""
        if sys.platform != "win32":
            return
        if os.environ.get("SSH_CONNECTION"):
            return
        if os.environ.get("TERM_PROGRAM") != "vscode":
            return
        settings_path = (
            Path(os.environ.get("APPDATA", "")) / "Code" / "User" / "settings.json"
        )
        if not settings_path.is_file():
            return
        try:
            content = settings_path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            return
        if re.search(r'"terminal\.integrated\.gpuAcceleration"\s*:\s*"off"', content):
            self._prompts.append((_VSCODE_GPU_PROMPT, _VSCODE_GPU_INSTRUCTIONS))

    def _check_windows_terminal(self) -> None:
        """No-op stub for Windows Terminal (future-proofing)."""
        if sys.platform != "win32":
            return
