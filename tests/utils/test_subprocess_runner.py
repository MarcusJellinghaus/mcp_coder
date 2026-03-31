"""Test subprocess_runner module."""

import logging
import os
import sys
import threading
import time
from subprocess import CompletedProcess, TimeoutExpired
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.utils.subprocess_runner import (
    MAX_STDERR_IN_ERROR,
    CommandOptions,
    CommandResult,
    _run_heartbeat,
    check_tool_missing_error,
    execute_subprocess,
    launch_process,
    prepare_env,
    truncate_stderr,
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

    def test_launch_process_inherits_parent_env(self) -> None:
        """env=None still inherits parent env via prepare_env (core bug fix)."""
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
            launch_process(["echo", "hello"], env=None)

        env = captured_kwargs["env"]
        assert isinstance(env, dict)
        # Parent env should be inherited — PATH is always present
        assert "PATH" in env or "Path" in env

    def test_launch_process_merges_custom_env(self) -> None:
        """Custom env vars are merged on top of parent env."""
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
            launch_process(["echo", "hello"], env={"CUSTOM": "val"})

        env = captured_kwargs["env"]
        assert isinstance(env, dict)
        assert env["CUSTOM"] == "val"
        # Parent env should also be present
        assert "PATH" in env or "Path" in env

    def test_launch_process_env_remove(self) -> None:
        """env_remove excludes specified keys from the prepared env."""
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
            launch_process(
                ["echo", "hello"],
                env={"FOO": "bar", "KEEP": "yes"},
                env_remove=["FOO"],
            )

        env = captured_kwargs["env"]
        assert isinstance(env, dict)
        assert "FOO" not in env
        assert env["KEEP"] == "yes"


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
        kill_event = threading.Event()

        class _BlockingStdout:
            """Iterator that blocks until the process is killed."""

            def __iter__(self) -> "_BlockingStdout":
                return self

            def __next__(self) -> str:
                kill_event.wait()
                raise StopIteration

        mock_proc.stdout = _BlockingStdout()
        mock_proc.stderr = MagicMock()
        mock_proc.stderr.read.return_value = ""
        mock_proc.wait.return_value = -9
        mock_proc.returncode = -9
        mock_proc.pid = 999
        mock_proc.poll.return_value = -9
        mock_proc.kill.side_effect = kill_event.set

        with patch(
            "mcp_coder.utils.subprocess_streaming.subprocess.Popen",
            return_value=mock_proc,
        ):
            stream = StreamResult(
                stream_subprocess(["sleep", "999"], CommandOptions(timeout_seconds=0))
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


class TestRunSubprocessUsesPrepareEnv:
    """Test that _run_subprocess delegates env setup to prepare_env."""

    def test_run_subprocess_passes_env_remove_to_prepare_env(self) -> None:
        """_run_subprocess calls prepare_env with options.env_remove."""
        mock_proc = MagicMock()
        mock_proc.communicate.return_value = ("out", "err")
        mock_proc.returncode = 0
        mock_proc.pid = 42
        mock_proc.poll.return_value = 0

        options = CommandOptions(
            env={"MY": "val"},
            env_remove=["CLAUDECODE", "SECRET"],
        )

        with (
            patch(
                "mcp_coder.utils.subprocess_runner.prepare_env",
                return_value={"PATH": "/usr/bin"},
            ) as mock_prepare,
            patch(
                "mcp_coder.utils.subprocess_runner.subprocess.Popen",
                return_value=mock_proc,
            ),
        ):
            from mcp_coder.utils.subprocess_runner import _run_subprocess

            _run_subprocess(["echo", "hi"], options)

        mock_prepare.assert_called_once_with(
            ["echo", "hi"], {"MY": "val"}, ["CLAUDECODE", "SECRET"]
        )


class TestStreamSubprocessUsesPrepareEnv:
    """Test that stream_subprocess delegates env setup to prepare_env."""

    def test_stream_subprocess_passes_env_remove(self) -> None:
        """stream_subprocess calls prepare_env with options.env_remove."""
        mock_proc = MagicMock()
        mock_proc.stdout = iter([])
        mock_proc.stderr = MagicMock()
        mock_proc.stderr.read.return_value = ""
        mock_proc.wait.return_value = 0
        mock_proc.returncode = 0
        mock_proc.pid = 55
        mock_proc.poll.return_value = 0

        options = CommandOptions(
            env={"FOO": "bar"},
            env_remove=["CLAUDECODE"],
        )

        with (
            patch(
                "mcp_coder.utils.subprocess_streaming.prepare_env",
                return_value={"PATH": "/usr/bin"},
            ) as mock_prepare,
            patch(
                "mcp_coder.utils.subprocess_streaming.subprocess.Popen",
                return_value=mock_proc,
            ),
        ):
            list(stream_subprocess(["echo", "test"], options))

        mock_prepare.assert_called_once_with(
            ["echo", "test"], {"FOO": "bar"}, ["CLAUDECODE"]
        )


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


class TestMergedUtilities:
    """Test utility functions merged from p_tools reference project."""

    def test_check_tool_missing_error_detects_missing_module(self) -> None:
        """stderr containing 'No module named pytest' returns actionable message."""
        stderr = "No module named pytest"
        result = check_tool_missing_error(stderr, "pytest", "/usr/bin/python3")
        assert result is not None
        assert "pytest is not installed" in result
        assert "/usr/bin/python3" in result
        assert "--python-executable" in result

    def test_check_tool_missing_error_returns_none_for_other_errors(self) -> None:
        """stderr with unrelated error returns None."""
        stderr = "SyntaxError: invalid syntax"
        result = check_tool_missing_error(stderr, "pytest", "/usr/bin/python3")
        assert result is None

    @pytest.mark.parametrize(
        "input_str,max_len,expected",
        [
            ("short", 500, "short"),
            ("x" * 600, 500, "x" * 500 + "..."),
            ("hello world", 5, "hello..."),
        ],
        ids=[
            "short_string_unchanged",
            "long_string_truncated",
            "custom_max_len",
        ],
    )
    def test_truncate_stderr(self, input_str: str, max_len: int, expected: str) -> None:
        """Verify truncate_stderr with various inputs and max_len values."""
        assert truncate_stderr(input_str, max_len) == expected

    def test_max_stderr_in_error_constant(self) -> None:
        """Verify MAX_STDERR_IN_ERROR == 500."""
        assert MAX_STDERR_IN_ERROR == 500


class TestHeartbeat:
    """Test heartbeat functionality in execute_subprocess."""

    def test_no_heartbeat_by_default(self, caplog: pytest.LogCaptureFixture) -> None:
        """No heartbeat logs when params not provided."""
        with patch("mcp_coder.utils.subprocess_runner._run_subprocess") as mock_run:
            mock_run.return_value = CompletedProcess(
                args=["echo"], returncode=0, stdout="", stderr=""
            )
            with caplog.at_level(
                logging.INFO, logger="mcp_coder.utils.subprocess_runner"
            ):
                execute_subprocess(["echo", "hi"])
            heartbeat_logs = [
                r
                for r in caplog.records
                if "heartbeat" in r.message.lower() or "elapsed" in r.message.lower()
            ]
            assert len(heartbeat_logs) == 0

    def test_heartbeat_thread_started_and_stopped(self) -> None:
        """Heartbeat thread is started before subprocess and stopped after."""
        with patch("mcp_coder.utils.subprocess_runner._run_subprocess") as mock_run:
            mock_run.return_value = CompletedProcess(
                args=["echo"], returncode=0, stdout="", stderr=""
            )
            with patch("mcp_coder.utils.subprocess_runner.threading") as mock_threading:
                mock_event = MagicMock()
                mock_threading.Event.return_value = mock_event
                mock_thread = MagicMock()
                mock_threading.Thread.return_value = mock_thread

                execute_subprocess(
                    ["echo", "hi"],
                    heartbeat_interval_seconds=120,
                    heartbeat_message="Test heartbeat",
                )

                mock_threading.Thread.assert_called_once()
                mock_thread.start.assert_called_once()  # pylint: disable=no-member
                mock_event.set.assert_called_once()  # Stop signal sent
                mock_thread.join.assert_called_once()  # pylint: disable=no-member

    def test_heartbeat_stopped_on_exception(self) -> None:
        """Heartbeat thread is stopped even if subprocess raises."""
        with patch("mcp_coder.utils.subprocess_runner._run_subprocess") as mock_run:
            mock_run.side_effect = TimeoutExpired(["cmd"], 10)
            with patch("mcp_coder.utils.subprocess_runner.threading") as mock_threading:
                mock_event = MagicMock()
                mock_threading.Event.return_value = mock_event
                mock_thread = MagicMock()
                mock_threading.Thread.return_value = mock_thread

                result = execute_subprocess(
                    ["cmd"],
                    heartbeat_interval_seconds=60,
                    heartbeat_message="test",
                )

                assert result.timed_out is True
                mock_event.set.assert_called_once()  # Stopped despite exception

    def test_heartbeat_zero_interval_disabled(self) -> None:
        """heartbeat_interval_seconds=0 does not start a thread."""
        with patch("mcp_coder.utils.subprocess_runner._run_subprocess") as mock_run:
            mock_run.return_value = CompletedProcess(
                args=["echo"], returncode=0, stdout="", stderr=""
            )
            with patch("mcp_coder.utils.subprocess_runner.threading") as mock_threading:
                execute_subprocess(
                    ["echo"],
                    heartbeat_interval_seconds=0,
                    heartbeat_message="x",
                )
                mock_threading.Thread.assert_not_called()

    def test_run_heartbeat_logs_periodically(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """_run_heartbeat logs at intervals until stop event is set."""
        stop_event = MagicMock(spec=threading.Event)
        # First wait returns False (not stopped), second returns True (stopped)
        stop_event.wait.side_effect = [False, True]

        with caplog.at_level(logging.INFO, logger="mcp_coder.utils.subprocess_runner"):
            _run_heartbeat(
                stop_event, interval=120, message="Test HB", start_time=time.time()
            )

        assert any("Test HB" in record.message for record in caplog.records)
