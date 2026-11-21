"""Toolkit rows of the verify command's PROJECT section.

Holds the row for the retired ``[tool.mcp-coder.implement] check_type_hints``
key. Same one-directional shape as ``verify_setup``: nothing here reaches back
into ``verify_sections`` or ``verify.py``.
"""

import json
from pathlib import Path

from ...utils.pyproject_config import get_leftover_check_type_hints
from ...utils.toolkit_runner import load_toolkit_config
from .verify_formatting import Row
from .verify_render import SectionBuilder

# Implement entries the retired key used to filter
_IMPLEMENT_ENTRIES: tuple[str, ...] = ("implement_task", "implement_final")


def check_type_hints_row(
    project_dir: Path, symbols: dict[str, str], out: SectionBuilder
) -> bool:
    """Add the row for a leftover ``check_type_hints`` key.

    ``false`` used to drop the ``check@*`` requests of the implement bindings.
    When those bindings still request checks, the key is an error naming the
    bindings that keep skipping them; otherwise it is a warning.

    Args:
        project_dir: Path to the project directory.
        symbols: Dict with 'success', 'failure', 'warning' keys.
        out: Builder the row is added to.

    Returns:
        False only when the key is ``false`` and an implement binding still
        requests ``check@*``.
    """
    value = get_leftover_check_type_hints(project_dir)
    if value is None:
        return True
    try:
        bindings = load_toolkit_config(project_dir).bindings
    except ValueError:
        # The Toolkit row already reports the broken config
        return True
    fixes = {
        entry: [r for r in bindings[entry] if not r.startswith("check@")]
        for entry in _IMPLEMENT_ENTRIES
        if any(r.startswith("check@") for r in bindings[entry])
    }
    if value is False and fixes:
        settings = ", ".join(f"{e} = {json.dumps(fix)}" for e, fix in fixes.items())
        out.add(
            Row(
                "check_type_hints",
                symbols["failure"],
                "false is retired and checks now run; to keep skipping them set"
                f" under [tool.mcp-coder.toolkit.bindings]: {settings}",
                4,
            )
        )
        return False
    out.add(Row("check_type_hints", symbols["warning"], "retired; remove it", 4))
    return True
