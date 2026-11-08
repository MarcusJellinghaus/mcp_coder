"""Toolkit configuration and runner.

Reads ``[tool.mcp-coder.toolkit]`` from ``pyproject.toml``, else from a root
``mcp-coder.toml``. Every config problem raises ``ValueError`` naming the file
and the offending key or value; callers map it to their own error.
"""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .toml_utils import load_toml

DEFAULT_TOOLKIT = "mcp-tools-py"

DEFAULT_BINDINGS: dict[str, tuple[str, ...]] = {
    "implement_task": (),
    "implement_final": ("check@quick",),
    "commit": ("format@apply",),
    "rebase": ("check@standard", "test@standard"),
    "rebase_automated": ("check@standard", "test@unattended"),
}

_ALLOWED_ACTIONS: dict[str, frozenset[str]] = {
    "implement_task": frozenset(),
    "implement_final": frozenset({"check"}),
    "commit": frozenset({"format"}),
    "rebase": frozenset({"check", "test"}),
    "rebase_automated": frozenset({"check", "test"}),
}

# Requests the commit entry may never make, although the action is allowed
_FORBIDDEN_REQUESTS: dict[str, frozenset[str]] = {
    "commit": frozenset({"format@check"}),
}

_REQUEST_RE = re.compile(r"^[a-z][a-z0-9_-]*@[a-z][a-z0-9_-]*$")
_CONFIG_FILES = ("pyproject.toml", "mcp-coder.toml")
_TABLE = "[tool.mcp-coder.toolkit]"
_RESERVED_KEYS = frozenset({"toolkit", "bindings", "params"})
# Per-action keys are reserved for a later version of the config format
_PER_ACTION_KEYS = frozenset({"format", "check", "test"})


@dataclass(frozen=True)
class ToolkitConfig:
    """Resolved [tool.mcp-coder.toolkit] configuration."""

    toolkit: str  # entry-point key
    bindings: dict[str, tuple[str, ...]]  # every entry, defaults merged
    params: dict[str, dict[str, Any]]  # raw [..toolkit.params] tables
    section: dict[str, Any]  # [tool.mcp-coder.toolkit.<toolkit>] or {}
    source: str | None  # file name the table came from, None = default


def _validate_bindings(source: str, raw: Any) -> dict[str, tuple[str, ...]]:
    """Validate [tool.mcp-coder.toolkit.bindings].

    Args:
        source: Config file name, named in errors.
        raw: The raw TOML value.

    Returns:
        The validated entries as tuples of requests.

    Raises:
        ValueError: If the table, an entry or a request is invalid.
    """
    if not isinstance(raw, dict):
        raise ValueError(
            f"Invalid {_TABLE} bindings in {source}: expected a table, "
            f"got {type(raw).__name__}: {raw!r}"
        )
    bindings: dict[str, tuple[str, ...]] = {}
    for entry, value in raw.items():
        if entry not in DEFAULT_BINDINGS:
            raise ValueError(
                f"Unknown {_TABLE} bindings entry {entry!r} in {source}; "
                f"expected one of {', '.join(DEFAULT_BINDINGS)}"
            )
        if not isinstance(value, list) or not all(isinstance(r, str) for r in value):
            raise ValueError(
                f"Invalid {_TABLE} bindings.{entry} in {source}: expected a list "
                f'of "action@depth" strings, got {type(value).__name__}: {value!r}'
            )
        for request in value:
            if not _REQUEST_RE.match(request):
                raise ValueError(
                    f"Invalid request {request!r} in {_TABLE} bindings.{entry} "
                    f'in {source}: expected "action@depth"'
                )
            action = request.split("@", 1)[0]
            allowed = _ALLOWED_ACTIONS[entry]
            if action not in allowed or request in _FORBIDDEN_REQUESTS.get(
                entry, frozenset()
            ):
                expected = ", ".join(sorted(allowed)) if allowed else "nothing"
                raise ValueError(
                    f"Request {request!r} not allowed in {_TABLE} bindings.{entry} "
                    f"in {source}; this entry can act on: {expected}"
                )
        bindings[entry] = tuple(value)
    return bindings


def _validate_params(source: str, raw: Any) -> dict[str, dict[str, Any]]:
    """Validate the shape of [tool.mcp-coder.toolkit.params].

    Values are checked against the toolkit's schema when it is loaded.

    Args:
        source: Config file name, named in errors.
        raw: The raw TOML value.

    Returns:
        The params tables, keyed by action.

    Raises:
        ValueError: If params is not a table of tables.
    """
    if not isinstance(raw, dict):
        raise ValueError(
            f"Invalid {_TABLE} params in {source}: expected a table, "
            f"got {type(raw).__name__}: {raw!r}"
        )
    for action, value in raw.items():
        if not isinstance(value, dict):
            raise ValueError(
                f"Invalid {_TABLE} params.{action} in {source}: expected a table, "
                f"got {type(value).__name__}: {value!r}"
            )
    return dict(raw)


def load_toolkit_config(project_dir: Path) -> ToolkitConfig:
    """Read and validate [tool.mcp-coder.toolkit].

    Args:
        project_dir: Project root containing pyproject.toml / mcp-coder.toml.

    Returns:
        The resolved ToolkitConfig; defaults when no file defines the table.

    Raises:
        ValueError: If a config file is malformed, both files define the
            table, or the table is invalid. The message names the file.
    """
    tables: dict[str, Any] = {}
    for file_name in _CONFIG_FILES:
        data = load_toml(project_dir / file_name, strict=True)
        table = data.get("tool", {}).get("mcp-coder", {}).get("toolkit")
        if table is not None:
            tables[file_name] = table

    if len(tables) == 2:
        raise ValueError(
            f"Both {' and '.join(_CONFIG_FILES)} in {project_dir} define "
            f"{_TABLE}; keep one"
        )
    if not tables:
        return ToolkitConfig(DEFAULT_TOOLKIT, dict(DEFAULT_BINDINGS), {}, {}, None)

    source, table = next(iter(tables.items()))
    if not isinstance(table, dict):
        raise ValueError(
            f"Invalid {_TABLE} in {source}: expected a table, "
            f"got {type(table).__name__}: {table!r}"
        )

    name: Any = table.get("toolkit", DEFAULT_TOOLKIT)
    if not isinstance(name, str):
        raise ValueError(
            f"Invalid {_TABLE} toolkit in {source}: expected a string, "
            f"got {type(name).__name__}: {name!r}"
        )
    if name in ("bindings", "params"):
        raise ValueError(
            f"Invalid {_TABLE} toolkit {name!r} in {source}: {name!r} is a reserved key"
        )

    for key in table:
        if key in _PER_ACTION_KEYS:
            raise ValueError(
                f"Unsupported {_TABLE} key {key!r} in {source}: per-action "
                "toolkits are not supported yet"
            )
        if key not in _RESERVED_KEYS and key != name:
            raise ValueError(
                f"Unknown {_TABLE} key {key!r} in {source}; expected toolkit, "
                f"bindings, params or {name}"
            )

    section: Any = table.get(name, {})
    if not isinstance(section, dict):
        raise ValueError(
            f"Invalid [tool.mcp-coder.toolkit.{name}] in {source}: expected a "
            f"table, got {type(section).__name__}: {section!r}"
        )

    bindings = DEFAULT_BINDINGS | _validate_bindings(source, table.get("bindings", {}))
    params = _validate_params(source, table.get("params", {}))
    return ToolkitConfig(name, bindings, params, section, source)


def get_binding(project_dir: Path, entry: str) -> tuple[str, ...]:
    """Return the requests bound to one workflow entry.

    Args:
        project_dir: Project root containing the config.
        entry: Binding entry name, one of DEFAULT_BINDINGS.

    Returns:
        The configured (or default) requests for the entry.
    """
    return load_toolkit_config(project_dir).bindings[entry]
