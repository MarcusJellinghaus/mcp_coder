"""Project setup configuration.

Reads ``[tool.mcp-coder.setup]`` from ``pyproject.toml``, else from a root
``mcp-coder.toml`` (via ``toml_utils.find_mcp_coder_table``). The table holds
``steps``, an ordered list of ``{argv | builtin, name, timeout}`` tables.
Without the table, a project with a ``pyproject.toml`` gets the ``python``
built-in; any other project has no steps. Every config problem raises
``ValueError`` naming the file, the step and the offending key or value.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .toml_utils import find_mcp_coder_table

BUILTINS = frozenset({"python"})
DEFAULT_STEP_TIMEOUT = 1800

_TABLE = "[tool.mcp-coder.setup]"
_STEP_KEYS = frozenset({"argv", "builtin", "name", "timeout"})


@dataclass(frozen=True)
class SetupStep:
    """One setup step: a command line or a built-in."""

    argv: tuple[str, ...] | None  # exactly one of argv / builtin is set
    builtin: str | None
    name: str | None
    timeout: int  # seconds; DEFAULT_STEP_TIMEOUT for built-in steps

    @property
    def label(self) -> str:
        """Name shown for the step: name, else built-in, else the command line."""
        if self.name is not None:
            return self.name
        if self.builtin is not None:
            return self.builtin
        return " ".join(self.argv or ())


@dataclass(frozen=True)
class SetupConfig:
    """Resolved [tool.mcp-coder.setup] configuration."""

    steps: tuple[SetupStep, ...]
    source: str | None  # file name the table came from, None = default

    def uses_python(self) -> bool:
        """Return True if any step is the ``python`` built-in."""
        return any(step.builtin == "python" for step in self.steps)


def _invalid(source: str, where: str, expected: str, value: Any) -> str:
    """Build the standard "Invalid ..." error message.

    Args:
        source: Config file name.
        where: Key path inside the table, e.g. ``steps[2].argv``.
        expected: What the value should have been.
        value: The offending raw value.

    Returns:
        The message for the ValueError.
    """
    return (
        f"Invalid {_TABLE} {where} in {source}: expected {expected}, "
        f"got {type(value).__name__}: {value!r}"
    )


def _parse_step(source: str, index: int, raw: Any) -> SetupStep:
    """Validate one entry of ``steps``.

    Args:
        source: Config file name, named in errors.
        index: Position of the step in ``steps``.
        raw: The raw TOML value.

    Returns:
        The validated step.

    Raises:
        ValueError: If the step or one of its keys is invalid.
    """
    where = f"steps[{index}]"
    if not isinstance(raw, dict):
        raise ValueError(_invalid(source, where, "a table", raw))
    for key in raw:
        if key not in _STEP_KEYS:
            raise ValueError(
                f"Unknown {_TABLE} key {key!r} in {where} in {source}; "
                "expected argv, builtin, name or timeout"
            )
    if ("argv" in raw) == ("builtin" in raw):
        raise ValueError(
            f"Invalid {_TABLE} {where} in {source}: set exactly one of argv or builtin"
        )

    name: Any = raw.get("name")
    if name is not None and not isinstance(name, str):
        raise ValueError(_invalid(source, f"{where}.name", "a string", name))

    if "builtin" in raw:
        builtin: Any = raw["builtin"]
        if not isinstance(builtin, str) or builtin not in BUILTINS:
            expected = f"one of {', '.join(sorted(BUILTINS))}"
            raise ValueError(_invalid(source, f"{where}.builtin", expected, builtin))
        if "timeout" in raw:
            raise ValueError(
                f"Invalid {_TABLE} {where} in {source}: timeout is only "
                "allowed with argv"
            )
        return SetupStep(None, builtin, name, DEFAULT_STEP_TIMEOUT)

    argv: Any = raw["argv"]
    if (
        not isinstance(argv, list)
        or not argv
        or not all(isinstance(arg, str) for arg in argv)
    ):
        raise ValueError(
            _invalid(source, f"{where}.argv", "a non-empty list of strings", argv)
        )

    timeout: Any = raw.get("timeout", DEFAULT_STEP_TIMEOUT)
    if isinstance(timeout, bool) or not isinstance(timeout, int) or timeout <= 0:
        raise ValueError(
            _invalid(source, f"{where}.timeout", "a positive integer", timeout)
        )

    return SetupStep(tuple(argv), None, name, timeout)


def load_setup_config(project_dir: Path) -> SetupConfig:
    """Read and validate [tool.mcp-coder.setup].

    Args:
        project_dir: Project root containing pyproject.toml / mcp-coder.toml.

    Returns:
        The resolved SetupConfig. Without the table: the ``python`` built-in
        if the project has a pyproject.toml, else no steps.

    Raises:
        ValueError: If a config file is malformed, both files define the
            table, or the table is invalid. The message names the file.
    """
    found = find_mcp_coder_table(project_dir, "setup")
    if found is None:
        if (project_dir / "pyproject.toml").is_file():
            default = SetupStep(None, "python", None, DEFAULT_STEP_TIMEOUT)
            return SetupConfig((default,), None)
        return SetupConfig((), None)

    source, table = found
    if not isinstance(table, dict):
        raise ValueError(
            f"Invalid {_TABLE} in {source}: expected a table, "
            f"got {type(table).__name__}: {table!r}"
        )
    for key in table:
        if key != "steps":
            raise ValueError(
                f"Unknown {_TABLE} key {key!r} in {source}; expected steps"
            )
    if "steps" not in table:
        raise ValueError(f"Missing {_TABLE} key 'steps' in {source}")

    steps: Any = table["steps"]
    if not isinstance(steps, list):
        raise ValueError(_invalid(source, "steps", "a list of tables", steps))
    return SetupConfig(
        tuple(_parse_step(source, i, raw) for i, raw in enumerate(steps)), source
    )
