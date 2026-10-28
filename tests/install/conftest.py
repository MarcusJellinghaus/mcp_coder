"""Shared test helpers for ``tests/install``.

Not a fixture module in the pytest-DI sense: ``namespace`` is a plain
function the test modules call directly with varying keyword overrides,
and is imported explicitly where needed.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any


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
