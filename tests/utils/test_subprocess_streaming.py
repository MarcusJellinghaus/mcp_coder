"""Tests for subprocess streaming inactivity watchdog timeout."""

import sys

from mcp_coder.utils.subprocess_runner import CommandOptions
from mcp_coder.utils.subprocess_streaming import StreamResult, stream_subprocess


class TestStreamInactivityWatchdog:
    """Test inactivity watchdog timeout in stream_subprocess."""

    def test_stream_inactivity_timeout_kills_process(self) -> None:
        """Process that goes silent is killed after inactivity timeout."""
        command = [
            sys.executable,
            "-u",
            "-c",
            "import time; print('hello'); time.sleep(999)",
        ]
        options = CommandOptions(timeout_seconds=2)

        stream = StreamResult(stream_subprocess(command, options))
        lines = list(stream)
        result = stream.result

        assert lines == ["hello"]
        assert result.timed_out is True  # pylint: disable=no-member
        assert result.execution_error is not None  # pylint: disable=no-member

    def test_stream_active_process_no_timeout(self) -> None:
        """Process with steady output does not trigger inactivity timeout."""
        command = [
            sys.executable,
            "-u",
            "-c",
            "import time\nfor i in range(4):\n    print(f'line{i}')\n    time.sleep(0.5)",
        ]
        options = CommandOptions(timeout_seconds=3)

        stream = StreamResult(stream_subprocess(command, options))
        lines = list(stream)
        result = stream.result

        assert lines == ["line0", "line1", "line2", "line3"]
        assert result.timed_out is False  # pylint: disable=no-member

    def test_stream_subprocess_basic(self) -> None:
        """Process that prints and exits normally."""
        command = [
            sys.executable,
            "-u",
            "-c",
            "print('a'); print('b'); print('c')",
        ]

        stream = StreamResult(stream_subprocess(command))
        lines = list(stream)
        result = stream.result

        assert lines == ["a", "b", "c"]
        assert result.timed_out is False  # pylint: disable=no-member
        assert result.return_code == 0  # pylint: disable=no-member
