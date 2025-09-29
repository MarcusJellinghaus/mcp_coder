"""
Subprocess execution utilities with MCP STDIO isolation support.

This module provides functions for executing command-line tools with proper
timeout handling and STDIO isolation for Python commands in MCP server contexts.

Code copied from p_config reference project: src/utils/subprocess_runner.py
"""

import logging
import os
import signal
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class CommandResult:
    """Represents the result of a command execution."""

    return_code: int
    stdout: str
    stderr: str
    timed_out: bool
    execution_error: str | None = None
    command: list[str] | None = field(default=None)
    runner_type: str | None = field(default=None)
    execution_time_ms: int | None = field(default=None)


@dataclass
class CommandOptions:
    """Configuration options for command execution.

    Attributes:
        cwd: Working directory for the subprocess
        timeout_seconds: Maximum time to wait for process completion
        env: Environment variables for the subprocess. May contain internal
             testing flags prefixed with underscore (e.g., _DISABLE_STDIO_ISOLATION)
             that should NEVER be used in production code.
        capture_output: Whether to capture stdout and stderr
        text: Whether to decode output as text
        check: Whether to raise exception on non-zero exit code
        shell: Whether to execute through shell
        input_data: Data to send to subprocess stdin

    Warning:
        Environment variables starting with underscore (_) are internal testing
        flags that bypass safety mechanisms. They must not be used in production.
    """

    cwd: str | None = None
    timeout_seconds: int = 120
    env: dict[str, str] | None = None
    capture_output: bool = True
    text: bool = True
    check: bool = False
    shell: bool = False
    input_data: str | None = None


def is_python_command(command: list[str]) -> bool:
    """Check if a command is a Python execution command."""
    if not command:
        return False

    executable = Path(command[0]).name.lower()
    return (
        executable in ["python", "python3", "python.exe", "python3.exe"]
        or command[0] == sys.executable
    )


def get_python_isolation_env() -> dict[str, str]:
    """Get environment variables for Python subprocess isolation."""
    env = os.environ.copy()

    # Python-specific settings to prevent MCP STDIO conflicts
    env.update(
        {
            "PYTHONUNBUFFERED": "1",
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONIOENCODING": "utf-8",
            "PYTHONNOUSERSITE": "1",
            "PYTHONHASHSEED": "0",
            "PYTHONSTARTUP": "",
        }
    )

    # Remove MCP-specific variables
    for var in ["MCP_STDIO_TRANSPORT", "MCP_SERVER_NAME", "MCP_CLIENT_PARAMS"]:
        env.pop(var, None)

    return env


def get_utf8_env() -> dict[str, str]:
    """Get environment variables for UTF-8 encoding support on all subprocess types."""
    env = os.environ.copy()

    # Set UTF-8 encoding for all subprocess types
    env.update(
        {
            "PYTHONIOENCODING": "utf-8",
            "PYTHONUTF8": "1",
        }
    )

    # On Windows, also set legacy encoding variables
    if os.name == "nt":
        env.update(
            {
                "PYTHONLEGACYWINDOWSFSENCODING": "utf-8",
            }
        )
    else:
        # On Unix systems, set locale for UTF-8
        env.update(
            {
                "LC_ALL": "C.UTF-8",
            }
        )

    return env


def _run_subprocess(
    command: list[str], options: CommandOptions, use_stdio_isolation: bool = False
) -> subprocess.CompletedProcess[str]:
    """
    Internal function to run subprocess with or without STDIO isolation.

    Args:
        command: Command to execute
        options: Execution options
        use_stdio_isolation: Whether to use file-based STDIO isolation

    Returns:
        CompletedProcess with execution results
    """
    # Track start time for timeout logging
    subprocess_start_time = time.time()
    # Prepare environment with UTF-8 encoding support
    if is_python_command(command):
        env = get_python_isolation_env()
        if options.env:
            env.update(options.env)
    else:
        # For non-Python commands, use UTF-8 environment
        env = get_utf8_env()
        if options.env:
            env.update(options.env)

    # Handle input data and stdin
    stdin_value = subprocess.DEVNULL if options.input_data is None else None

    # Use start_new_session for process isolation (thread-safe alternative to preexec_fn)
    start_new_session = os.name != "nt"  # True on Unix, False on Windows

    # Use file-based STDIO for Python commands if needed
    if use_stdio_isolation and options.capture_output:
        with tempfile.TemporaryDirectory() as temp_dir:
            stdout_file = Path(temp_dir) / "stdout.txt"
            stderr_file = Path(temp_dir) / "stderr.txt"

            process = None
            stdout_f = None
            stderr_f = None

            try:
                # Open files
                stdout_f = open(stdout_file, "w", encoding="utf-8")
                stderr_f = open(stderr_file, "w", encoding="utf-8")

                # Use Popen for better process control
                popen_proc = None
                try:
                    popen_proc = subprocess.Popen(
                        command,
                        stdout=stdout_f,
                        stderr=stderr_f,
                        stdin=(
                            stdin_value
                            if options.input_data is None
                            else subprocess.PIPE
                        ),
                        cwd=options.cwd,
                        text=options.text,
                        encoding="utf-8" if options.text else None,
                        errors="replace",  # Replace invalid characters instead of crashing
                        env=env,
                        shell=options.shell,
                        start_new_session=start_new_session,
                    )

                    # Communicate with timeout
                    try:
                        _, _ = popen_proc.communicate(
                            input=options.input_data, timeout=options.timeout_seconds
                        )
                        process = subprocess.CompletedProcess(
                            args=command,
                            returncode=popen_proc.returncode,
                            stdout="",  # Will be read from file
                            stderr="",  # Will be read from file
                        )
                    except subprocess.TimeoutExpired:
                        # Kill the process and all children
                        if popen_proc:
                            elapsed_time = time.time() - subprocess_start_time
                            cmd_display = " ".join(command[:3]) + (
                                "..." if len(command) > 3 else ""
                            )
                            logger.warning(
                                f"Killing timed out process (STDIO isolation, PID: {popen_proc.pid}): "
                                f"command='{cmd_display}', timeout={options.timeout_seconds}s, "
                                f"elapsed={elapsed_time:.1f}s, cwd='{options.cwd or 'current'}'"
                            )

                            # On Windows, use taskkill to kill process tree
                            if os.name == "nt":
                                try:
                                    # Kill process tree on Windows
                                    subprocess.run(
                                        [
                                            "taskkill",
                                            "/F",
                                            "/T",
                                            "/PID",
                                            str(popen_proc.pid),
                                        ],
                                        capture_output=True,
                                        timeout=5,
                                        check=False,
                                    )
                                except (
                                    subprocess.SubprocessError,
                                    subprocess.TimeoutExpired,
                                    OSError,
                                ) as e:
                                    logger.debug(
                                        f"Taskkill failed, using fallback: {e}"
                                    )
                                    popen_proc.terminate()
                                    time.sleep(0.5)
                                    if popen_proc.poll() is None:
                                        popen_proc.kill()
                            else:
                                # On Unix, kill the process group
                                try:
                                    if (
                                        hasattr(os, "killpg")
                                        and hasattr(os, "getpgid")
                                        and hasattr(signal, "SIGTERM")
                                        and hasattr(signal, "SIGKILL")
                                    ):
                                        # Type ignore needed because mypy doesn't understand hasattr checks on some platforms
                                        os.killpg(  # type: ignore[attr-defined,unused-ignore]
                                            os.getpgid(popen_proc.pid), signal.SIGTERM  # type: ignore[attr-defined,unused-ignore]
                                        )
                                        time.sleep(0.5)
                                        if popen_proc.poll() is None:
                                            os.killpg(  # type: ignore[attr-defined,unused-ignore]
                                                os.getpgid(popen_proc.pid),  # type: ignore[attr-defined,unused-ignore]
                                                signal.SIGKILL,  # type: ignore[attr-defined,unused-ignore]
                                            )
                                    else:
                                        popen_proc.terminate()
                                        time.sleep(0.5)
                                        if popen_proc.poll() is None:
                                            popen_proc.kill()
                                except (
                                    OSError,
                                    ProcessLookupError,
                                    AttributeError,
                                ) as e:
                                    logger.debug(
                                        f"Process group kill failed, using fallback: {e}"
                                    )
                                    popen_proc.terminate()
                                    time.sleep(0.5)
                                    if popen_proc.poll() is None:
                                        popen_proc.kill()

                            # Wait a bit for cleanup
                            try:
                                popen_proc.wait(timeout=2)
                            except subprocess.TimeoutExpired:
                                pass

                        # Re-raise the timeout exception
                        raise

                except subprocess.TimeoutExpired:
                    # Close files before re-raising to prevent Windows file locking
                    # This cleanup is necessary before re-raising the timeout exception
                    if stdout_f:
                        stdout_f.flush()
                        stdout_f.close()
                    if stderr_f:
                        stderr_f.flush()
                        stderr_f.close()

                    # On Windows, add a small delay to help with file handle cleanup
                    if os.name == "nt":
                        time.sleep(0.1)

                    # Re-raise to be handled by the caller
                    raise  # pylint: disable=try-except-raise
                finally:
                    # Ensure files are closed
                    if stdout_f and not stdout_f.closed:
                        stdout_f.close()
                    if stderr_f and not stderr_f.closed:
                        stderr_f.close()
            except Exception:
                # Let any other exceptions propagate after cleanup in finally block
                raise  # pylint: disable=try-except-raise

            # Read output files after process completes
            # Use a small delay on Windows to avoid file locking issues
            if os.name == "nt":
                time.sleep(0.2)

            # Read output files, handling potential errors
            stdout = ""
            stderr = ""

            try:
                if stdout_file.exists():
                    stdout = stdout_file.read_text(encoding="utf-8")
            except (OSError, PermissionError) as exc:
                logger.debug(f"Could not read stdout file: {exc}")

            try:
                if stderr_file.exists():
                    stderr = stderr_file.read_text(encoding="utf-8")
            except (OSError, PermissionError) as exc:
                logger.debug(f"Could not read stderr file: {exc}")

            # Update the process with the actual output read from files
            return subprocess.CompletedProcess(
                args=command,
                returncode=process.returncode if process else 1,
                stdout=stdout,
                stderr=stderr,
            )
    else:
        # Regular execution with better process cleanup
        popen_proc = None
        try:
            if options.capture_output:
                popen_proc = subprocess.Popen(
                    command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    stdin=(
                        stdin_value if options.input_data is None else subprocess.PIPE
                    ),
                    cwd=options.cwd,
                    text=options.text,
                    encoding="utf-8" if options.text else None,
                    errors="replace",  # Replace invalid characters instead of crashing
                    env=env,
                    shell=options.shell,
                    start_new_session=start_new_session,
                )

                try:
                    stdout, stderr = popen_proc.communicate(
                        input=options.input_data, timeout=options.timeout_seconds
                    )
                    return subprocess.CompletedProcess(
                        args=command,
                        returncode=popen_proc.returncode,
                        stdout=stdout or "",
                        stderr=stderr or "",
                    )
                except subprocess.TimeoutExpired:
                    # Kill the process tree on timeout
                    if popen_proc:
                        elapsed_time = time.time() - subprocess_start_time
                        cmd_display = " ".join(command[:3]) + (
                            "..." if len(command) > 3 else ""
                        )
                        logger.warning(
                            f"Killing timed out process (regular execution, PID: {popen_proc.pid}): "
                            f"command='{cmd_display}', timeout={options.timeout_seconds}s, "
                            f"elapsed={elapsed_time:.1f}s, cwd='{options.cwd or 'current'}'"
                        )

                        if os.name == "nt":
                            # Windows: Kill process tree
                            try:
                                subprocess.run(
                                    [
                                        "taskkill",
                                        "/F",
                                        "/T",
                                        "/PID",
                                        str(popen_proc.pid),
                                    ],
                                    capture_output=True,
                                    timeout=5,
                                    check=False,
                                )
                            except (
                                subprocess.SubprocessError,
                                subprocess.TimeoutExpired,
                                OSError,
                            ) as e:
                                logger.debug(
                                    f"Taskkill failed in regular execution: {e}"
                                )
                                popen_proc.kill()
                        else:
                            # Unix: Kill process group
                            try:
                                if (
                                    hasattr(os, "killpg")
                                    and hasattr(os, "getpgid")
                                    and hasattr(signal, "SIGTERM")
                                    and hasattr(signal, "SIGKILL")
                                ):
                                    # Type ignore needed because mypy doesn't understand hasattr checks on some platforms
                                    os.killpg(  # type: ignore[attr-defined,unused-ignore]
                                        os.getpgid(popen_proc.pid), signal.SIGTERM  # type: ignore[attr-defined,unused-ignore]
                                    )
                                    time.sleep(0.5)
                                    if popen_proc.poll() is None:
                                        os.killpg(  # type: ignore[attr-defined,unused-ignore]
                                            os.getpgid(popen_proc.pid), signal.SIGKILL  # type: ignore[attr-defined,unused-ignore]
                                        )
                                else:
                                    popen_proc.kill()
                            except (OSError, ProcessLookupError, AttributeError) as e:
                                logger.debug(
                                    f"Process group kill failed in regular execution: {e}"
                                )
                                popen_proc.kill()

                        # Wait for cleanup
                        try:
                            popen_proc.wait(timeout=2)
                        except subprocess.TimeoutExpired:
                            pass
                    raise
            else:
                # No output capture needed
                return subprocess.run(
                    command,
                    capture_output=False,
                    cwd=options.cwd,
                    text=options.text,
                    encoding="utf-8" if options.text else None,
                    errors="replace",  # Replace invalid characters instead of crashing
                    timeout=options.timeout_seconds,
                    env=env,
                    shell=options.shell,
                    stdin=stdin_value,
                    input=options.input_data,
                    start_new_session=start_new_session,
                    check=False,
                )
        except subprocess.TimeoutExpired:
            raise  # pylint: disable=try-except-raise  # Re-raise for handling in execute_subprocess
        except Exception:
            # Re-raise any other exceptions (this catch-all is needed for cleanup)
            raise  # pylint: disable=try-except-raise


def execute_subprocess(
    command: list[str], options: CommandOptions | None = None
) -> CommandResult:
    """
    Execute a command with automatic STDIO isolation for Python commands.

    Args:
        command: Command and arguments as a list
        options: Execution options

    Returns:
        CommandResult with execution details
    """
    if command is None:
        raise TypeError("Command cannot be None")

    if options is None:
        options = CommandOptions()

    start_time = time.time()

    # Determine if we need STDIO isolation
    disable_isolation = (
        options.env and options.env.get("_DISABLE_STDIO_ISOLATION") == "1"
    )
    use_isolation = is_python_command(command) and not disable_isolation

    logger.debug(f"Starting subprocess execution: {command[:3] if command else None}")

    try:
        process = _run_subprocess(command, options, use_isolation)

        # Handle check parameter
        if options.check and process.returncode != 0:
            raise subprocess.CalledProcessError(
                process.returncode, command, process.stdout, process.stderr
            )

        execution_time_ms = int((time.time() - start_time) * 1000)

        return CommandResult(
            return_code=process.returncode,
            stdout=process.stdout or "",
            stderr=process.stderr or "",
            timed_out=False,
            command=command,
            runner_type="subprocess",
            execution_time_ms=execution_time_ms,
        )

    except subprocess.TimeoutExpired:
        execution_time_ms = int((time.time() - start_time) * 1000)
        return CommandResult(
            return_code=1,
            stdout="",
            stderr="",
            timed_out=True,
            execution_error=f"Process timed out after {options.timeout_seconds} seconds",
            command=command,
            runner_type="subprocess",
            execution_time_ms=execution_time_ms,
        )

    except subprocess.CalledProcessError as e:
        if options.check:
            raise
        execution_time_ms = int((time.time() - start_time) * 1000)
        return CommandResult(
            return_code=e.returncode,
            stdout=getattr(e, "stdout", "") or "",
            stderr=getattr(e, "stderr", "") or "",
            timed_out=False,
            command=command,
            runner_type="subprocess",
            execution_time_ms=execution_time_ms,
        )

    except (FileNotFoundError, PermissionError, OSError) as e:
        # Handle file system and permission errors
        execution_time_ms = int((time.time() - start_time) * 1000)
        logger.error(f"Subprocess execution failed: {type(e).__name__}: {e}")
        return CommandResult(
            return_code=1,
            stdout="",
            stderr="",
            timed_out=False,
            execution_error=f"{type(e).__name__}: {e}",
            command=command,
            runner_type="subprocess",
            execution_time_ms=execution_time_ms,
        )


def execute_command(
    command: list[str],
    cwd: str | None = None,
    timeout_seconds: int = 120,
    env: dict[str, str] | None = None,
) -> CommandResult:
    """
    Execute a command with automatic STDIO isolation for Python commands.

    Args:
        command: Complete command as list (e.g., ["python", "-m", "pylint", "src"])
        cwd: Working directory for subprocess
        timeout_seconds: Timeout in seconds
        env: Optional environment variables

    Returns:
        CommandResult with execution details and output
    """
    options = CommandOptions(
        cwd=cwd,
        timeout_seconds=timeout_seconds,
        env=env,
    )
    return execute_subprocess(command, options)
