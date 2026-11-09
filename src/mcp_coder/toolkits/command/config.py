"""Pure parser for the `[tool.mcp-coder.toolkit.command]` config table.

One validator feeds `describe`, `verify` and `run`, so they never disagree.
`parse_config` never raises and never touches the filesystem; problems are
collected as `Problem` items, tagged global or `(action, depth)`.
"""

import os
import shlex
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Literal

ACTIONS = ("format", "check", "test")
PARSERS = ("exit-code", "junit")
STATUSES = ("ok", "findings", "skipped", "error")
LLM_PERMISSIONS = ("bash", "none")
DEFAULT_EXIT_CODES: dict[int, str] = {0: "ok", 1: "findings"}
DEFAULT_TIMEOUT = 600

_DEFAULT_KEYS = ("llm_permissions", "parser", "exit_codes", "timeout")
_STEP_KEYS = ("argv", "name", "parser", "exit_codes", "timeout", "report")
_GLOBAL_NAME = "command"


@dataclass(frozen=True)
class Step:
    """One well-formed step of an action depth."""

    argv: tuple[str, ...]
    name: str | None
    parser: str
    exit_codes: dict[int, str]
    timeout: int
    report: str | None
    grant: str | None

    @property
    def label(self) -> str:
        """The step's name, else its argv joined by spaces."""
        return self.name if self.name is not None else " ".join(self.argv)


@dataclass(frozen=True)
class Problem:
    """A config problem; `scope` is None for global ones."""

    scope: tuple[str, str] | None
    status: Literal["error", "warning"]
    name: str
    message: str


@dataclass(frozen=True)
class ParsedConfig:
    """Well-formed steps per action and depth, plus every problem found."""

    steps: dict[str, dict[str, list[Step]]]
    problems: list[Problem]

    def global_errors(self) -> list[Problem]:
        """Return the errors that are not tied to an action and depth.

        Returns:
            Global problems with status ``error``.
        """
        return [p for p in self.problems if p.scope is None and p.status == "error"]

    def errors_for(self, action: str, depth: str) -> list[Problem]:
        """Return the errors scoped to `(action, depth)`.

        Returns:
            Problems of that scope with status ``error``; warnings are excluded.
        """
        return [
            p
            for p in self.problems
            if p.scope == (action, depth) and p.status == "error"
        ]


@dataclass(frozen=True)
class _Defaults:
    llm_permissions: str | None  # None when the configured value is invalid
    parser: str
    exit_codes: dict[int, str]
    timeout: int


def _exit_codes_errors(value: Any) -> tuple[dict[int, str], list[str]]:
    if not isinstance(value, Mapping):
        return {}, [f"exit_codes must be a table, got {value!r}"]
    table: dict[int, str] = {}
    errors: list[str] = []
    for key, status in value.items():
        try:
            if isinstance(key, bool):
                raise ValueError
            code = int(key)
        except (TypeError, ValueError):
            errors.append(f"exit_codes key must be an integer, got {key!r}")
            continue
        if status not in STATUSES:
            errors.append(
                f"exit_codes value for {key!r} must be one of "
                f"{', '.join(STATUSES)}, got {status!r}"
            )
            continue
        table[code] = status
    return table, errors


def _timeout_error(value: Any) -> str | None:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        return f"timeout must be a positive integer, got {value!r}"
    return None


def _parser_error(value: Any) -> str | None:
    if value not in PARSERS:
        return f"parser must be one of {', '.join(PARSERS)}, got {value!r}"
    return None


def _parse_defaults(config: Mapping[str, Any]) -> tuple[_Defaults, list[str]]:
    errors: list[str] = []

    llm_permissions: str | None = config.get("llm_permissions", "bash")
    if llm_permissions not in LLM_PERMISSIONS:
        errors.append(
            f"llm_permissions must be one of {', '.join(LLM_PERMISSIONS)}, "
            f"got {llm_permissions!r}"
        )
        llm_permissions = None

    parser = config.get("parser", "exit-code")
    parser_error = _parser_error(parser)
    if parser_error:
        errors.append(parser_error)
        parser = "exit-code"

    exit_codes = dict(DEFAULT_EXIT_CODES)
    if "exit_codes" in config:
        table, table_errors = _exit_codes_errors(config["exit_codes"])
        errors.extend(table_errors)
        if not table_errors:
            exit_codes = table

    timeout = config.get("timeout", DEFAULT_TIMEOUT)
    timeout_error = _timeout_error(timeout)
    if timeout_error:
        errors.append(timeout_error)
        timeout = DEFAULT_TIMEOUT

    return _Defaults(llm_permissions, parser, exit_codes, timeout), errors


def _safe(element: str) -> bool:
    return shlex.quote(element) == element and "," not in element


def _report_error(report: Any) -> str | None:
    if not isinstance(report, str) or not report:
        return f"report must be a non-empty string, got {report!r}"
    posix = report.replace("\\", "/")
    if posix.startswith("/") or (len(posix) >= 2 and posix[1] == ":"):
        return f"report must be relative to the project, got {report!r}"
    first = os.path.normpath(posix).replace("\\", "/").split("/")[0]
    if first == "..":
        return f"report must be inside the project, got {report!r}"
    return None


def _parse_step(
    raw: Any, defaults: _Defaults
) -> tuple[Step | None, list[str], list[str]]:
    """Return the step (None when malformed), its errors and its warnings."""
    if not isinstance(raw, Mapping):
        return None, [f"step must be a table, got {raw!r}"], []

    errors = [f"unknown key {key!r}" for key in raw if key not in _STEP_KEYS]

    argv: Any = raw.get("argv")
    if "argv" not in raw:
        errors.append("argv is required")
    elif not isinstance(argv, list):
        errors.append(f"argv must be a list of strings, got {argv!r}")
    elif not argv:
        errors.append("argv must not be empty")
    elif not all(isinstance(a, str) for a in argv):
        errors.append(f"argv elements must be strings, got {argv!r}")

    name = raw.get("name")
    if name is not None and not isinstance(name, str):
        errors.append(f"name must be a string, got {name!r}")

    parser = raw.get("parser", defaults.parser)
    parser_error = _parser_error(parser)
    if parser_error:
        errors.append(parser_error)

    exit_codes = defaults.exit_codes
    if "exit_codes" in raw:
        exit_codes, table_errors = _exit_codes_errors(raw["exit_codes"])
        errors.extend(table_errors)

    timeout = raw.get("timeout", defaults.timeout)
    timeout_error = _timeout_error(timeout)
    if timeout_error:
        errors.append(timeout_error)

    report = raw.get("report")
    if not parser_error:
        if parser == "junit" and "report" not in raw:
            errors.append("parser 'junit' requires report")
        elif parser != "junit" and "report" in raw:
            errors.append(f"report is only allowed with parser 'junit', not {parser!r}")
        elif parser == "junit":
            report_error = _report_error(report)
            if report_error:
                errors.append(report_error)

    if errors:
        return None, errors, []

    warnings: list[str] = []
    grant: str | None = None
    if defaults.llm_permissions == "bash":
        unsafe = [a for a in argv if not _safe(a)]
        if unsafe:
            warnings.append(
                f"argument {unsafe[0]!r} is not shell-safe; "
                "the step runs without a grant"
            )
        else:
            grant = f"Bash({' '.join(argv)})"

    step = Step(
        argv=tuple(argv),
        name=name,
        parser=parser,
        exit_codes=dict(exit_codes),
        timeout=timeout,
        report=report,
        grant=grant,
    )
    return step, [], warnings


def parse_config(config: Mapping[str, Any]) -> ParsedConfig:
    """Parse the command toolkit config; never raises.

    Every declared depth appears in `steps`, even when all its steps are
    malformed, so a request for it reaches `run` and fails there.

    Returns:
        The well-formed steps per action and depth, in config order, and all
        problems found.
    """
    problems: list[Problem] = []

    def global_error(message: str) -> None:
        problems.append(Problem(None, "error", _GLOBAL_NAME, message))

    defaults, default_errors = _parse_defaults(config)
    for message in default_errors:
        global_error(message)

    for key in config:
        if key not in _DEFAULT_KEYS and key not in ACTIONS:
            global_error(f"unknown top-level key {key!r}")

    steps: dict[str, dict[str, list[Step]]] = {}
    for action, table in config.items():
        if action not in ACTIONS:
            continue
        if not isinstance(table, Mapping):
            global_error(f"{action} must be a table of depths, got {table!r}")
            continue
        depths: dict[str, list[Step]] = {}
        steps[action] = depths
        for depth, raw_steps in table.items():
            depth = str(depth)
            scope = (action, depth)
            depths[depth] = []
            if not isinstance(raw_steps, list):
                name = f"{action}.{depth}"
                problems.append(
                    Problem(
                        scope,
                        "error",
                        name,
                        f"{name}: must be a list of steps, got {raw_steps!r}",
                    )
                )
                continue
            for index, raw_step in enumerate(raw_steps, start=1):
                name = f"{action}.{depth}[{index}]"
                step, errors, warnings = _parse_step(raw_step, defaults)
                for message in errors:
                    problems.append(Problem(scope, "error", name, f"{name}: {message}"))
                for message in warnings:
                    problems.append(
                        Problem(scope, "warning", name, f"{name}: {message}")
                    )
                if step is not None:
                    depths[depth].append(step)

    return ParsedConfig(steps=steps, problems=problems)
