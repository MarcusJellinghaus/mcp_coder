"""Startup dependency guard — pure, stdlib + ``packaging`` only.

This module is deliberately kept outside the layered architecture: it imports
nothing from ``mcp_coder.*`` and pulls no heavy dependencies, so it is safe to
import from ``mcp_coder/__init__.py`` while ``__init__`` is still executing.

It detects an incomplete install (e.g. ``pip install --no-deps``) and turns the
resulting ``ModuleNotFoundError`` traceback into a clear, diagnosable message.
"""

import sys
from importlib.metadata import PackageNotFoundError, requires, version

from packaging.requirements import Requirement


def find_missing_dependencies() -> list[str]:
    """Return declared mandatory distributions that are not installed.

    Pure: no side effects, no heavy imports. Returns ``[]`` when mcp-coder's own
    distribution metadata is absent (source-only / pythonpath runs) or when
    ``requires()`` yields nothing — the guard cannot enumerate deps, so it must
    not block.
    """
    try:
        reqs = requires("mcp-coder") or []
    except PackageNotFoundError:
        return []

    missing: list[str] = []
    for spec in reqs:
        try:
            req = Requirement(spec)
        except Exception:  # pylint: disable=broad-exception-caught
            # Unparseable spec has no usable name to check — skip it.
            continue
        try:
            # Explicit extra="" makes extra-markers evaluate False across
            # packaging versions; off-platform markers drop too.
            if req.marker and not req.marker.evaluate(environment={"extra": ""}):
                continue
        except Exception:  # pylint: disable=broad-exception-caught
            # Odd marker still has a name — don't fail-open; fall through to
            # the presence check below.
            pass
        try:
            version(req.name)
        except PackageNotFoundError:
            missing.append(req.name)
    return missing


def ensure_dependencies() -> None:
    """Print a friendly message to stderr and exit 1 if deps are missing."""
    missing = find_missing_dependencies()
    if not missing:
        return
    print(f"mcp-coder {_installed_version()}", file=sys.stderr)
    print(
        "Installation incomplete — missing required dependencies: "
        f"{', '.join(missing)}",
        file=sys.stderr,
    )
    print(
        "This looks like a --no-deps install. Reinstall with:  "
        "pip install mcp-coder",
        file=sys.stderr,
    )
    raise SystemExit(1)


def _installed_version() -> str:
    """mcp-coder version via importlib.metadata, or the dev fallback."""
    try:
        return version("mcp-coder")
    except PackageNotFoundError:
        return "0.0.0.dev0+unknown"
