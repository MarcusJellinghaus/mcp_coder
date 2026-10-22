"""The six phases of an install run, in the order ``install()`` calls them."""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

from ..utils.pyproject_config import get_github_install_config
from ..utils.subprocess_runner import CommandOptions, execute_subprocess
from ._env import (
    MCP_CODER_REPO,
    REPORT_BINARIES,
    REPORT_PACKAGES,
    InstallConfig,
    exe,
    rmtree_with_retry,
    run,
)

# Generous on purpose: a check is a smoke test, but a cold first start of a
# freshly-installed CLI (AV scan, .pyc compilation) can take a while.
POST_INSTALL_CHECK_TIMEOUT_SECONDS = 300


def phase_venv(config: InstallConfig, venv: Path) -> None:
    """Phase 1+2: prepare the target dir and (re)create the venv.

    With ``--clean``, an existing venv is wiped first. ``uv venv`` is
    preferred when an existing ``uv`` binary is on PATH; otherwise the
    stdlib ``venv`` module is used.

    Args:
        config: Resolved install configuration.
        venv: Path of the venv to create.
    """
    config.target.mkdir(parents=True, exist_ok=True)
    if config.clean and venv.exists():
        print(f"--- wiping {venv}")
        if not config.check:
            rmtree_with_retry(venv)
    if venv.exists():
        return
    uv_bootstrap = shutil.which("uv")
    if uv_bootstrap:
        run([uv_bootstrap, "venv", str(venv)], dry=config.check)
    else:
        run([config.python, "-m", "venv", str(venv)], dry=config.check)


def phase_bootstrap_pip_uv(config: InstallConfig, py_v: Path) -> None:
    """Phase 3: ensure pip and uv exist inside the freshly-built venv.

    ``uv venv`` does NOT seed pip into the new venv, so we cannot
    ``python -m pip install ...`` from inside it. When system ``uv``
    is on PATH (the typical case), use it with ``--python <venv-py>``
    to populate the venv. Falls back to in-venv pip when only a
    stdlib venv exists.

    Skipped by ``install()`` for the local+``use_sync`` path: ``uv sync``
    reconciles the venv to the lockfile and removes pip+uv again since
    they are not project dependencies, so running this phase first would
    only add a write-then-delete of ``uv.exe`` moments apart.

    Args:
        config: Resolved install configuration.
        py_v: Path to the venv's python executable.
    """
    uv_bootstrap = shutil.which("uv")
    if uv_bootstrap:
        run(
            [uv_bootstrap, "pip", "install", "--python", str(py_v), "pip", "uv"],
            dry=config.check,
        )
    else:
        run(
            [str(py_v), "-m", "pip", "install", "--upgrade", "pip", "uv"],
            dry=config.check,
        )


def phase_install_main(config: InstallConfig, uv_bin: str, py_v: Path) -> bool:
    """Phase 4: install the main package per ``--source``.

    Uses ``uv_bin`` (system uv) targeted at the venv via
    ``--python <venv-py>``. We do NOT call the in-venv uv here: ``uv sync``
    rewrites the venv to match the lockfile, which removes pip+uv (they
    are not project dependencies), so any subsequent in-venv ``uv`` call
    would FileNotFoundError. System uv side-steps that entirely.

    Args:
        config: Resolved install configuration.
        uv_bin: Path to the system uv binary.
        py_v: Path to the venv's python executable.

    Returns:
        True when this is an editable install (so phase 5 knows whether
        to re-finalize the link after applying GitHub overrides).
    """
    extras = f"[{config.extras}]" if config.extras else ""

    if config.source == "git":
        spec = f"mcp-coder{extras} @ git+{MCP_CODER_REPO}@{config.ref}"
        cmd = [uv_bin, "pip", "install", "--python", str(py_v)]
        if config.refresh:
            cmd.append("--refresh")
        run(cmd + [spec], dry=config.check)
        return False

    if config.source == "pypi":
        run(
            [uv_bin, "pip", "install", "--python", str(py_v), f"mcp-coder{extras}"],
            dry=config.check,
        )
        return False

    # --source local
    if config.use_sync:
        # uv.lock-honoring flow: reproducible builds via the project's
        # lockfile. `uv sync` needs to run from the project directory
        # (it reads pyproject.toml + uv.lock there) and writes to
        # <cwd>/.venv — the cwd's .venv must equal our target venv.
        # InstallConfig.from_args enforces local_path == target.
        sync_cmd = [uv_bin, "sync"]
        for extra in config.extras.split(","):
            extra = extra.strip()
            if extra:
                sync_cmd += ["--extra", extra]
        if config.refresh:
            sync_cmd.append("--refresh")
        run(sync_cmd, dry=config.check, cwd=config.local_path)
    else:
        cmd = [uv_bin, "pip", "install", "--python", str(py_v)]
        if config.refresh:
            cmd.append("--refresh")
        cmd += ["-e", f"{config.local_path}{extras}"]
        run(cmd, dry=config.check)

    return True


def phase_overrides(
    config: InstallConfig, uv_bin: str, py_v: Path, is_editable: bool
) -> None:
    """Phase 5: apply ``[tool.mcp-coder.install-from-github]`` overrides.

    Replaces transient PyPI versions of sibling MCP packages with their
    GitHub HEAD versions (or whatever revision is specified in the
    declaring project's pyproject.toml). Always re-finalizes the
    editable link afterwards when ``is_editable`` is True — a fresh
    mcp-coder wheel may have been pulled in transitively and shadowed
    the editable install.

    Skipped entirely for ``--source pypi`` (PyPI-only install) or when
    ``--skip-overrides`` is set (caller opts out of GitHub HEAD). When the
    resolved ``local_path`` declares no overrides at all, that is reported
    rather than passed over in silence: it is the usual outcome of a
    ``--source git`` install whose ``--local-path`` is not a checkout, and
    it means the siblings come from PyPI.

    Args:
        config: Resolved install configuration.
        uv_bin: Path to the system uv binary.
        py_v: Path to the venv's python executable.
        is_editable: Whether phase 4 performed an editable install.
    """
    if config.source == "pypi" or config.skip_overrides:
        return

    overrides = get_github_install_config(config.local_path)
    if not overrides.packages and not overrides.packages_no_deps:
        pyproject = config.local_path / "pyproject.toml"
        reason = (
            f"no {pyproject}"
            if not pyproject.exists()
            else f"no [tool.mcp-coder.install-from-github] in {pyproject}"
        )
        print(
            f"--- skipping GitHub overrides ({reason}); "
            "sibling packages come from PyPI"
        )
    if overrides.packages:
        cmd = [uv_bin, "pip", "install", "--python", str(py_v)]
        if config.refresh:
            cmd.append("--refresh")
        run(cmd + overrides.packages, dry=config.check)
    if overrides.packages_no_deps:
        cmd = [uv_bin, "pip", "install", "--no-deps", "--python", str(py_v)]
        if config.refresh:
            cmd.append("--refresh")
        run(cmd + overrides.packages_no_deps, dry=config.check)

    if is_editable:
        # The override step may have pulled a fresh mcp-coder wheel in
        # as a transitive dep, replacing the editable install. Re-link.
        run(
            [
                uv_bin,
                "pip",
                "install",
                "-e",
                str(config.local_path),
                "--no-deps",
                "--python",
                str(py_v),
            ],
            dry=config.check,
        )


def phase_report_versions(
    config: InstallConfig, bin_dir: Path, uv_bin: str, py_v: Path
) -> None:
    """Phase 6: print installed versions of CLIs and library-only packages.

    Purely informational: a binary the target project never asked for is
    reported as not installed, and a CLI that crashes on ``--version`` is a
    separate problem worth a separate signal. Neither fails the install.

    Args:
        config: Resolved install configuration.
        bin_dir: The venv's executable directory.
        uv_bin: Path to the system uv binary.
        py_v: Path to the venv's python executable.
    """
    print("\n--- installed versions")
    if config.check:
        print("  (skipped in --check mode)")
        return
    for name in REPORT_BINARIES:
        binp = bin_dir / exe(name)
        if binp.exists():
            run([str(binp), "--version"], check=False)
        else:
            print(f"  (not installed: {name})")
    for pkg in REPORT_PACKAGES:
        run([uv_bin, "pip", "show", "--python", str(py_v), pkg], check=False)


def _resolve_check_executable(
    name: str, bin_dir: Path, local_path: Path
) -> Path | None:
    """Resolve argv[0] of a post-install check; None means not found.

    A name containing a path separator is a path: used as-is when absolute,
    joined to ``local_path`` when relative. A bare name is looked up in the
    venv ``bin_dir`` first, then in each absolute ``PATH`` entry in order.
    The current directory is never searched -- ``shutil.which`` is avoided
    because on Windows it adds the cwd to the search path.

    Args:
        name: The declared argv[0].
        bin_dir: The venv's executable directory.
        local_path: The target project directory.

    Returns:
        The resolved executable file, or None when nothing matches.
    """
    if os.sep in name or (os.altsep and os.altsep in name):
        path = Path(name) if Path(name).is_absolute() else local_path / name
        return path if path.is_file() else None
    candidate = name if name.lower().endswith(".exe") else exe(name)
    # Relative PATH entries (e.g. ".") are skipped: they would search the cwd.
    path_dirs = [
        Path(entry)
        for entry in os.environ.get("PATH", "").split(os.pathsep)
        if Path(entry).is_absolute()
    ]
    for directory in [bin_dir, *path_dirs]:
        if (directory / candidate).is_file():
            return directory / candidate
    return None


def phase_post_install_checks(config: InstallConfig, bin_dir: Path) -> None:
    """Phase 7: run [tool.mcp-coder.install] post_install_checks; exit 1 on any failure.

    Every declared check runs, even after one fails, so a single summary
    names all of them. An executable that cannot be resolved is reported as
    not found without spawning anything. In ``--check`` mode the declared
    argv is echoed unresolved and nothing runs.

    Args:
        config: Resolved install configuration.
        bin_dir: The venv's executable directory.
    """
    if not config.post_install_checks:
        return
    print("\n--- post-install checks")
    if config.check:
        for argv in config.post_install_checks:
            run(list(argv), dry=True, cwd=config.local_path)
        return

    failures: list[tuple[tuple[str, ...], str]] = []
    path_env = f"{bin_dir}{os.pathsep}{os.environ.get('PATH', '')}"
    for argv in config.post_install_checks:
        resolved = _resolve_check_executable(argv[0], bin_dir, config.local_path)
        if resolved is None:
            failures.append((argv, "not found"))
            continue
        cmd = [str(resolved), *argv[1:]]
        run(cmd, dry=True, cwd=config.local_path)
        result = execute_subprocess(
            cmd,
            CommandOptions(
                cwd=str(config.local_path),
                timeout_seconds=POST_INSTALL_CHECK_TIMEOUT_SECONDS,
                capture_output=False,
                env={"PATH": path_env},
            ),
        )
        if result.timed_out:
            failures.append(
                (argv, f"timed out after {POST_INSTALL_CHECK_TIMEOUT_SECONDS} s")
            )
        elif result.execution_error:
            failures.append((argv, result.execution_error))
        elif result.return_code:
            failures.append((argv, f"exit code {result.return_code}"))

    if failures:
        total = len(config.post_install_checks)
        print(f"\nERROR: {len(failures)} of {total} post-install checks failed:")
        for argv, reason in failures:
            print(f"  {' '.join(argv)}: {reason}")
        sys.exit(1)
