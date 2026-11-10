"""Toolkit configuration and runner.

Reads ``[tool.mcp-coder.toolkit]`` from ``pyproject.toml``, else from a root
``mcp-coder.toml``. Every config problem raises ``ValueError`` naming the file
and the offending key or value; callers map it to their own error.

The runner part looks the toolkit up in the ``mcp_coder.toolkits`` entry-point
group, validates the configured params against its schema, and runs
``action@depth`` requests. Exceptions from ``run()`` become ``error`` results;
load and ``verify()`` problems raise ``ValueError``.
"""

import logging
import os
import re
from collections.abc import Sequence
from dataclasses import dataclass
from importlib.metadata import entry_points
from pathlib import Path
from typing import Any

from .toml_utils import load_toml
from .toolkit import (
    ActionRequest,
    ActionResult,
    Toolkit,
    ToolkitInfo,
    VerifyItem,
    validate_params,
)

logger = logging.getLogger(__name__)

DEFAULT_TOOLKIT = "mcp-tools-py"
ENTRY_POINT_GROUP = "mcp_coder.toolkits"

# Depths that fall back to the nearest lower declared one, lowest first
_STANDARD_DEPTHS = ("quick", "standard", "full")

DEFAULT_BINDINGS: dict[str, tuple[str, ...]] = {
    "implement_task": ("check@quick",),
    "implement_final": ("check@standard", "test@quick"),
    "commit": ("format@apply",),
    "rebase": ("check@standard", "test@standard"),
    "rebase_automated": ("check@standard", "test@unattended"),
}

_ALLOWED_ACTIONS: dict[str, frozenset[str]] = {
    "implement_task": frozenset({"check", "test"}),
    "implement_final": frozenset({"check", "test"}),
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

_BASH_PREFIX = "Bash("
# Warn once per process when Bash grants are dropped for a non-Claude provider
_bash_drop_warned = False


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
        data: Any = load_toml(project_dir / file_name, strict=True)
        for key in ("tool", "mcp-coder"):
            data = data.get(key, {})
            if not isinstance(data, dict):
                raise ValueError(
                    f"Invalid {key!r} in {file_name}: expected a table, "
                    f"got {type(data).__name__}: {data!r}"
                )
        table = data.get("toolkit")
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


@dataclass(frozen=True)
class LoadedToolkit:
    """A constructed toolkit with its description and config."""

    name: str  # entry-point key
    toolkit: Toolkit
    info: ToolkitInfo
    config: ToolkitConfig


def _toolkit_class(name: str) -> type[Toolkit]:
    """Look a toolkit class up in the mcp_coder.toolkits entry-point group.

    Args:
        name: Entry-point name.

    Returns:
        The loaded toolkit class.

    Raises:
        ValueError: If no entry point has the name, or loading it fails.
    """
    registered = list(entry_points(group=ENTRY_POINT_GROUP))
    for entry_point in registered:
        if entry_point.name == name:
            try:
                cls: type[Toolkit] = entry_point.load()
            except Exception as exc:
                raise ValueError(f"Toolkit '{name}' failed to load: {exc}") from exc
            return cls
    names = ", ".join(sorted(ep.name for ep in registered)) or "none"
    raise ValueError(
        f"Toolkit '{name}' is not registered in the {ENTRY_POINT_GROUP} "
        f"entry-point group; registered: {names}"
    )


def _request_params(loaded: LoadedToolkit, action: str, depth: str) -> dict[str, Any]:
    """Merge the configured params for one action and depth.

    Args:
        loaded: The loaded toolkit.
        action: Action name, declared by the toolkit.
        depth: Depth name.

    Returns:
        The action table without its depth sub-tables, overridden by the
        depth's sub-table.
    """
    table = loaded.config.params.get(action, {})
    depths = loaded.info.actions[action]
    base = {k: v for k, v in table.items() if k not in depths}
    overrides: dict[str, Any] = table.get(depth, {})
    return base | overrides


def load_toolkit(project_dir: Path) -> LoadedToolkit:
    """Load the configured toolkit and validate its params.

    Args:
        project_dir: Project root containing the config.

    Returns:
        The constructed toolkit with its description and config.

    Raises:
        ValueError: If the config is invalid, the toolkit isn't registered or
            fails to construct or describe itself, or the params are invalid.
    """
    config = load_toolkit_config(project_dir)
    name = config.toolkit
    cls = _toolkit_class(name)
    try:
        toolkit = cls(config.section)
        info = toolkit.describe()
    except Exception as exc:
        raise ValueError(f"Toolkit '{name}' failed to load: {exc}") from exc

    loaded = LoadedToolkit(name, toolkit, info, config)
    for action, table in config.params.items():
        if action not in info.actions:
            raise ValueError(
                f"{_TABLE} params.{action} in {config.source}: toolkit '{name}' "
                f"declares no action {action!r}; declared: {', '.join(info.actions)}"
            )
        for depth in info.actions[action]:
            if not isinstance(table.get(depth, {}), dict):
                raise ValueError(
                    f"Invalid {_TABLE} params.{action}.{depth} in {config.source}: "
                    "expected a table"
                )
            try:
                validate_params(
                    info.params_schema, _request_params(loaded, action, depth)
                )
            except ValueError as exc:
                raise ValueError(
                    f"{_TABLE} params for {action}@{depth} in {config.source}: {exc}"
                ) from exc
    return loaded


def _resolve_depth(declared: list[str], depth: str) -> str | None:
    """Pick the depth to run for a requested one.

    Args:
        declared: Depths the toolkit declares for the action.
        depth: Requested depth.

    Returns:
        The depth itself if declared; for an undeclared standard depth, the
        nearest lower declared standard depth; otherwise None.
    """
    if depth in declared:
        return depth
    if depth not in _STANDARD_DEPTHS:
        return None
    lower = _STANDARD_DEPTHS[: _STANDARD_DEPTHS.index(depth)]
    for candidate in reversed(lower):
        if candidate in declared:
            return candidate
    return None


def run_request(loaded: LoadedToolkit, project_dir: Path, request: str) -> ActionResult:
    """Run one ``action@depth`` request.

    Args:
        loaded: The loaded toolkit.
        project_dir: Project root to run in.
        request: The ``action@depth`` request.

    Returns:
        The toolkit's result; status "error" if the action or depth can't be
        run or ``run()`` raises.
    """
    action, depth = request.split("@")
    declared = loaded.info.actions.get(action)
    resolved = _resolve_depth(declared, depth) if declared else None
    if resolved is None:
        return ActionResult(
            "error", f"{request}: not declared by toolkit '{loaded.name}'"
        )
    if resolved != depth:
        logger.info("%s: depth %s not declared, running %s", action, depth, resolved)
    try:
        return loaded.toolkit.run(
            ActionRequest(
                action, resolved, project_dir, _request_params(loaded, action, resolved)
            )
        )
    except Exception as exc:  # pylint: disable=broad-exception-caught
        return ActionResult("error", f"{request} raised: {exc}")


def run_binding(
    loaded: LoadedToolkit, project_dir: Path, entry: str
) -> list[tuple[str, ActionResult]]:
    """Run every request bound to a workflow entry, in order.

    Args:
        loaded: The loaded toolkit.
        project_dir: Project root to run in.
        entry: Binding entry name, one of DEFAULT_BINDINGS.

    Returns:
        ``(request, result)`` pairs in binding order.
    """
    return [
        (request, run_request(loaded, project_dir, request))
        for request in loaded.config.bindings[entry]
    ]


def verify_toolkit(
    loaded: LoadedToolkit, project_dir: Path, action: str | None
) -> list[VerifyItem]:
    """Run the toolkit's own verification.

    Args:
        loaded: The loaded toolkit.
        project_dir: Project root to check.
        action: Action to check, or None for everything.

    Returns:
        The toolkit's verify items.

    Raises:
        ValueError: If ``verify()`` raises.
    """
    try:
        return list(loaded.toolkit.verify(project_dir, action))
    except Exception as exc:
        raise ValueError(f"Toolkit '{loaded.name}' verify failed: {exc}") from exc


def get_fragment(loaded: LoadedToolkit, name: str) -> str:
    """Return one prompt fragment contributed by the toolkit.

    Args:
        loaded: The loaded toolkit.
        name: Fragment name.

    Returns:
        The fragment, or "" if absent or ``prompt_fragments()`` raises.
    """
    try:
        return loaded.toolkit.prompt_fragments().get(name, "")
    except Exception as exc:  # pylint: disable=broad-exception-caught
        logger.warning("Toolkit '%s' prompt_fragments failed: %s", loaded.name, exc)
        return ""


def llm_permissions(
    project_dir: Path, provider: str, entry: str | None = None
) -> list[str]:
    """Permission strings the LLM session gets from the loaded toolkit.

    Args:
        project_dir: Project root containing the config.
        provider: LLM provider; empty falls back to MCP_CODER_LLM_PROVIDER,
            then "claude", as in prompt_llm.
        entry: Binding entry whose requests scope the permissions, or None
            for the union over every action and depth.

    Returns:
        The deduplicated permissions in declaration order. ``Bash(`` entries
        are dropped for non-Claude providers; empty if the toolkit fails to
        load.
    """
    global _bash_drop_warned  # pylint: disable=global-statement
    try:
        loaded = load_toolkit(project_dir)
    except ValueError as exc:
        logger.warning("No toolkit grants: %s", exc)
        return []

    perms = loaded.info.llm_permissions
    pairs: list[tuple[str, str]] = []
    if entry is None:
        pairs = [
            (action, depth) for action, depths in perms.items() for depth in depths
        ]
    else:
        for request in loaded.config.bindings[entry]:
            action, depth = request.split("@", 1)
            resolved = _resolve_depth(loaded.info.actions.get(action, []), depth)
            if resolved is not None:
                pairs.append((action, resolved))

    out: list[str] = []
    for action, depth in pairs:
        for permission in perms.get(action, {}).get(depth, []):
            if permission not in out:
                out.append(permission)

    provider = provider or os.environ.get("MCP_CODER_LLM_PROVIDER") or "claude"
    if provider != "claude" and bash_grants_of(out):
        if not _bash_drop_warned:
            logger.warning(
                "Bash grants dropped for provider %s: the LLM cannot re-run the "
                "toolkit's checks",
                provider,
            )
            _bash_drop_warned = True
        out = [p for p in out if not p.startswith(_BASH_PREFIX)]
    return out


def bash_grants_of(permissions: Sequence[str]) -> list[str]:
    """Keep only the ``Bash(...)`` entries.

    Args:
        permissions: Permission strings, e.g. from llm_permissions.

    Returns:
        The ``Bash(...)`` entries, in order.
    """
    return [p for p in permissions if p.startswith(_BASH_PREFIX)]
