"""Streaming subprocess execution utilities.

This module provides streaming variants of subprocess execution that yield
output lines in real-time rather than buffering all output.

Extracted from subprocess_runner.py to keep file sizes manageable.
"""

import logging
import os
import subprocess
import threading
import time
from collections.abc import Generator, Iterator

from .subprocess_runner import (
    CommandOptions,
    CommandResult,
    prepare_env,
)

logger = logging.getLogger(__name__)

__all__ = [
    "StreamResult",
    "stream_subprocess",
]


class StreamResult:
    """Wrapper that iterates stream lines and captures the final CommandResult.

    Usage:
        stream = StreamResult(stream_subprocess(command, options))
        for line in stream:
            process(line)
        result = stream.result  # CommandResult after iteration

    Note: Accessing ``result`` before iteration completes raises RuntimeError.
    """

    def __init__(self, gen: Generator[str, None, CommandResult]) -> None:
        self._gen = gen
        self._result: CommandResult | None = None

    def __iter__(self) -> Iterator[str]:
        """Return the iterator object (self)."""
        return self

    def __next__(self) -> str:
        """Return the next line from the stream.

        Raises:
            StopIteration: When the underlying stream is exhausted and the
                final ``CommandResult`` has been captured.
        """
        try:
            return next(self._gen)
        except StopIteration as exc:
            self._result = exc.value
            raise

    @property
    def result(self) -> CommandResult:
        """Return the final CommandResult after iteration completes.

        Returns:
            The CommandResult captured when the generator finished.

        Raises:
            RuntimeError: If iteration has not yet completed.
        """
        if self._result is None:
            raise RuntimeError("Result is not yet available; iterate fully first.")
        return self._result


def stream_subprocess(
    command: list[str],
    options: CommandOptions | None = None,
) -> Generator[str, None, CommandResult]:
    """Execute a command and yield stdout lines as they arrive.

    Unlike execute_subprocess() which buffers all output, this generator
    yields each line of stdout in real-time. After iteration completes,
    the final CommandResult is available via the generator's return value
    (accessible via StopIteration.value or a StreamResult wrapper).

    Args:
        command: Command and arguments as a list
        options: Execution options (timeout, env, cwd, etc.)

    Returns:
        CommandResult with final execution details (via generator return)

    Yields:
        Individual lines from stdout (without trailing newline)

    Raises:
        TypeError: If command is None.
    """
    if command is None:
        raise TypeError("Command cannot be None")

    if options is None:
        options = CommandOptions()

    start_time = time.time()

    env = prepare_env(command, options.env, options.env_remove)

    start_new_session = os.name != "nt"

    timed_out = False

    stdin_mode = subprocess.PIPE if options.input_data else subprocess.DEVNULL

    proc = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        stdin=stdin_mode,
        cwd=options.cwd,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        start_new_session=start_new_session,
    )

    # Write input data and close stdin before reading stdout
    if options.input_data and proc.stdin:
        proc.stdin.write(options.input_data)
        proc.stdin.close()

    # Inactivity watchdog: resets on each yielded line, kills on silence.
    # Lock-free float access relies on CPython's GIL for atomicity
    # (single writer in main thread, single reader in watchdog thread).
    last_activity = time.time()
    stop_event = threading.Event()

    def _watchdog() -> None:
        nonlocal timed_out
        while not stop_event.wait(timeout=1):
            if time.time() - last_activity > options.timeout_seconds:
                timed_out = True
                try:
                    proc.kill()
                except OSError:
                    pass
                return

    watchdog_thread = threading.Thread(target=_watchdog, daemon=True)
    watchdog_thread.start()

    # Collect stderr in a background thread to avoid pipe-buffer deadlock
    stderr_chunks: list[str] = []

    def _read_stderr() -> None:
        if proc.stderr:
            stderr_chunks.append(proc.stderr.read())

    stderr_thread = threading.Thread(target=_read_stderr, daemon=True)
    stderr_thread.start()

    try:
        assert proc.stdout is not None  # guaranteed by stdout=PIPE  # noqa: S101
        for line in proc.stdout:
            last_activity = time.time()  # Reset inactivity timer
            yield line.rstrip("\n")
        proc.wait()
    except GeneratorExit:
        try:
            proc.kill()
        except OSError:
            pass
        proc.wait()
        raise
    finally:
        stop_event.set()
        watchdog_thread.join(timeout=5)
        stderr_thread.join(timeout=5)

    stderr = stderr_chunks[0] if stderr_chunks else ""
    execution_time_ms = int((time.time() - start_time) * 1000)

    return CommandResult(
        return_code=proc.returncode,
        stdout="",
        stderr=stderr,
        timed_out=timed_out,
        execution_error=(
            f"Process timed out after {options.timeout_seconds} seconds"
            if timed_out
            else None
        ),
        command=command,
        runner_type="subprocess",
        execution_time_ms=execution_time_ms,
    )
