#!/usr/bin/env python3
"""Install mcp-coder (and/or related projects) into a target environment.

A **standalone script**, not part of mcp-coder's importable API.

Distribution
------------
The canonical script lives at ``tools/install.py`` in the repo. The
wheel also ships a copy at ``<install-prefix>/share/mcp-coder/install.py``
(via ``[tool.setuptools.data-files]`` in ``pyproject.toml``) so
processes running from an installed mcp-coder env can locate and
invoke the same script.

Scope
-----
Installs Python packages only. Files that need to be staged alongside
the install (e.g. ``.mcp.json``, ``.claude/``) are the caller's
responsibility.

Install sources
---------------
``--source git`` *(default)*
    Fetch from ``git+https://...mcp_coder.git@<ref>``. Sibling MCP
    packages (mcp-tools-py, mcp-workspace, mcp-coder-utils) come from
    GitHub HEAD via ``[tool.mcp-coder.install-from-github]``.

``--source pypi``
    Plain ``mcp-coder`` from PyPI. GitHub override step is skipped.

``--source local``
    Editable install of a local checkout (``-e <path>[extras]``).
    With ``--use-sync``, switches to a uv.lock-honoring flow:
    ``uv venv`` -> ``uv sync --extra <extras>`` -> GitHub overrides ->
    ``uv pip install -e . --no-deps``.

Constraints
-----------
* stdlib only — must run before mcp-coder is installed.
* Idempotent. Re-running upgrades in place unless ``--clean``.
* Never blocks on user input (no ``pause``, no interactive prompts).

Examples
--------
Fresh install from git into a target directory::

    python tools/install.py /path/to/target --refresh --clean

Editable install of a local checkout (uv sync flow)::

    python tools/install.py . --source local --local-path . \\
        --use-sync --refresh

Stable PyPI release::

    python tools/install.py /opt/mcp-coder --source pypi --extras ""
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

MCP_CODER_REPO = "https://github.com/MarcusJellinghaus/mcp_coder.git"

CLI_BINARIES = ("mcp-coder", "mcp-tools-py", "mcp-workspace", "mcp-config")
EXTRA_VERSION_QUERIES = ("mcp-coder-utils",)


def _detect_repo_root() -> Path | None:
    """Return the mcp-coder repo root if this file lives in a clone.

    Two file layouts are supported:

    * Clone (any checkout of the mcp-coder repo):
      ``<repo>/tools/install.py``  ->  REPO_ROOT = ``<repo>``
    * Wheel-deployed copy:
      ``<install-prefix>/share/mcp-coder/install.py``  ->  no repo root.

    Returns ``None`` when no repo root could be detected. Detection is
    "does the candidate parent directory contain ``pyproject.toml``" —
    the deployed copy sits next to no pyproject.toml, so it falls
    through and ``REPO_ROOT`` ends up ``None``.
    """
    here = Path(__file__).resolve()
    # parents[1] = repo root when this file is at <repo>/tools/install.py
    candidate = here.parents[1]
    if (candidate / "pyproject.toml").exists():
        return candidate
    return None


REPO_ROOT: Path | None = _detect_repo_root()


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Build the argparse parser and return the parsed namespace.

    ``argv`` defaults to ``sys.argv[1:]`` when not provided; pass an
    explicit list for testing or when invoking programmatically.
    """
    p = argparse.ArgumentParser(
        prog="install-env",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument(
        "target", type=Path,
        help="Directory that will hold <target>/.venv and copied configs.",
    )
    p.add_argument(
        "--source", choices=("git", "pypi", "local"), default="git",
        help="Where to install mcp-coder from (default: git).",
    )
    p.add_argument(
        "--ref", default="main",
        help="Git ref (branch/tag/sha) for --source=git. Default: main.",
    )
    p.add_argument(
        "--local-path", type=Path,
        help="Path to a local checkout (required for --source=local). Also "
             "determines which pyproject.toml is read for GitHub overrides.",
    )
    p.add_argument(
        "--extras", default="dev",
        help='Extras to install, e.g. "dev" or "dev,mlflow". Pass "" for '
             'no extras (typical with --source=pypi). Default: dev.',
    )
    p.add_argument(
        "--extra-packages", default="",
        help="Space-separated extra packages installed after the main "
             "install (e.g. \"langchain mlflow\").",
    )
    p.add_argument(
        "--use-sync", action="store_true",
        help="For --source=local: use the uv.lock-honoring install "
             "sequence (uv venv + uv sync --extra <extras> + GitHub "
             "overrides + uv pip install -e . --no-deps) instead of a "
             "single uv pip install. Reproducible builds via the "
             "project's uv.lock.",
    )
    p.add_argument(
        "--skip-overrides", action="store_true",
        help="Skip the [tool.mcp-coder.install-from-github] step entirely. "
             "Use when whatever versions PyPI / the lock file provide are "
             "preferred over GitHub HEAD.",
    )
    p.add_argument(
        "--refresh", action="store_true",
        help="Pass --refresh to uv so cached git clones are bypassed.",
    )
    p.add_argument(
        "--clean", action="store_true",
        help="Delete an existing .venv before creating a fresh one.",
    )
    p.add_argument(
        "--python", default=sys.executable,
        help="Base interpreter for `python -m venv`. Default: current.",
    )
    p.add_argument(
        "--check", action="store_true",
        help="Dry-run mode: print every command without executing anything.",
    )
    return p.parse_args(argv)


def venv_bin(venv: Path) -> Path:
    """Return the executable subdir of a venv (Scripts on NT, bin elsewhere)."""
    return venv / ("Scripts" if os.name == "nt" else "bin")


def exe(name: str) -> str:
    """Append the .exe suffix on Windows; pass-through on POSIX."""
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
        check: Exit the script on non-zero return code when True.
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
    r = subprocess.run(cmd, cwd=cwd)
    if check and r.returncode != 0:
        sys.exit(r.returncode)
    return r.returncode


def github_overrides(pyproject_dir: Path) -> tuple[list[str], list[str]]:
    """Read ``[tool.mcp-coder.install-from-github]`` from ``pyproject_dir``.

    Returns:
        ``(packages, packages_no_deps)`` — two lists of install specs.
        Empty when the section or file is missing.

    Notes:
        Same parsing as :mod:`mcp_coder.utils.pyproject_config`, but
        duplicated here so this module remains importable without any
        mcp-coder dependencies (bootstrap requirement).
    """
    pp = pyproject_dir / "pyproject.toml"
    if not pp.exists():
        return [], []
    data = tomllib.loads(pp.read_text(encoding="utf-8"))
    gh = data.get("tool", {}).get("mcp-coder", {}).get("install-from-github", {})
    return list(gh.get("packages", [])), list(gh.get("packages-no-deps", []))


def _source_dir_for_overrides(args: argparse.Namespace) -> Path | None:
    """Pick which pyproject.toml is consulted for GitHub overrides.

    Precedence:
    1. ``--local-path`` when provided (target project's overrides).
    2. ``REPO_ROOT`` (only set when running from a mcp-coder clone).
    3. ``None`` — no overrides applied.
    """
    if args.local_path:
        return args.local_path
    return REPO_ROOT


def _phase_venv(target: Path, venv: Path, args: argparse.Namespace) -> None:
    """Phase 1+2: prepare the target dir and (re)create the venv.

    With ``--clean``, an existing venv is wiped first. ``uv venv`` is
    preferred when an existing ``uv`` binary is on PATH; otherwise the
    stdlib ``venv`` module is used.
    """
    target.mkdir(parents=True, exist_ok=True)
    if args.clean and venv.exists():
        print(f"--- wiping {venv}")
        if not args.check:
            shutil.rmtree(venv)
    if venv.exists():
        return
    uv_bootstrap = shutil.which("uv")
    if uv_bootstrap:
        run([uv_bootstrap, "venv", str(venv)], dry=args.check)
    else:
        run([args.python, "-m", "venv", str(venv)], dry=args.check)


def _phase_bootstrap_pip_uv(py_v: Path, args: argparse.Namespace) -> None:
    """Phase 3: ensure pip and uv exist inside the freshly-built venv.

    ``uv venv`` does NOT seed pip into the new venv, so we cannot
    ``python -m pip install ...`` from inside it. When system ``uv``
    is on PATH (the typical case), use it with ``--python <venv-py>``
    to populate the venv. Falls back to in-venv pip when only a
    stdlib venv exists.
    """
    uv_bootstrap = shutil.which("uv")
    if uv_bootstrap:
        run([uv_bootstrap, "pip", "install", "--python", str(py_v),
             "pip", "uv"], dry=args.check)
    else:
        run([str(py_v), "-m", "pip", "install", "--upgrade", "pip", "uv"],
            dry=args.check)


def _phase_install_main(
    uv_v: Path, py_v: Path, args: argparse.Namespace
) -> bool:
    """Phase 4: install the main package per ``--source``.

    Returns:
        True when this is an editable install (so phase 5 knows whether
        to re-finalize the link after applying GitHub overrides).
    """
    extras = f"[{args.extras}]" if args.extras else ""

    if args.source == "git":
        spec = f"mcp-coder{extras} @ git+{MCP_CODER_REPO}@{args.ref}"
        cmd = [str(uv_v), "pip", "install", "--python", str(py_v)]
        if args.refresh:
            cmd.append("--refresh")
        run(cmd + [spec], dry=args.check)
        return False

    if args.source == "pypi":
        spec = f"mcp-coder{extras}"
        run([str(uv_v), "pip", "install", "--python", str(py_v), spec],
            dry=args.check)
        return False

    # --source local
    if not args.local_path:
        sys.exit("--source local requires --local-path")

    if args.use_sync:
        # uv.lock-honoring flow: reproducible builds via the project's
        # lockfile. `uv sync` needs to run from the project directory
        # (it reads pyproject.toml + uv.lock there) and writes to
        # <cwd>/.venv — the cwd's .venv must equal our target venv.
        # We arrange that by always passing local_path == target.
        sync_cmd = [str(uv_v), "sync"]
        if args.extras:
            for extra in args.extras.split(","):
                extra = extra.strip()
                if extra:
                    sync_cmd += ["--extra", extra]
        if args.refresh:
            sync_cmd.append("--refresh")
        run(sync_cmd, dry=args.check, cwd=args.local_path)
    else:
        cmd = [str(uv_v), "pip", "install", "--python", str(py_v)]
        if args.refresh:
            cmd.append("--refresh")
        cmd += ["-e", f"{args.local_path}{extras}"]
        run(cmd, dry=args.check)

    return True


def _phase_overrides(
    uv_v: Path, py_v: Path, args: argparse.Namespace, is_editable: bool
) -> None:
    """Phase 5: apply ``[tool.mcp-coder.install-from-github]`` overrides.

    Replaces transient PyPI versions of sibling MCP packages with their
    GitHub HEAD versions (or whatever revision is specified in the
    declaring project's pyproject.toml). Always re-finalizes the
    editable link afterwards when ``is_editable`` is True — a fresh
    mcp-coder wheel may have been pulled in transitively and shadowed
    the editable install.

    Skipped entirely for ``--source pypi`` (PyPI-only install) or when
    ``--skip-overrides`` is set (caller opts out of GitHub HEAD).
    """
    if args.source == "pypi" or args.skip_overrides:
        return

    src_dir = _source_dir_for_overrides(args)
    if src_dir is None:
        print("--- skipping GitHub overrides (no pyproject.toml available)")
        return

    pkgs, pkgs_no_deps = github_overrides(src_dir)
    if pkgs:
        cmd = [str(uv_v), "pip", "install", "--python", str(py_v)]
        if args.refresh:
            cmd.append("--refresh")
        run(cmd + pkgs, dry=args.check)
    if pkgs_no_deps:
        cmd = [str(uv_v), "pip", "install", "--no-deps", "--python", str(py_v)]
        if args.refresh:
            cmd.append("--refresh")
        run(cmd + pkgs_no_deps, dry=args.check)

    if is_editable:
        # The override step may have pulled a fresh mcp-coder wheel in
        # as a transitive dep, replacing the editable install. Re-link.
        run([str(uv_v), "pip", "install", "-e", str(args.local_path),
             "--no-deps", "--python", str(py_v)], dry=args.check)


def _phase_versions(bin_dir: Path, uv_v: Path, py_v: Path, args: argparse.Namespace) -> None:
    """Phase 7b: print installed versions of CLIs and library-only packages.

    Exits non-zero when an expected CLI binary is missing from the venv
    — that indicates the install silently failed to wire up an entry
    point. ``--version`` itself is still allowed to fail (a CLI that
    crashes on ``--version`` is a separate problem worth a separate
    signal, not a reason to fail the whole install).
    """
    print("\n--- installed versions")
    if args.check:
        print("  (skipped in --check mode)")
        return
    missing: list[str] = []
    for name in CLI_BINARIES:
        binp = bin_dir / exe(name)
        if binp.exists():
            run([str(binp), "--version"], check=False)
        else:
            print(f"  (missing CLI: {name})")
            missing.append(name)
    for pkg in EXTRA_VERSION_QUERIES:
        run([str(uv_v), "pip", "show", "--python", str(py_v), pkg],
            check=False)
    if missing:
        sys.exit(
            f"missing CLI binaries after install: {', '.join(missing)}. "
            "Entry points were not wired into the venv."
        )


def main(argv: list[str] | None = None) -> None:
    """Drive the install. See module docstring for caller scenarios."""
    args = parse_args(argv)
    target = args.target.resolve()

    # `uv sync` writes its venv to `<cwd>/.venv`, where cwd is forced to
    # `args.local_path` (it needs that dir's pyproject.toml + uv.lock).
    # So with --use-sync, target MUST equal local_path; otherwise we'd
    # provision `target/.venv` in phase 1, then `uv sync` would silently
    # create a second venv at `local_path/.venv` and leave the original
    # empty. Codify the invariant — better a clear error than two venvs.
    if args.use_sync and args.local_path:
        if args.local_path.resolve() != target:
            sys.exit(
                f"--use-sync requires target ({target}) to equal "
                f"--local-path ({args.local_path.resolve()}). "
                "uv sync writes to <local-path>/.venv."
            )

    venv = target / ".venv"
    bin_dir = venv_bin(venv)
    py_v = bin_dir / exe("python")
    uv_v = bin_dir / exe("uv")

    src_label = args.source
    if args.source == "git":
        src_label += f"@{args.ref}"
    elif args.source == "local":
        src_label += f" ({args.local_path})"
        if args.use_sync:
            src_label += " [uv sync]"
    print(f"=== install-env -> {target}")
    print(f"    source: {src_label}")

    _phase_venv(target, venv, args)
    _phase_bootstrap_pip_uv(py_v, args)
    is_editable = _phase_install_main(uv_v, py_v, args)
    _phase_overrides(uv_v, py_v, args, is_editable)

    if args.extra_packages:
        run([str(uv_v), "pip", "install", "--python", str(py_v),
             *args.extra_packages.split()], dry=args.check)

    _phase_versions(bin_dir, uv_v, py_v, args)
    print(f"\nOK  install-env complete: {target}")


if __name__ == "__main__":
    main()
