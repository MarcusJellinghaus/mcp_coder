"""Environment helpers and the resolved configuration for ``mcp-coder install``.

Everything the install phases need that is not itself a phase: the module
constants, the frozen :class:`InstallConfig` built from parsed CLI arguments,
and the small subprocess / filesystem helpers.

Raw ``subprocess`` is deliberate here: the shared ``execute_command`` helper
captures output and times out, and ``stream_subprocess`` is line-based, which
mangles ``uv``'s carriage-return progress display. Commands normally run with
inherited stdio. When stderr is not a terminal and ``run()`` is given
``retry_on`` signatures, only stderr is piped: it is relayed byte for byte to
``sys.stderr.buffer`` and its tail is matched against the signatures.
"""

from __future__ import annotations

import argparse
import contextlib
import logging
import os
import re
import shutil
import stat
import subprocess
import sys
import threading
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import IO, Any

from ..utils.log_utils import OUTPUT
from ..utils.pyproject_config import get_install_extras, get_post_install_checks

logger = logging.getLogger(__name__)

MCP_CODER_REPO = "https://github.com/MarcusJellinghaus/mcp_coder.git"

# Reported after every install, never required: only projects that ask for a
# given binary pull it in, so a missing one is information, not a failure.
REPORT_BINARIES: tuple[str, ...] = (
    "mcp-coder",
    "mcp-tools-py",
    "mcp-workspace",
    "mcp-config",
)
# Library-only packages: no entry point, so `uv pip show` is the only probe.
REPORT_PACKAGES: tuple[str, ...] = ("mcp-coder-utils",)

# Used when neither --extras nor the [tool.mcp-coder.install] section in the
# pyproject.toml at --local-path declares anything. This is the only
# fallback site.
_DEFAULT_EXTRAS = "dev"

# (id, regexes): a signature matches when every regex is found in the text.
Signature = tuple[str, tuple[str, ...]]

# Transient uv failures worth one retry. Keep the regexes narrow: they must
# never match the retry log line, and any other error must fail at once.
UV_TRANSIENT_SIGNATURES: tuple[Signature, ...] = (
    ("ENV-PYPI-NETWORK", (r"Failed to fetch: `?https://pypi\.org",)),
    (
        "ENV-UV-ACCESS-DENIED-CACHE",
        (r"Failed to persist temporary file", r"Access is denied"),
    ),
)
_STDERR_TAIL_BYTES = 64 * 1024
_READ_CHUNK_BYTES = 64 * 1024
# A grandchild may inherit the stderr pipe and keep it open after the child
# exits; the reader is abandoned (daemon thread) after this long.
_READER_JOIN_TIMEOUT_SECONDS = 5.0
_UV_RETRY_DELAY_SECONDS = 10


@dataclass(frozen=True)
class InstallConfig:
    """Fully resolved inputs for one install run.

    ``local_path`` and ``extras`` are always resolved, so no phase ever sees
    a sentinel: ``local_path`` defaults to ``target`` and ``extras`` falls
    back to the declared policy in the pyproject.toml at ``local_path``,
    then to ``"dev"``.
    """

    target: Path
    source: str
    ref: str
    local_path: Path
    extras: str
    extra_packages: str
    use_sync: bool
    skip_overrides: bool
    refresh: bool
    clean: bool
    python: str
    check: bool
    post_install_checks: tuple[tuple[str, ...], ...]

    @classmethod
    def from_args(cls, args: argparse.Namespace) -> InstallConfig:
        """Resolve a parsed argument namespace into an InstallConfig.

        Args:
            args: Namespace produced by ``add_install_parser``.

        Returns:
            The resolved configuration.

        Raises:
            ValueError: If ``--source local`` was passed without
                ``--local-path``, if ``--use-sync`` was combined with a
                target that differs from ``--local-path``, if the target
                project's pyproject.toml exists but cannot be parsed, or if
                its ``post_install_checks`` value is malformed.
        """
        if args.source == "local" and args.local_path is None:
            raise ValueError("--source local requires --local-path")

        target = Path(args.target).resolve()
        local_path = Path(args.local_path or args.target).resolve()

        # `uv sync` writes its venv to `<cwd>/.venv`, where cwd is forced to
        # local_path (it needs that dir's pyproject.toml + uv.lock). So with
        # --use-sync, target MUST equal local_path; otherwise we'd provision
        # target/.venv in phase 1, then `uv sync` would silently create a
        # second venv at local_path/.venv and leave the original empty.
        if args.use_sync and local_path != target:
            raise ValueError(
                f"--use-sync requires target ({target}) to equal "
                f"--local-path ({local_path}). "
                "uv sync writes to <local-path>/.venv."
            )

        # Unconditional and strict: an explicit --extras overrides the value
        # but must not skip the read, so a malformed pyproject.toml aborts
        # here rather than being swallowed by the lax override reader later.
        declared = get_install_extras(local_path, strict=True)
        post_install_checks = get_post_install_checks(local_path, strict=True)
        if args.extras is not None:
            extras = str(args.extras)
        elif declared is not None:
            extras = declared
        else:
            extras = _DEFAULT_EXTRAS

        return cls(
            target=target,
            source=args.source,
            ref=args.ref,
            local_path=local_path,
            extras=extras,
            extra_packages=args.extra_packages,
            use_sync=args.use_sync,
            skip_overrides=args.skip_overrides,
            refresh=args.refresh,
            clean=args.clean,
            python=args.python,
            check=args.check,
            post_install_checks=post_install_checks,
        )


def venv_bin(venv: Path) -> Path:
    """Return the executable subdir of a venv (Scripts on NT, bin elsewhere)."""
    return venv / ("Scripts" if os.name == "nt" else "bin")


def exe(name: str) -> str:
    """Append the .exe suffix on Windows; pass-through on POSIX.

    Args:
        name: Bare executable name.

    Returns:
        The platform-appropriate executable file name.
    """
    return f"{name}.exe" if os.name == "nt" else name


def _can_capture_stderr() -> bool:
    """Return True when stderr can be piped and relayed without losing a TTY."""
    stream = sys.stderr
    return stream is not None and hasattr(stream, "buffer") and not stream.isatty()


def _match_signature(text: str, signatures: Sequence[Signature]) -> str | None:
    """Return the id of the first signature whose regexes all match ``text``."""
    for sig_id, regexes in signatures:
        if all(re.search(rx, text) for rx in regexes):
            return sig_id
    return None


def _drain_stderr(stream: IO[bytes], tail: bytearray) -> None:
    """Relay a child's stderr pipe to ``sys.stderr.buffer``, keeping a tail.

    Reads until EOF and never stops early on a relay error: a reader that
    stopped would let the pipe fill up and deadlock the child.
    """
    try:
        fd = stream.fileno()
    except (OSError, ValueError):
        return
    while True:
        try:
            chunk = os.read(fd, _READ_CHUNK_BYTES)
        except OSError:
            return
        if not chunk:
            return
        tail.extend(chunk)
        del tail[:-_STDERR_TAIL_BYTES]
        try:
            sys.stderr.flush()
            sys.stderr.buffer.write(chunk)
            sys.stderr.buffer.flush()
        except (OSError, ValueError, AttributeError):
            pass


def _run_capturing(
    command: list[str], signatures: Sequence[Signature], cwd: Path | None
) -> tuple[int, str | None]:
    """Run ``command`` with only stderr piped and match its tail.

    No ``with Popen`` and the pipe is never closed here: a grandchild that
    inherited the pipe would otherwise block the install until it exits.

    Returns:
        The exit code and the id of the matched signature, or None.
    """
    proc = subprocess.Popen(  # pylint: disable=consider-using-with
        command, cwd=cwd, stderr=subprocess.PIPE
    )
    assert proc.stderr is not None  # noqa: S101 -- stderr=PIPE always sets it
    tail = bytearray()
    reader = threading.Thread(
        target=_drain_stderr, args=(proc.stderr, tail), daemon=True
    )
    reader.start()
    try:
        returncode = proc.wait()
    except BaseException:
        proc.kill()
        raise
    reader.join(_READER_JOIN_TIMEOUT_SECONDS)
    text = bytes(tail).decode("utf-8", errors="replace")
    return returncode, _match_signature(text, signatures)


def run(
    cmd: list[str],
    *,
    check: bool = True,
    dry: bool = False,
    cwd: Path | None = None,
    retry_on: tuple[Signature, ...] = (),
) -> int:
    """Run a subprocess command, logging it first.

    Args:
        cmd: Command + arguments as a list (no shell interpolation).
        check: Exit the process on a non-zero return code when True.
        dry: Log only, don't execute. Wired to ``--check``.
        cwd: Working directory for the subprocess. Required for
            ``uv sync`` which reads pyproject.toml from cwd.
        retry_on: Signatures that allow one retry after
            ``_UV_RETRY_DELAY_SECONDS``; only used when stderr is not a
            terminal.

    Returns:
        Subprocess return code, or 0 when ``dry=True``.
    """
    pretty = " ".join(f'"{c}"' if " " in str(c) else str(c) for c in cmd)
    cwd_hint = f" (cwd={cwd})" if cwd else ""
    logger.log(OUTPUT, "> %s%s", pretty, cwd_hint)
    if dry:
        return 0
    if retry_on and _can_capture_stderr():
        returncode, hit = _run_capturing(cmd, retry_on, cwd)
        if returncode != 0 and hit:
            # Must never contain WARNING or ERROR: (Jenkins marks the build
            # UNSTABLE on those).
            logger.log(
                OUTPUT,
                "--- uv failed with a transient error (%s); retrying once in %d s",
                hit,
                _UV_RETRY_DELAY_SECONDS,
            )
            time.sleep(_UV_RETRY_DELAY_SECONDS)
            returncode, _ = _run_capturing(cmd, retry_on, cwd)
            if returncode == 0:
                logger.log(OUTPUT, "--- uv retry succeeded")
    else:
        # check=False is subprocess's own flag. This wrapper's `check` means
        # "exit the process on failure", handled below; forwarding it would
        # raise CalledProcessError instead and change behaviour.
        returncode = subprocess.run(cmd, cwd=cwd, check=False).returncode
    if check and returncode != 0:
        sys.exit(returncode)
    return returncode


def ensure_system_uv() -> str:
    """Locate system uv; auto-install via ``pip install uv`` if missing.

    Order of attempts:

    1. ``shutil.which("uv")`` — already on PATH, nothing to do.
    2. ``python -m pip install uv`` — try to install it. Lands in the
       active venv (if any) or the system Python — both of which put
       the resulting ``uv`` on PATH for the next lookup.
    3. ``shutil.which("uv")`` again — pick up the newly-installed uv.

    Exits the process with a message naming the manual fix when uv is
    neither on PATH nor installable (pip missing, or the install succeeded
    but the binary still cannot be located).

    Returns:
        Absolute path to a working uv binary.
    """
    uv_bin = shutil.which("uv")
    if uv_bin:
        return uv_bin

    logger.log(OUTPUT, "--- uv not on PATH; attempting `python -m pip install uv`")
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "uv"],
            check=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        sys.exit(
            f"mcp-coder install requires `uv` on PATH; auto-install via pip "
            f"failed ({exc}). Install manually: `pip install uv` or see "
            "https://docs.astral.sh/uv/."
        )

    uv_bin = shutil.which("uv")
    if uv_bin:
        return uv_bin

    sys.exit(
        "mcp-coder install installed uv via `pip install uv` but cannot locate "
        "it on PATH. Activate the venv it was installed into, or install uv "
        "system-wide and retry."
    )


def _rmtree_onexc(func: Callable[[str], Any], path: str, _exc: BaseException) -> None:
    """Rmtree error handler: clear the read-only bit and retry."""
    with contextlib.suppress(OSError):
        os.chmod(path, stat.S_IWRITE)
    func(path)


def rmtree_with_retry(path: Path, attempts: int = 3, delay: float = 1.0) -> None:
    """Delete a directory tree, tolerating read-only files and transient locks.

    Robust ``shutil.rmtree`` for Windows: an antivirus scanner or a
    just-exited process may still hold a handle, so failures are retried a
    few times. On final failure, exits with a clear message naming the
    locked file.

    Args:
        path: Directory tree to delete.
        attempts: How many times to try before giving up.
        delay: Seconds to wait between attempts.
    """
    kwargs: dict[str, Any] = {}
    if sys.version_info >= (3, 12):
        kwargs["onexc"] = _rmtree_onexc
    else:
        kwargs["onerror"] = _rmtree_onexc

    last_err: PermissionError | None = None
    for i in range(attempts):
        try:
            shutil.rmtree(path, **kwargs)
            return
        except PermissionError as e:
            last_err = e
            if i < attempts - 1:
                time.sleep(delay)
    assert last_err is not None  # noqa: S101 -- set whenever the loop falls through
    locked = last_err.filename or "<unknown>"
    sys.exit(
        f"ERROR: could not delete {path}\n"
        f"  locked file: {locked}\n"
        f"  Another process is holding a file in this directory open.\n"
        f"  Close any python.exe, mcp-* servers, IDEs, or shells using\n"
        f"  this venv, then re-run."
    )
