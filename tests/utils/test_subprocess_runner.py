"""Test subprocess_runner module."""

import os
import sys
import threading
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.utils.subprocess_runner import (
    CommandOptions,
    CommandResult,
    launch_process,
    prepare_env,
)
from mcp_coder.utils.subprocess_streaming import StreamResult, stream_subprocess


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

        # DEVNULL is a negative integer (platform-specific value)
        # Both stdout and stderr should be redirected to the same DEVNULL
        assert isinstance(captured_kwargs["stdout"], int)
        assert captured_kwargs["stdout"] < 0  # DEVNULL is negative
        assert captured_kwargs["stdout"] == captured_kwargs["stderr"]


class TestStreamSubprocess:
    """Test stream_subprocess generator function."""

    def test_stream_subprocess_yields_lines(self) -> None:
        """Yields individual stdout lines from a command."""
        mock_proc = MagicMock()
        mock_proc.stdout = iter(["line1\n", "line2\n", "line3\n"])
        mock_proc.stderr = MagicMock()
        mock_proc.stderr.read.return_value = ""
        mock_proc.wait.return_value = 0
        mock_proc.returncode = 0
        mock_proc.pid = 123
        mock_proc.poll.return_value = 0

        with patch(
            "mcp_coder.utils.subprocess_streaming.subprocess.Popen",
            return_value=mock_proc,
        ):
            lines = list(stream_subprocess(["echo", "test"]))

        assert lines == ["line1", "line2", "line3"]

    def test_stream_subprocess_returns_command_result(self) -> None:
        """StreamResult.result has correct return_code after iteration."""
        mock_proc = MagicMock()
        mock_proc.stdout = iter(["output\n"])
        mock_proc.stderr = MagicMock()
        mock_proc.stderr.read.return_value = ""
        mock_proc.wait.return_value = 0
        mock_proc.returncode = 0
        mock_proc.pid = 456
        mock_proc.poll.return_value = 0

        with patch(
            "mcp_coder.utils.subprocess_streaming.subprocess.Popen",
            return_value=mock_proc,
        ):
            stream = StreamResult(stream_subprocess(["echo", "test"]))
            for _ in stream:
                pass
            result = stream.result

        assert isinstance(result, CommandResult)
        assert result.return_code == 0  # pylint: disable=no-member
        assert result.runner_type == "subprocess"  # pylint: disable=no-member

    def test_stream_subprocess_captures_stderr(self) -> None:
        """stderr is captured in the final CommandResult."""
        mock_proc = MagicMock()
        mock_proc.stdout = iter(["out\n"])
        mock_proc.stderr = MagicMock()
        mock_proc.stderr.read.return_value = "some error output"
        mock_proc.wait.return_value = 1
        mock_proc.returncode = 1
        mock_proc.pid = 789
        mock_proc.poll.return_value = 1

        with patch(
            "mcp_coder.utils.subprocess_streaming.subprocess.Popen",
            return_value=mock_proc,
        ):
            stream = StreamResult(stream_subprocess(["failing_cmd"]))
            for _ in stream:
                pass
            result = stream.result

        assert result.stderr == "some error output"  # pylint: disable=no-member
        assert result.return_code == 1  # pylint: disable=no-member

    def test_stream_subprocess_timeout(self) -> None:
        """Timed-out process sets timed_out=True in result."""
        mock_proc = MagicMock()
        # Simulate a blocking read that gets interrupted when process is killed
        mock_proc.stdout = iter([])  # No output before timeout
        mock_proc.stderr = MagicMock()
        mock_proc.stderr.read.return_value = ""
        mock_proc.wait.return_value = -9
        mock_proc.returncode = -9
        mock_proc.pid = 999
        mock_proc.poll.return_value = -9
        mock_proc.kill.return_value = None

        # Patch Timer to call the callback immediately
        def instant_timer(
            _interval: float, function: object, args: object = None
        ) -> MagicMock:
            """Timer that fires the callback immediately on start."""
            timer = MagicMock()

            def start() -> None:
                if callable(function):
                    function()

            timer.start = start
            timer.cancel = MagicMock()
            return timer

        with (
            patch(
                "mcp_coder.utils.subprocess_streaming.subprocess.Popen",
                return_value=mock_proc,
            ),
            patch(
                "mcp_coder.utils.subprocess_streaming.threading.Timer",
                side_effect=instant_timer,
            ),
        ):
            stream = StreamResult(
                stream_subprocess(["sleep", "999"], CommandOptions(timeout_seconds=1))
            )
            for _ in stream:
                pass
            result = stream.result

        assert result.timed_out is True  # pylint: disable=no-member

    def test_stream_subprocess_none_command_raises(self) -> None:
        """TypeError raised when command is None."""
        with pytest.raises(TypeError, match="Command cannot be None"):
            list(stream_subprocess(None))  # type: ignore[arg-type]

    def test_stream_subprocess_env_setup(self) -> None:
        """Python commands get isolation env variables."""
        import sys

        captured_kwargs: dict[str, object] = {}
        mock_proc = MagicMock()
        mock_proc.stdout = iter([])
        mock_proc.stderr = MagicMock()
        mock_proc.stderr.read.return_value = ""
        mock_proc.wait.return_value = 0
        mock_proc.returncode = 0
        mock_proc.pid = 100
        mock_proc.poll.return_value = 0

        def mock_popen(cmd: list[str], **kwargs: object) -> MagicMock:
            captured_kwargs.update(kwargs)
            return mock_proc

        with patch(
            "mcp_coder.utils.subprocess_streaming.subprocess.Popen",
            side_effect=mock_popen,
        ):
            list(stream_subprocess([sys.executable, "-c", "print('hi')"]))

        env = captured_kwargs.get("env", {})
        assert isinstance(env, dict)
        assert env.get("PYTHONUNBUFFERED") == "1"


class TestStreamResult:
    """Test StreamResult wrapper class."""

    def test_stream_result_wrapper_iteration(self) -> None:
        """StreamResult correctly wraps generator and collects lines."""
        mock_proc = MagicMock()
        mock_proc.stdout = iter(["a\n", "b\n"])
        mock_proc.stderr = MagicMock()
        mock_proc.stderr.read.return_value = ""
        mock_proc.wait.return_value = 0
        mock_proc.returncode = 0
        mock_proc.pid = 200
        mock_proc.poll.return_value = 0

        with patch(
            "mcp_coder.utils.subprocess_streaming.subprocess.Popen",
            return_value=mock_proc,
        ):
            stream = StreamResult(stream_subprocess(["echo", "test"]))
            lines = []
            for line in stream:
                lines.append(line)

        assert lines == ["a", "b"]
        assert stream.result.return_code == 0  # pylint: disable=no-member

    def test_stream_result_accessed_before_iteration_raises(self) -> None:
        """RuntimeError raised when result accessed before iteration completes."""
        mock_proc = MagicMock()
        mock_proc.stdout = iter(["a\n"])
        mock_proc.stderr = MagicMock()
        mock_proc.stderr.read.return_value = ""
        mock_proc.wait.return_value = 0
        mock_proc.returncode = 0
        mock_proc.pid = 300
        mock_proc.poll.return_value = 0

        with patch(
            "mcp_coder.utils.subprocess_streaming.subprocess.Popen",
            return_value=mock_proc,
        ):
            stream = StreamResult(stream_subprocess(["echo", "test"]))
            with pytest.raises(RuntimeError, match="not yet available"):
                _ = stream.result


class TestCommandOptionsEnvRemove:
    """Test env_remove field on CommandOptions."""

    def test_command_options_env_remove_default_none(self) -> None:
        """env_remove defaults to None."""
        opts = CommandOptions()
        assert opts.env_remove is None


class TestPrepareEnv:
    """Test prepare_env helper function."""

    def test_prepare_env_python_command_uses_isolation_env(self) -> None:
        """Python command gets PYTHONUNBUFFERED=1 etc."""
        result = prepare_env([sys.executable, "-c", "pass"], env=None, env_remove=None)
        assert result["PYTHONUNBUFFERED"] == "1"
        assert result["PYTHONDONTWRITEBYTECODE"] == "1"

    def test_prepare_env_non_python_command_uses_utf8_env(self) -> None:
        """Non-Python command gets UTF-8 env, not isolation env."""
        with patch.dict(os.environ, {}, clear=False):
            # Ensure isolation-specific key is absent from parent env
            os.environ.pop("PYTHONHASHSEED", None)
            result = prepare_env(["echo", "hello"], env=None, env_remove=None)
        assert result["PYTHONIOENCODING"] == "utf-8"
        # PYTHONHASHSEED="0" is only set by isolation env, not utf8 env
        assert result.get("PYTHONHASHSEED") != "0"

    def test_prepare_env_string_command_treated_as_non_python(self) -> None:
        """String command uses utf8 env, not isolation env."""
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("PYTHONHASHSEED", None)
            result = prepare_env("python -c pass", env=None, env_remove=None)
        assert result["PYTHONIOENCODING"] == "utf-8"
        # PYTHONHASHSEED="0" is only set by isolation env
        assert result.get("PYTHONHASHSEED") != "0"

    def test_prepare_env_merges_caller_env(self) -> None:
        """env={"MY_VAR": "hello"} appears in result."""
        result = prepare_env(["echo", "test"], env={"MY_VAR": "hello"}, env_remove=None)
        assert result["MY_VAR"] == "hello"

    def test_prepare_env_caller_env_overrides_base(self) -> None:
        """Caller env takes precedence over base env."""
        result = prepare_env(
            ["echo", "test"],
            env={"PYTHONIOENCODING": "ascii"},
            env_remove=None,
        )
        assert result["PYTHONIOENCODING"] == "ascii"

    @pytest.mark.parametrize(
        "env_remove,key_present",
        [
            (["PYTHONIOENCODING"], False),  # existing key is removed
            (["NONEXISTENT_KEY_XYZ"], True),  # missing key doesn't error
        ],
        ids=["removes_existing_key", "ignores_missing_key"],
    )
    def test_prepare_env_env_remove(
        self, env_remove: list[str], key_present: bool
    ) -> None:
        """env_remove removes keys; ignores missing keys without error."""
        result = prepare_env(["echo", "test"], env=None, env_remove=env_remove)
        if not key_present:
            assert "PYTHONIOENCODING" not in result
        # No exception for missing keys — test passes if we get here

    def test_prepare_env_none_env_still_inherits_parent(self) -> None:
        """env=None still gets full parent env (the core bug scenario)."""
        result = prepare_env(["echo", "test"], env=None, env_remove=None)
        # PATH should always be inherited from parent environment
        assert "PATH" in result or "Path" in result  # Windows uses 'Path'


class TestPrepareEnvIntegration:
    """Integration test calling prepare_env with real os.environ."""

    def test_prepare_env_integration_real_env(self) -> None:
        """Validate core bug scenario: env inheritance + merge + remove."""
        result = prepare_env(
            ["echo", "test"],
            env={"CUSTOM_TEST_VAR": "custom_value"},
            env_remove=["CUSTOM_TEST_VAR_REMOVE"],
        )
        # Parent env inherited (PATH always present)
        assert "PATH" in result or "Path" in result
        # Caller-provided env vars are present
        assert result["CUSTOM_TEST_VAR"] == "custom_value"
        # env_remove keys are absent (even if they weren't present)
        assert "CUSTOM_TEST_VAR_REMOVE" not in result
