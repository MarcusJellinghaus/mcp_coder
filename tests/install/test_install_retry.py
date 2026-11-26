"""Unit tests for the stderr capture helper and the retry loop in ``install._env``.

The capture-path tests run real child processes (small Python scripts written
to ``tmp_path``), so the pipe, the relay and the reader thread are exercised
as in production. ``sys.stderr`` is replaced by an in-memory text wrapper so
the relayed bytes can be read back.
"""

from __future__ import annotations

import contextlib
import io
import os
import signal
import subprocess
import sys
import threading
import time
from collections.abc import Callable
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from mcp_coder.install import _env
from mcp_coder.install._env import UV_TRANSIENT_SIGNATURES, run
from mcp_coder.utils.log_utils import OUTPUT

PYPI_ERROR = (
    "error: Failed to fetch: `https://pypi.org/simple/flask-cors/`\n"
    "  Caused by: connection error\n"
    "  Caused by: stream closed because of a broken pipe\n"
)
CACHE_ERROR = (
    "error: Failed to write to the client cache\n"
    "  Caused by: Failed to persist temporary file to "
    "C:\\Users\\builder\\AppData\\Local\\uv\\cache\\simple-v14\\pypi\\starlette.rkyv: "
    "Access is denied. (os error 5)\n"
)
OTHER_ERROR = "error: No solution found when resolving dependencies\n"

SUCCESS_LINE = "--- uv retry succeeded"


def _retry_line(sig_id: str) -> str:
    return f"--- uv failed with a transient error ({sig_id}); retrying once in 10 s"


_SCRIPTED_CHILD = """\
import sys
from pathlib import Path

ATTEMPTS = {attempts!r}
counter = Path(sys.argv[1])
index = int(counter.read_text()) if counter.exists() else 0
counter.write_text(str(index + 1))
code, text = ATTEMPTS[index]
sys.stderr.buffer.write(text.encode("utf-8"))
sys.stderr.buffer.flush()
sys.exit(code)
"""


def _scripted_child(tmp_path: Path, attempts: list[tuple[int, str]]) -> list[str]:
    """Command for a child that plays ``attempts[i]`` on its i-th invocation."""
    script = tmp_path / "scripted_child.py"
    script.write_text(_SCRIPTED_CHILD.format(attempts=attempts), encoding="utf-8")
    return [sys.executable, str(script), str(tmp_path / "counter.txt")]


def _attempt_count(tmp_path: Path) -> int:
    return int((tmp_path / "counter.txt").read_text())


def _child(tmp_path: Path, body: str) -> list[str]:
    """Command for a child running the given Python source."""
    script = tmp_path / "child.py"
    script.write_text(body, encoding="utf-8")
    return [sys.executable, str(script)]


def _messages(caplog: pytest.LogCaptureFixture) -> list[str]:
    return [r.getMessage() for r in caplog.records]


def _assert_no_jenkins_markers(caplog: pytest.LogCaptureFixture) -> None:
    for message in _messages(caplog):
        assert "WARNING" not in message
        assert "ERROR:" not in message


def _recording_threads(monkeypatch: pytest.MonkeyPatch) -> list[threading.Thread]:
    """Record every stderr reader thread ``_env`` starts."""
    recorded: list[threading.Thread] = []
    real_thread = threading.Thread

    class Recording(real_thread):  # type: ignore[valid-type,misc]
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            super().__init__(*args, **kwargs)
            if kwargs.get("target") is _env._drain_stderr:
                recorded.append(self)

    monkeypatch.setattr(threading, "Thread", Recording)
    return recorded


@pytest.fixture(autouse=True)
def sleeps(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> list[float]:
    """Record retry delays instead of sleeping; capture install log output."""
    recorded: list[float] = []
    # time.sleep is shared with rmtree_with_retry; monkeypatch restores it.
    monkeypatch.setattr(time, "sleep", recorded.append)
    caplog.set_level(OUTPUT, logger="mcp_coder.install")
    return recorded


def _relay(monkeypatch: pytest.MonkeyPatch) -> io.BytesIO:
    """Replace ``sys.stderr``; return the byte buffer the relay writes to.

    Must be called from the test body, not a fixture: pytest's global
    capture reinstalls its own ``sys.stderr`` between setup and call.
    """
    buffer = io.BytesIO()
    monkeypatch.setattr(sys, "stderr", io.TextIOWrapper(buffer, encoding="utf-8"))
    return buffer


def _capture(monkeypatch: pytest.MonkeyPatch) -> io.BytesIO:
    """Force the capture path; return the relay buffer (call from the test body)."""
    monkeypatch.setattr(_env, "_can_capture_stderr", lambda: True)
    return _relay(monkeypatch)


class TestRetryLoop:
    """``run(retry_on=...)`` retries once on a matched transient signature."""

    @pytest.mark.parametrize(
        ("sig_id", "text"),
        [
            ("ENV-PYPI-NETWORK", PYPI_ERROR),
            ("ENV-UV-ACCESS-DENIED-CACHE", CACHE_ERROR),
        ],
    )
    def test_transient_error_retries_once_then_succeeds(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        sleeps: list[float],
        caplog: pytest.LogCaptureFixture,
        sig_id: str,
        text: str,
    ) -> None:
        capture = _capture(monkeypatch)
        cmd = _scripted_child(tmp_path, [(2, text), (0, "")])

        assert run(cmd, retry_on=UV_TRANSIENT_SIGNATURES) == 0

        assert sleeps == [10]
        messages = _messages(caplog)
        assert messages.count(_retry_line(sig_id)) == 1
        assert messages.count(SUCCESS_LINE) == 1
        assert len([m for m in messages if m.startswith("> ")]) == 1
        _assert_no_jenkins_markers(caplog)
        assert _attempt_count(tmp_path) == 2
        assert capture.getvalue().decode("utf-8") == text

    def test_two_transient_failures_exit_with_uv_code(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        sleeps: list[float],
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        _capture(monkeypatch)
        cmd = _scripted_child(tmp_path, [(2, PYPI_ERROR)] * 2)

        with pytest.raises(SystemExit) as exc_info:
            run(cmd, retry_on=UV_TRANSIENT_SIGNATURES)

        assert exc_info.value.code == 2
        assert sleeps == [10]
        messages = _messages(caplog)
        assert messages.count(_retry_line("ENV-PYPI-NETWORK")) == 1
        assert SUCCESS_LINE not in messages
        assert _attempt_count(tmp_path) == 2
        _assert_no_jenkins_markers(caplog)

    def test_other_error_is_not_retried(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        sleeps: list[float],
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        _capture(monkeypatch)
        cmd = _scripted_child(tmp_path, [(1, OTHER_ERROR)])

        with pytest.raises(SystemExit) as exc_info:
            run(cmd, retry_on=UV_TRANSIENT_SIGNATURES)

        assert exc_info.value.code == 1
        assert not sleeps
        assert _attempt_count(tmp_path) == 1
        assert not [m for m in _messages(caplog) if "transient error" in m]

    def test_partial_cache_signature_is_not_retried(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        sleeps: list[float],
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        _capture(monkeypatch)
        cmd = _scripted_child(tmp_path, [(2, "Access is denied. (os error 5)\n")])

        with pytest.raises(SystemExit) as exc_info:
            run(cmd, retry_on=UV_TRANSIENT_SIGNATURES)

        assert exc_info.value.code == 2
        assert not sleeps
        assert _attempt_count(tmp_path) == 1
        assert not [m for m in _messages(caplog) if "transient error" in m]

    @pytest.mark.parametrize(
        "sig_id", ["ENV-PYPI-NETWORK", "ENV-UV-ACCESS-DENIED-CACHE"]
    )
    def test_retry_line_does_not_match_signatures(self, sig_id: str) -> None:
        assert (
            _env._match_signature(_retry_line(sig_id), UV_TRANSIENT_SIGNATURES) is None
        )
        assert _env._match_signature(SUCCESS_LINE, UV_TRANSIENT_SIGNATURES) is None


class TestPathSelection:
    """Without ``retry_on`` or a capturable stderr, ``run()`` is unchanged."""

    @staticmethod
    def _recorder(
        returncode: int,
    ) -> tuple[list[tuple[tuple[Any, ...], dict[str, Any]]], Callable[..., Any]]:
        calls: list[tuple[tuple[Any, ...], dict[str, Any]]] = []

        def fake_run(*args: Any, **kwargs: Any) -> SimpleNamespace:
            calls.append((args, kwargs))
            return SimpleNamespace(returncode=returncode)

        return calls, fake_run

    def test_empty_retry_on_keeps_subprocess_run(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(_env, "_can_capture_stderr", lambda: True)
        calls, fake_run = self._recorder(0)
        monkeypatch.setattr(subprocess, "run", fake_run)
        cmd = ["uv", "pip", "install", "x"]

        assert run(cmd, cwd=tmp_path) == 0

        assert calls == [((cmd,), {"cwd": tmp_path, "check": False})]

    def test_no_capture_keeps_subprocess_run_and_no_retry(
        self, monkeypatch: pytest.MonkeyPatch, sleeps: list[float]
    ) -> None:
        monkeypatch.setattr(_env, "_can_capture_stderr", lambda: False)
        calls, fake_run = self._recorder(1)
        monkeypatch.setattr(subprocess, "run", fake_run)
        cmd = ["uv", "pip", "install", "x"]

        with pytest.raises(SystemExit) as exc_info:
            run(cmd, retry_on=UV_TRANSIENT_SIGNATURES)

        assert exc_info.value.code == 1
        assert calls == [((cmd,), {"cwd": None, "check": False})]
        assert not sleeps


class _TtyWrapper(io.TextIOWrapper):
    def isatty(self) -> bool:
        return True


@pytest.mark.parametrize(
    ("make_stream", "expected"),
    [
        (lambda: None, False),
        (io.StringIO, False),
        (lambda: _TtyWrapper(io.BytesIO()), False),
        (lambda: io.TextIOWrapper(io.BytesIO()), True),
    ],
    ids=["none", "no-buffer", "tty", "pipe"],
)
def test_can_capture_stderr(
    monkeypatch: pytest.MonkeyPatch,
    make_stream: Callable[[], Any],
    expected: bool,
) -> None:
    monkeypatch.setattr(sys, "stderr", make_stream())
    assert _env._can_capture_stderr() is expected


class TestCapture:
    """The pipe, relay and reader thread behind ``_run_capturing``."""

    def test_relay_is_byte_exact(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        capture = _capture(monkeypatch)
        cmd = _child(
            tmp_path,
            "import sys\n"
            "sys.stderr.buffer.write(b'50%\\r100%\\r\\n')\n"
            "sys.stderr.buffer.flush()\n",
        )

        assert run(cmd, retry_on=UV_TRANSIENT_SIGNATURES) == 0

        assert capture.getvalue() == b"50%\r100%\r\n"

    @pytest.mark.parametrize(
        ("error_first", "expected"),
        [(True, None), (False, "ENV-PYPI-NETWORK")],
        ids=["error-pushed-out-of-tail", "error-at-end"],
    )
    def test_tail_is_bounded(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        error_first: bool,
        expected: str | None,
    ) -> None:
        _relay(monkeypatch)
        filler = "x" * (200 * 1024)
        text = PYPI_ERROR + filler if error_first else filler + PYPI_ERROR
        cmd = _scripted_child(tmp_path, [(2, text)])

        assert _env._run_capturing(cmd, UV_TRANSIENT_SIGNATURES, None) == (2, expected)

    def test_grandchild_holding_stderr_does_not_block(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _capture(monkeypatch)
        monkeypatch.setattr(_env, "_READER_JOIN_TIMEOUT_SECONDS", 0.2)
        readers = _recording_threads(monkeypatch)
        pid_file = tmp_path / "grandchild.pid"
        # stderr=sys.stderr must be explicit: without any stdio argument,
        # Windows Popen (close_fds=True) passes no handles to the grandchild.
        # The 30 s sleep / 10 s budget leave room for slow process start-up
        # on a loaded machine; the grandchild is killed afterwards.
        cmd = _child(
            tmp_path,
            "import subprocess, sys\n"
            "grandchild = subprocess.Popen(\n"
            "    [sys.executable, '-c', 'import time; time.sleep(30)'],\n"
            "    stderr=sys.stderr,\n"
            ")\n"
            f"open({str(pid_file)!r}, 'w').write(str(grandchild.pid))\n",
        )

        try:
            start = time.monotonic()
            assert run(cmd, retry_on=UV_TRANSIENT_SIGNATURES) == 0
            elapsed = time.monotonic() - start

            assert len(readers) == 1
            assert readers[0].is_alive()
            assert elapsed < 10
        finally:
            if pid_file.exists():
                with contextlib.suppress(OSError):
                    os.kill(int(pid_file.read_text()), signal.SIGTERM)
            for reader in readers:
                reader.join(5)

    def test_relay_write_error_keeps_draining(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        class BrokenBuffer:
            def write(self, data: bytes) -> int:
                raise OSError("relay target gone")

            def flush(self) -> None:
                pass

        class BrokenStderr:
            buffer = BrokenBuffer()

            def write(self, text: str) -> int:
                return len(text)

            def flush(self) -> None:
                pass

            def isatty(self) -> bool:
                return False

        monkeypatch.setattr(sys, "stderr", BrokenStderr())
        cmd = _child(
            tmp_path,
            "import sys\n"
            "sys.stderr.buffer.write(b'x' * (1024 * 1024))\n"
            "sys.stderr.buffer.flush()\n",
        )
        results: list[tuple[int, str | None]] = []
        worker = threading.Thread(
            target=lambda: results.append(
                _env._run_capturing(cmd, UV_TRANSIENT_SIGNATURES, None)
            ),
            daemon=True,
        )

        worker.start()
        worker.join(60)

        assert not worker.is_alive()
        assert results == [(0, None)]

    def test_wait_interrupt_kills_child(self, monkeypatch: pytest.MonkeyPatch) -> None:
        killed: list[bool] = []
        streams: list[Any] = []

        class FakePopen:
            def __init__(self, *_args: Any, **_kwargs: Any) -> None:
                read_fd, write_fd = os.pipe()
                os.close(write_fd)
                # Closed in the test's finally block, after the reader ends.
                self.stderr = open(  # noqa: SIM115  # pylint: disable=consider-using-with
                    read_fd, "rb"
                )
                streams.append(self.stderr)

            def wait(self) -> int:
                raise KeyboardInterrupt

            def kill(self) -> None:
                killed.append(True)

        readers = _recording_threads(monkeypatch)
        monkeypatch.setattr(subprocess, "Popen", FakePopen)

        try:
            with pytest.raises(KeyboardInterrupt):
                _env._run_capturing(["uv"], UV_TRANSIENT_SIGNATURES, None)
            assert killed == [True]
        finally:
            for reader in readers:
                reader.join(5)
            for stream in streams:
                stream.close()
