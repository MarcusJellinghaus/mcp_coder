r"""Resolve a step's `argv[0]` to an executable path.

Shared by the command toolkit, `mcp-coder setup` and `verify`. The rules are
applied without `shutil.which` so they are unit-testable on any host:

- A path-like `argv[0]` (contains `/`; on Windows also `\`) is taken as-is when
  absolute, else relative to the project directory.
- A bare name is looked up in the absolute entries of `PATH`; empty and relative
  entries are skipped, so the working directory is never searched.
- Windows: a name whose suffix is in `PATHEXT` is used as-is; otherwise each
  `PATHEXT` extension is tried in order. There is no fallback to the
  extensionless file.
"""

import os
import sys
from pathlib import Path

_DEFAULT_PATHEXT = ".COM;.EXE;.BAT;.CMD"


def resolve_executable(
    argv0: str, project_dir: Path, path: str | None = None
) -> str | None:
    """Resolve a step's argv[0]; None when not found.

    Args:
        argv0: The step's first argument.
        project_dir: Directory that relative path-like names are resolved against.
        path: PATH string to search for bare names; None = `os.environ["PATH"]`.

    Returns:
        The resolved executable path, or None when no candidate matches.
    """
    windows = sys.platform == "win32"
    exts = (
        [e.lower() for e in os.environ.get("PATHEXT", _DEFAULT_PATHEXT).split(";") if e]
        if windows
        else []
    )

    if "/" in argv0 or (windows and "\\" in argv0):
        argv0_path = Path(argv0)
        bases = [argv0_path if argv0_path.is_absolute() else project_dir / argv0]
    else:
        search = path if path is not None else os.environ.get("PATH", "")
        bases = [
            Path(d) / argv0
            for d in search.split(os.pathsep)
            if d and Path(d).is_absolute()
        ]

    for base in bases:
        if not windows or base.suffix.lower() in exts:
            candidates = [base]
        else:
            candidates = [base.with_name(base.name + e) for e in exts]
        for candidate in candidates:
            if candidate.is_file() and (windows or os.access(candidate, os.X_OK)):
                return str(candidate)
    return None
