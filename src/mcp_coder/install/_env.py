"""Environment helpers and the resolved configuration for ``mcp-coder install``.

Everything the install phases need that is not itself a phase: the module
constants, the frozen :class:`InstallConfig` built from parsed CLI arguments,
and the small subprocess / filesystem helpers.

Raw ``subprocess.run`` with inherited stdio is deliberate here: the shared
``execute_command`` helper captures output and times out, and
``stream_subprocess`` is line-based, which mangles ``uv``'s carriage-return
progress display.
"""

from __future__ import annotations

import argparse
import os
import shutil
import stat
import subprocess
import sys
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..utils.pyproject_config import get_install_extras

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

# Used when neither --extras nor the target's [tool.mcp-coder.install] section
# declares anything. This is the only fallback site.
_DEFAULT_EXTRAS = "dev"


@dataclass(frozen=True)
class InstallConfig:
    """Fully resolved inputs for one install run.

    ``local_path`` and ``extras`` are always resolved, so no phase ever sees
    a sentinel: ``local_path`` defaults to ``target`` and ``extras`` falls
    back to the target project's declared policy, then to ``"dev"``.
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

    @classmethod
    def from_args(cls, args: argparse.Namespace) -> "InstallConfig":
        """Resolve a parsed argument namespace into an InstallConfig.

        Args:
            args: Namespace produced by ``add_install_parser``.

        Returns:
            The resolved configuration.

        Raises:
            ValueError: If ``--source local`` was passed without
                ``--local-path``, if ``--use-sync`` was combined with a
                target that differs from ``--local-path``, or if the target
                project's pyproject.toml exists but cannot be parsed.
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


def run(
    cmd: list[str],
    *,
    check: bool = True,
    dry: bool = False,
    cwd: Path | None = None,
) -> int:
    """Run a subprocess command, printing it first.

    Args:
        cmd: Command + arguments as a list (no shell interpolation).
        check: Exit the process on a non-zero return code when True.
        dry: Print only, don't execute. Wired to ``--check``.
        cwd: Working directory for the subprocess. Required for
            ``uv sync`` which reads pyproject.toml from cwd.

    Returns:
        Subprocess return code, or 0 when ``dry=True``.
    """
    pretty = " ".join(f'"{c}"' if " " in str(c) else str(c) for c in cmd)
    cwd_hint = f" (cwd={cwd})" if cwd else ""
    print(">", pretty + cwd_hint)
    if dry:
        return 0
    # check=False is subprocess's own flag. This wrapper's `check` means
    # "exit the process on failure", handled two lines below; forwarding it
    # would raise CalledProcessError instead and change behaviour.
    result = subprocess.run(cmd, cwd=cwd, check=False)
    if check and result.returncode != 0:
        sys.exit(result.returncode)
    return result.returncode


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

    print("--- uv not on PATH; attempting `python -m pip install uv`")
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
    try:
        os.chmod(path, stat.S_IWRITE)
    except OSError:
        pass
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
    assert last_err is not None
    locked = last_err.filename or "<unknown>"
    sys.exit(
        f"ERROR: could not delete {path}\n"
        f"  locked file: {locked}\n"
        f"  Another process is holding a file in this directory open.\n"
        f"  Close any python.exe, mcp-* servers, IDEs, or shells using\n"
        f"  this venv, then re-run."
    )
