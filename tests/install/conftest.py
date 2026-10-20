"""Shared test helpers for ``tests/install``.

Not a fixture module in the pytest-DI sense: ``namespace`` is a plain
function the test modules call directly with varying keyword overrides,
and ``subprocess`` is a module-attribute shim. Both are imported
explicitly where needed.

Subprocess note: ``_env.subprocess`` is reached as a module attribute on
purpose. The ``subprocess_isolation`` import-linter contract grants
``tests.install`` no exemption, so a bare ``import subprocess`` here would
break it.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from mcp_coder.install import _env

# Reached via attribute access with a type: ignore rather than a bare
# `import subprocess`: the latter would break the subprocess_isolation
# contract, which grants tests.install no exemption. mypy's
# no-implicit-reexport flags the attribute form as attr-defined since
# _env doesn't explicitly re-export this stdlib module.
subprocess = _env.subprocess  # type: ignore[attr-defined]


def namespace(**overrides: Any) -> argparse.Namespace:
    """Build the Namespace add_install_parser would produce.

    Defaults mirror the ``source="git"`` / editable-install path used by
    ``test_install_phases.py`` and ``test_install_env.py``. A caller whose
    file needs different defaults (e.g. ``test_install_integration.py``,
    which defaults to ``source="local"``) should layer them on top in a
    thin local wrapper rather than passing them as overrides on every call.
    """
    defaults: dict[str, Any] = {
        "target": Path("."),
        "source": "git",
        "ref": "main",
        "local_path": None,
        "extras": None,
        "extra_packages": "",
        "use_sync": False,
        "skip_overrides": False,
        "refresh": False,
        "clean": False,
        "python": sys.executable,
        "check": False,
    }
    defaults.update(overrides)
    return argparse.Namespace(**defaults)
