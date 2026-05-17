#!/usr/bin/env python3
"""Install mcp-coder into a target environment.

The single entry point for every mcp-coder install flow. Exists so the
install logic lives in exactly one place rather than being duplicated
across AutoRunner's `create-environment.bat`, `tools/reinstall_local.bat`,
and vscodeclaude's session-startup templates.

Callers
-------
1. **AutoRunner / Jenkins CI**
   Shallow-clones mcp_coder into a temp dir, then calls `install.bat`
   pointing at `C:\\Jenkins\\environments\\mcp-coder-dev`. Uses
   `--source git` (default) so the runtime tracks GitHub HEAD.
   See `AutoRunner/jenkins-windows/setup/create-environment.bat`.

2. **Developer reinstall** (`tools/reinstall_local.bat`)
   Reinstalls the developer's local checkout in editable mode. Uses
   `--source local --local-path <repo> --skip-templates` (the dev
   checkout already owns its templates) and adds extras: langchain,
   langchain-anthropic, mlflow.

3. **vscodeclaude session startup** (future refactor)
   Today, vscodeclaude generates inline install commands in
   `src/mcp_coder/workflows/vscodeclaude/templates.py`. Those should be
   replaced by a single call to this script.

Install sources
---------------
``--source git`` *(default)*
    Fetch from ``git+https://...mcp_coder.git@<ref>``. Sibling MCP
    packages (mcp-tools-py, mcp-workspace, mcp-coder-utils) come from
    GitHub HEAD via ``[tool.mcp-coder.install-from-github]`` in
    ``pyproject.toml``.

``--source pypi``
    Plain ``mcp-coder`` from PyPI. The GitHub override step is skipped —
    every dependency resolves through PyPI.

``--source local``
    Editable install of a local checkout (``-e <path>[extras]``).
    Sibling overrides apply so mcp-coder's deps match what CI sees.

Constraints
-----------
* **stdlib only** — must run before mcp-coder itself is installed.
* **idempotent** — safe to re-run. Without ``--clean`` the venv is
  reused and packages are upgraded in place.
* **no ``pause``** — CI must never hang on error.

Examples
--------
Jenkins runtime install::

    python tools/install.py C:\\Jenkins\\environments\\mcp-coder-dev --refresh --clean

Developer editable reinstall (also see ``tools/reinstall_local.bat``)::

    python tools/install.py . --source local --local-path . --skip-templates --refresh

Specific git tag::

    python tools/install.py /opt/mcp-coder --source git --ref v0.2.0

Stable PyPI release (no GitHub overrides)::

    python tools/install.py /opt/mcp-coder --source pypi --extras "" --skip-templates

Dry-run (print the plan, change nothing)::

    python tools/install.py /tmp/scratch --check
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

# install.py lives in tools/, so the repo root is the parent of this
# file's parent. Templates and pyproject.toml are read from there.
REPO_ROOT = Path(__file__).resolve().parent.parent

MCP_CODER_REPO = "https://github.com/MarcusJellinghaus/mcp_coder.git"

# Template files copied into <target>. Both items must exist at
# REPO_ROOT. Plain files are copied as-is; directories are merged into
# the target so existing user edits in <target>/.claude/ survive a
# re-install of unrelated files.
TEMPLATE_PATHS = (".mcp.json", ".claude")

# CLI binaries expected under <venv>/Scripts/ (or bin/) after a
# successful install. Each is queried with --version at the end as a
# smoke test and for visibility in CI logs.
CLI_BINARIES = ("mcp-coder", "mcp-tools-py", "mcp-workspace", "mcp-config")

# Library-only packages (no CLI entry point). We surface their version
# via `uv pip show` so install logs still show what's installed.
EXTRA_VERSION_QUERIES = ("mcp-coder-utils",)


def parse_args() -> argparse.Namespace:
    """Build the argparse parser and return the parsed namespace.

    See the module docstring for end-to-end examples.
    """
    p = argparse.ArgumentParser(
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
        help="Git ref for --source=git: branch, tag, or commit sha. "
             "Default: main.",
    )
    p.add_argument(
        "--local-path", type=Path,
        help="Path to a local mcp-coder checkout. Required for --source=local.",
    )
    p.add_argument(
        "--extras", default="dev",
        help='mcp-coder extras to install, e.g. "dev" or "dev,mlflow". '
             'Pass "" for no extras (typical with --source=pypi). Default: dev.',
    )
    p.add_argument(
        "--extra-packages", default="",
        help="Space-separated list of extra pip packages installed after "
             "mcp-coder, e.g. \"langchain mlflow\". Used by reinstall_local.bat.",
    )
    p.add_argument(
        "--skip-templates", action="store_true",
        help="Don't copy .mcp.json / .claude/ into <target>. Use when the "
             "target already owns its templates (e.g. a developer checkout).",
    )
    p.add_argument(
        "--refresh", action="store_true",
        help="Pass --refresh to uv so cached git clones are bypassed. "
             "Required when sibling repos have advanced since the last install.",
    )
    p.add_argument(
        "--clean", action="store_true",
        help="Delete an existing .venv before creating a fresh one. Without "
             "this flag, the existing venv is reused and packages are upgraded "
             "in place (faster, but accumulates dependencies over time).",
    )
    p.add_argument(
        "--python", default=sys.executable,
        help="Base interpreter for `python -m venv`. Default: the interpreter "
             "running this script.",
    )
    p.add_argument(
        "--check", action="store_true",
        help="Dry-run mode: print every command without executing anything.",
    )
    return p.parse_args()


def venv_bin(venv: Path) -> Path:
    """Return the executable subdir of a venv (Scripts on NT, bin elsewhere)."""
    return venv / ("Scripts" if os.name == "nt" else "bin")


def exe(name: str) -> str:
    """Append the .exe suffix on Windows; pass-through on POSIX."""
    return f"{name}.exe" if os.name == "nt" else name


def run(cmd: list[str], *, check: bool = True, dry: bool = False) -> int:
    """Run a subprocess command, printing it first.

    Args:
        cmd: Command and arguments as a list (no shell interpolation).
        check: If True (default), exit the script on non-zero return code.
            Set False for "advisory" calls like ``--version`` checks.
        dry: If True, print the command but don't execute. Wired to ``--check``.

    Returns:
        The subprocess return code, or 0 when ``dry=True``.

    Args containing whitespace are wrapped in quotes for the printed line
    so the dry-run output is shell-readable.
    """
    pretty = " ".join(f'"{c}"' if " " in str(c) else str(c) for c in cmd)
    print(">", pretty)
    if dry:
        return 0
    r = subprocess.run(cmd)
    if check and r.returncode != 0:
        sys.exit(r.returncode)
    return r.returncode


def github_overrides() -> tuple[list[str], list[str]]:
    """Read ``[tool.mcp-coder.install-from-github]`` from REPO_ROOT/pyproject.toml.

    Returns:
        A tuple ``(packages, packages_no_deps)``:

        * ``packages`` — installed with their dependencies. The common
          case for leaf packages (mcp-tools-py, mcp-workspace, etc.).
        * ``packages_no_deps`` — installed with ``--no-deps``. Used for
          packages that depend on siblings, to avoid downgrading peers
          back to PyPI versions.

    Returns ``([], [])`` if ``pyproject.toml`` is missing or has no such
    section (e.g. running from a stripped install).
    """
    pp = REPO_ROOT / "pyproject.toml"
    if not pp.exists():
        return [], []
    data = tomllib.loads(pp.read_text(encoding="utf-8"))
    gh = data.get("tool", {}).get("mcp-coder", {}).get("install-from-github", {})
    return list(gh.get("packages", [])), list(gh.get("packages-no-deps", []))


def build_source_spec(args: argparse.Namespace) -> tuple[list[str], bool]:
    """Translate ``--source/--ref/--local-path`` into uv install arguments.

    Returns:
        ``(args_after_install, is_editable)`` — the list of arguments that
        follow ``uv pip install``, and whether this is an editable install
        (used later to decide whether to re-finalize the editable link).

    Exits the process (via ``sys.exit``) if ``--source local`` was passed
    without ``--local-path``.
    """
    extras = f"[{args.extras}]" if args.extras else ""
    if args.source == "git":
        return [f"mcp-coder{extras} @ git+{MCP_CODER_REPO}@{args.ref}"], False
    if args.source == "pypi":
        return [f"mcp-coder{extras}"], False
    # --source local
    if not args.local_path:
        sys.exit("--source local requires --local-path")
    return ["-e", f"{args.local_path}{extras}"], True


def copy_templates(target: Path, *, dry: bool) -> None:
    """Copy each item in ``TEMPLATE_PATHS`` from REPO_ROOT into ``<target>``.

    Directories are merged with ``dirs_exist_ok=True`` so existing files in
    the target are overwritten but unrelated files survive. Missing source
    items are skipped with a warning, not an error — the templates are
    optional in principle (some callers may pre-populate them).
    """
    for name in TEMPLATE_PATHS:
        src, dst = REPO_ROOT / name, target / name
        if not src.exists():
            print(f"  skip (missing): {name}")
            continue
        print(f"  {name}  ->  {dst}")
        if dry:
            continue
        if src.is_dir():
            shutil.copytree(src, dst, dirs_exist_ok=True)
        else:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)


def main() -> None:
    """Drive the install in seven phases.

    1. Resolve target / venv paths and print a banner.
    2. Wipe + recreate venv (or reuse the existing one).
    3. Bootstrap pip + uv inside the venv.
    4. Install mcp-coder per ``--source``.
    5. Apply GitHub overrides for siblings (git / local only).
    6. Install ``--extra-packages`` if any.
    7. Copy templates and print installed versions.
    """
    args = parse_args()
    target = args.target.resolve()
    venv = target / ".venv"
    bin_dir = venv_bin(venv)
    py_v = bin_dir / exe("python")
    uv_v = bin_dir / exe("uv")

    # --- Phase 1: banner ----------------------------------------------------
    src_label = args.source
    if args.source == "git":
        src_label += f"@{args.ref}"
    elif args.source == "local":
        src_label += f" ({args.local_path})"
    print(f"=== install-env -> {target}")
    print(f"    source: {src_label}")

    # --- Phase 2: target dir + venv ----------------------------------------
    target.mkdir(parents=True, exist_ok=True)
    if args.clean and venv.exists():
        print(f"--- wiping {venv}")
        if not args.check:
            shutil.rmtree(venv)
    if not venv.exists():
        run([args.python, "-m", "venv", str(venv)], dry=args.check)

    # --- Phase 3: bootstrap pip + uv ---------------------------------------
    # uv is the actual installer used below; pip is only needed long enough
    # to fetch uv (uv isn't part of the stdlib).
    run([str(py_v), "-m", "pip", "install", "--upgrade", "pip", "uv"], dry=args.check)

    # --- Phase 4: install mcp-coder itself ---------------------------------
    spec_args, is_editable = build_source_spec(args)
    cmd = [str(uv_v), "pip", "install", "--python", str(py_v)]
    if args.refresh:
        cmd.append("--refresh")
    run(cmd + spec_args, dry=args.check)

    # --- Phase 5: GitHub overrides for sibling MCP packages ----------------
    # mcp-coder's pyproject.toml lists `mcp-tools-py`, `mcp-workspace`,
    # `mcp-coder-utils` as plain PyPI deps so published wheels stay portable.
    # Locally / on CI we want their GitHub HEAD instead — declared under
    # `[tool.mcp-coder.install-from-github]`. We re-install them here.
    # This step is skipped for --source pypi where the whole point is
    # reproducible PyPI-only resolution.
    if args.source in ("git", "local"):
        pkgs, pkgs_no_deps = github_overrides()
        if pkgs:
            c = [str(uv_v), "pip", "install", "--python", str(py_v)]
            if args.refresh:
                c.append("--refresh")
            run(c + pkgs, dry=args.check)
        if pkgs_no_deps:
            c = [str(uv_v), "pip", "install", "--no-deps", "--python", str(py_v)]
            if args.refresh:
                c.append("--refresh")
            run(c + pkgs_no_deps, dry=args.check)
        # When mcp-coder was installed editable, the override step above may
        # have pulled in a fresh mcp-coder wheel as a transitive dep and
        # replaced the editable link. Re-run the editable install so the
        # developer's source tree wins again.
        if is_editable:
            run([str(uv_v), "pip", "install", "-e", str(args.local_path),
                 "--python", str(py_v)], dry=args.check)

    # --- Phase 6: additional packages --------------------------------------
    if args.extra_packages:
        run([str(uv_v), "pip", "install", "--python", str(py_v),
             *args.extra_packages.split()], dry=args.check)

    # --- Phase 7: templates + version banner -------------------------------
    if not args.skip_templates:
        print("\n--- templates")
        copy_templates(target, dry=args.check)

    print("\n--- installed versions")
    if args.check:
        print("  (skipped in --check mode)")
    else:
        for name in CLI_BINARIES:
            binp = bin_dir / exe(name)
            if binp.exists():
                run([str(binp), "--version"], check=False)
            else:
                print(f"  (missing CLI: {name})")
        for pkg in EXTRA_VERSION_QUERIES:
            run([str(uv_v), "pip", "show", "--python", str(py_v), pkg], check=False)

    print(f"\nOK  install-env complete: {target}")


if __name__ == "__main__":
    main()
