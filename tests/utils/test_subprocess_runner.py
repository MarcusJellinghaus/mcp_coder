"""Test subprocess_runner module."""

from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.utils.subprocess_runner import launch_process


class TestLaunchProcess:
    """Test launch_process function for non-blocking process execution."""

    def test_launch_process_returns_pid(self) -> None:
        """Returns PID from subprocess.Popen."""
        mock_process = MagicMock()
        mock_process.pid = 54321

        with patch(
            "mcp_coder.utils.subprocess_runner.subprocess.Popen",
            return_value=mock_process,
        ):
            pid = launch_process(["echo", "hello"])
            assert pid == 54321

    def test_launch_process_passes_command_list(self) -> None:
        """Passes command list to Popen."""
        captured_args: list[list[str]] = []

        def mock_popen(cmd: list[str], **kwargs: object) -> MagicMock:
            captured_args.append(cmd)
            mock = MagicMock()
            mock.pid = 1
            return mock

        with patch(
            "mcp_coder.utils.subprocess_runner.subprocess.Popen",
            side_effect=mock_popen,
        ):
            launch_process(["echo", "hello", "world"])

        assert captured_args[0] == ["echo", "hello", "world"]

    def test_launch_process_with_shell_true(self) -> None:
        """Passes shell=True when specified."""
        captured_kwargs: dict[str, object] = {}

        def mock_popen(cmd: str, **kwargs: object) -> MagicMock:
            captured_kwargs.update(kwargs)
            mock = MagicMock()
            mock.pid = 1
            return mock

        with patch(
            "mcp_coder.utils.subprocess_runner.subprocess.Popen",
            side_effect=mock_popen,
        ):
            launch_process('echo "hello world"', shell=True)

        assert captured_kwargs["shell"] is True

    def test_launch_process_with_cwd(self) -> None:
        """Passes cwd to Popen."""
        captured_kwargs: dict[str, object] = {}

        def mock_popen(cmd: list[str], **kwargs: object) -> MagicMock:
            captured_kwargs.update(kwargs)
            mock = MagicMock()
            mock.pid = 1
            return mock

        with patch(
            "mcp_coder.utils.subprocess_runner.subprocess.Popen",
            side_effect=mock_popen,
        ):
            launch_process(["echo", "test"], cwd="/some/path")

        assert captured_kwargs["cwd"] == "/some/path"

    def test_launch_process_redirects_stdout_stderr(self) -> None:
        """Redirects stdout and stderr to DEVNULL."""
        import subprocess

        captured_kwargs: dict[str, object] = {}

        def mock_popen(cmd: list[str], **kwargs: object) -> MagicMock:
            captured_kwargs.update(kwargs)
            mock = MagicMock()
            mock.pid = 1
            return mock

        with patch(
            "mcp_coder.utils.subprocess_runner.subprocess.Popen",
            side_effect=mock_popen,
        ):
            launch_process(["echo", "test"])

        assert captured_kwargs["stdout"] == subprocess.DEVNULL
        assert captured_kwargs["stderr"] == subprocess.DEVNULL
