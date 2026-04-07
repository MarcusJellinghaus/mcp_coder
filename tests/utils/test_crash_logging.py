"""Tests for crash_logging utility."""

import subprocess
import sys
import textwrap
from collections.abc import Generator
from pathlib import Path
from unittest.mock import patch

import pytest

from mcp_coder.utils.crash_logging import (
    _reset_for_testing,
    _state,
    enable_crash_logging,
)


@pytest.fixture(autouse=True)
def _isolate_crash_logging_state() -> Generator[None, None, None]:
    """Reset module state before and after each test."""
    _reset_for_testing()
    yield
    _reset_for_testing()


class TestEnableCrashLogging:
    """Tests for enable_crash_logging."""

    def test_enable_creates_file(self, tmp_path: Path) -> None:
        """File is created under logs/faulthandler/ with expected pattern."""
        result = enable_crash_logging(tmp_path, "implement")

        assert result is not None
        assert result.exists()
        assert result.parent == tmp_path / "logs" / "faulthandler"
        assert result.name.startswith("crash_implement_")
        assert result.name.endswith(".log")

    def test_enable_calls_faulthandler(self, tmp_path: Path) -> None:
        """faulthandler.enable is called with correct arguments."""
        with patch("mcp_coder.utils.crash_logging.faulthandler") as mock_fh:
            enable_crash_logging(tmp_path, "plan")

            mock_fh.enable.assert_called_once()
            call_kwargs = mock_fh.enable.call_args
            assert call_kwargs[1]["all_threads"] is True
            assert call_kwargs[1]["file"] is _state["handle"]

    def test_enable_returns_path(self, tmp_path: Path) -> None:
        """Return value is a Path instance."""
        result = enable_crash_logging(tmp_path, "test")

        assert isinstance(result, Path)

    def test_enable_logs_debug(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """DEBUG log message contains the crash log path."""
        import logging

        with caplog.at_level(logging.DEBUG, logger="mcp_coder.utils.crash_logging"):
            result = enable_crash_logging(tmp_path, "implement")

        assert result is not None
        assert str(result) in caplog.text

    def test_enable_idempotent(self, tmp_path: Path) -> None:
        """Second call returns same path; faulthandler.enable called only once."""
        first = enable_crash_logging(tmp_path, "implement")
        first_handle = _state["handle"]

        with patch("mcp_coder.utils.crash_logging.faulthandler") as mock_fh:
            second = enable_crash_logging(tmp_path, "implement")

            mock_fh.enable.assert_not_called()

        assert first == second
        assert _state["handle"] is first_handle

    def test_enable_swallows_error(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Returns None and logs WARNING when os.makedirs raises OSError."""
        import logging

        with (
            patch(
                "mcp_coder.utils.crash_logging.os.makedirs",
                side_effect=OSError("disk full"),
            ),
            caplog.at_level(logging.WARNING, logger="mcp_coder.utils.crash_logging"),
        ):
            result = enable_crash_logging(tmp_path, "implement")

        assert result is None
        assert "Failed to enable crash logging" in caplog.text

    def test_reset_clears_state(self, tmp_path: Path) -> None:
        """After _reset_for_testing(), a new call creates a new file."""
        enable_crash_logging(tmp_path, "implement")
        first_handle = _state["handle"]
        _reset_for_testing()

        assert _state["path"] is None
        assert _state["handle"] is None

        second = enable_crash_logging(tmp_path, "plan")

        assert second is not None
        assert second.exists()
        assert _state["handle"] is not first_handle


def test_crash_log_captures_real_segfault(tmp_path: Path) -> None:
    """Subprocess crash via faulthandler._sigsegv() writes traceback to log.

    Uses faulthandler._sigsegv() — CPython's standard test hook for triggering
    a real segfault. This is the same API used by CPython's own test suite.
    """
    script = textwrap.dedent(f"""\
        import sys
        from pathlib import Path
        import faulthandler
        from mcp_coder.utils.crash_logging import enable_crash_logging
        enable_crash_logging(Path(r"{tmp_path}"), "test")
        faulthandler._sigsegv()
    """)

    result = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        check=False,
    )

    assert result.returncode != 0

    crash_dir = tmp_path / "logs" / "faulthandler"
    crash_files = list(crash_dir.glob("crash_test_*.log"))
    assert len(crash_files) == 1

    content = crash_files[0].read_text(encoding="utf-8")
    assert "Fatal Python error" in content or "Current thread" in content
