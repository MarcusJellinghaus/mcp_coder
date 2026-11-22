"""Toolkit rows of the verify command's PROJECT section.

Holds the Toolkit row, the toolkit's verify items per requested action, one
row per requested depth the toolkit doesn't declare, and the row for the
retired ``[tool.mcp-coder.implement] check_type_hints`` key. Same
one-directional shape as ``verify_setup``: nothing here reaches back into
``verify_sections`` or ``verify.py``.
"""

import json
from pathlib import Path

from ...utils.pyproject_config import get_format_code, get_leftover_check_type_hints
from ...utils.toolkit import VerifyItem
from ...utils.toolkit_runner import (
    LoadedToolkit,
    load_toolkit,
    load_toolkit_config,
    resolve_depth,
    verify_toolkit,
)
from .verify_formatting import Row
from .verify_render import SectionBuilder

# Implement entries the retired key used to filter
_IMPLEMENT_ENTRIES: tuple[str, ...] = ("implement_task", "implement_final")

# VerifyItem.status mapped to the symbols-dict key it prints with
_VERIFY_STATUS_SYMBOL: dict[str, str] = {
    "ok": "success",
    "warning": "warning",
    "error": "failure",
}

# Identity of an item when comparing across actions: (name, status, message)
_ItemKey = tuple[str, str, str]


def _formatting_enabled(project_dir: Path) -> bool:
    """Return ``format_code``; an invalid value counts as enabled.

    The format_code row already reports the invalid value.
    """
    try:
        return get_format_code(project_dir).enabled
    except ValueError:
        return True


def _requests(
    bindings: dict[str, tuple[str, ...]], formatting: bool
) -> dict[tuple[str, str], list[str]]:
    """Collect the distinct requests of the bindings.

    Args:
        bindings: Binding entries mapped to their ``action@depth`` requests.
        formatting: Whether ``format_code`` is on; ``commit`` counts only then.

    Returns:
        ``(action, depth)`` mapped to the binding entries requesting it, both
        in first-seen order.
    """
    requests: dict[tuple[str, str], list[str]] = {}
    for entry, entry_requests in bindings.items():
        if entry == "commit" and not formatting:
            continue
        for request in entry_requests:
            action, depth = request.split("@", 1)
            entries = requests.setdefault((action, depth), [])
            if entry not in entries:
                entries.append(entry)
    return requests


def _key(item: VerifyItem) -> _ItemKey:
    """Return the identity of *item* used to find items shared by actions."""
    return (item.name, item.status, item.message)


def _depth_row(
    loaded: LoadedToolkit,
    action: str,
    depth: str,
    entries: list[str],
    symbols: dict[str, str],
    indent: int,
) -> Row | None:
    """Return the row for one requested depth, or None when it is declared.

    Args:
        loaded: The loaded toolkit.
        action: Requested action.
        depth: Requested depth.
        entries: Binding entries requesting ``action@depth``.
        symbols: Dict with 'success', 'failure', 'warning' keys.
        indent: Number of leading spaces.

    Returns:
        An error row when the action or depth can't run, a warning row when a
        lower depth runs instead, None when the depth is declared.
    """
    by = f"(requested by {', '.join(entries)})"
    label = f"{action}@{depth}"
    declared = loaded.info.actions.get(action)
    if declared is None:
        message = f"action not declared by toolkit '{loaded.name}' {by}"
        return Row(label, symbols["failure"], message, indent, wrap=True)
    resolved = resolve_depth(declared, depth)
    if resolved == depth:
        return None
    if resolved is not None:
        message = f"not declared; runs {resolved} {by}"
        return Row(label, symbols["warning"], message, indent, wrap=True)
    return Row(label, symbols["failure"], f"not declared {by}", indent, wrap=True)


def toolkit_rows(
    project_dir: Path, symbols: dict[str, str], out: SectionBuilder, *, indent: int = 4
) -> bool:
    """Add the Toolkit row, the global items, then one group per requested action.

    ``verify()`` runs once per requested action the toolkit declares; ``commit``
    requests count only while ``format_code`` is on. When two or more actions
    return items, the items every one of them returns are shown once as global
    items, and the other ``check`` / ``test`` errors are shown as warnings.

    Args:
        project_dir: Path to the project directory.
        symbols: Dict with 'success', 'failure', 'warning' keys.
        out: Builder the rows are added to.
        indent: Number of leading spaces of the Toolkit row.

    Returns:
        False if the toolkit fails to load or any added row is an error.
    """
    try:
        loaded = load_toolkit(project_dir)
    except ValueError as exc:
        out.add(Row("Toolkit", symbols["failure"], str(exc), indent))
        return False
    out.add(Row("Toolkit", symbols["success"], loaded.name, indent))

    requests = _requests(loaded.config.bindings, _formatting_enabled(project_dir))
    actions = list(dict.fromkeys(action for action, _ in requests))
    returned: dict[str, list[VerifyItem]] = {}
    raised: dict[str, str] = {}
    for action in actions:
        if action not in loaded.info.actions:
            continue
        try:
            returned[action] = verify_toolkit(loaded, project_dir, action)
        except ValueError as exc:
            raised[action] = str(exc)

    multi = len(returned) >= 2
    shared: set[_ItemKey] = set()
    if multi:
        shared = set.intersection(
            *({_key(item) for item in items} for items in returned.values())
        )

    rows: list[Row] = []
    shown: set[_ItemKey] = set()
    for items in returned.values():
        for item in items:
            if _key(item) in shared and _key(item) not in shown:
                shown.add(_key(item))
                rows.append(
                    Row(
                        item.name,
                        symbols[_VERIFY_STATUS_SYMBOL[item.status]],
                        item.message or item.status,
                        indent + 2,
                    )
                )
    out.add(*rows)
    ok = all(row.marker != symbols["failure"] for row in rows)

    for action in actions:
        group: list[Row] = []
        if action in raised:
            severity = "failure" if action == "format" else "warning"
            group.append(
                Row("verify", symbols[severity], raised[action], indent + 4, wrap=True)
            )
        for item in returned.get(action, []):
            if _key(item) in shared:
                continue
            status = item.status
            if multi and action != "format" and status == "error":
                status = "warning"
            group.append(
                Row(
                    item.name,
                    symbols[_VERIFY_STATUS_SYMBOL[status]],
                    item.message or item.status,
                    indent + 4,
                )
            )
        for (req_action, depth), entries in requests.items():
            if req_action != action:
                continue
            row = _depth_row(loaded, action, depth, entries, symbols, indent + 4)
            if row is not None:
                group.append(row)
        if group:
            out.add(" " * (indent + 2) + action, *group)
            ok = ok and all(row.marker != symbols["failure"] for row in group)
    return ok


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
