"""Resolve ``${VAR}`` placeholders the way Claude Code does in ``.mcp.json``.

Semantics:

- ``${VAR}`` is replaced by the value of ``VAR``.
- ``${VAR:-default}`` uses ``default`` only when ``VAR`` is unset; an empty
  value counts as set.
- An unresolved ``${VAR}`` stays literal and its name is reported.
- Single pass: replacement values and default text are not expanded again.

Lookup order is the caller's ``env_vars`` first, then ``os.environ``.
``mcp-coder verify`` and the LangChain MCP config loader share this resolver,
so both agree on what a placeholder resolves to.
"""

import os
import re
from collections.abc import Mapping

_PLACEHOLDER_PATTERN = re.compile(r"\$\{([^}]+?)(?::-([^}]*))?\}")


def resolve_placeholders(
    value: str,
    env_vars: Mapping[str, str] | None = None,
    *,
    case_insensitive: bool | None = None,
) -> tuple[str, list[str]]:
    """Expand ``${VAR}`` / ``${VAR:-default}`` like Claude Code does in ``.mcp.json``.

    Args:
        value: String that may contain placeholders.
        env_vars: Extra variables; they take precedence over ``os.environ``.
        case_insensitive: Match ``env_vars`` keys case-insensitively.
            ``None`` uses the platform default (``True`` on Windows).
            ``os.environ`` is queried directly and keeps its own casing rules.

    Returns:
        The resolved string and the names that could not be resolved,
        in first-seen order without duplicates.
    """
    ci = (os.name == "nt") if case_insensitive is None else case_insensitive
    extra: dict[str, str] = (
        {k.upper(): v for k, v in (env_vars or {}).items()}
        if ci
        else dict(env_vars or {})
    )
    unresolved: list[str] = []

    def _replacer(match: re.Match[str]) -> str:
        name, default = match.group(1), match.group(2)
        key = name.upper() if ci else name
        if key in extra:
            return extra[key]
        if name in os.environ:
            return os.environ[name]
        if default is not None:
            return default
        if name not in unresolved:
            unresolved.append(name)
        return match.group(0)

    return _PLACEHOLDER_PATTERN.sub(_replacer, value), unresolved
