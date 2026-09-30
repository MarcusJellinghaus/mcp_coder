"""Pure ``@group`` token expander for the iCoder permission system.

Expands one matcher token into :class:`Matcher` objects, resolving ``@group``
references transitively against a raw-token-valued group map. Errors are
returned **as data** and are pathless — the caller prefixes the source path
and emits any warning.

Cycles need no detector: one visited-name set shared across the whole
expansion makes every group contribute at most once, and a top-level ref that
expands to zero matchers is an error (covers unknown, empty and cyclic refs).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from mcp_coder.icoder.permissions.matcher import parse_matcher
from mcp_coder.icoder.permissions.model import Matcher

_REF_PREFIX = "@"


def is_ref(token: str) -> bool:
    """Return True if ``token`` is a ``@group`` reference (whitespace-tolerant).

    Args:
        token: A raw matcher token.

    Returns:
        True if the stripped token starts with ``@``.
    """
    return token.strip().startswith(_REF_PREFIX)


def ref_name(token: str) -> str:
    """Return the bare group name of a ``@ref`` token (no leading ``@``).

    Args:
        token: A ``@group`` reference token.

    Returns:
        The group name without surrounding whitespace or the ``@`` prefix.
    """
    return token.strip()[len(_REF_PREFIX) :].strip()


def expand(
    token: str,
    groups: Mapping[str, Sequence[str]],
) -> tuple[list[Matcher], list[str]]:
    """Expand one token into matchers, resolving ``@group`` refs transitively.

    Args:
        token: A matcher token or a ``@group`` reference.
        groups: Merged group map, group name to raw member tokens.

    Returns:
        A ``(matchers, errors)`` tuple. On any error the caller treats the
        token as granting nothing (fail-closed).
    """
    if not is_ref(token):
        return parse_matcher(token)
    matchers, errors = _expand_ref(token, groups, set())
    if not errors and not matchers:
        errors = [
            f"group reference {token.strip()!r} resolves to no tools (empty or cyclic)"
        ]
    return matchers, errors


def expand_group(
    name: str,
    groups: Mapping[str, Sequence[str]],
) -> tuple[list[Matcher], list[str]]:
    """Expand the group stored under the exact key ``name`` (no stripping).

    Args:
        name: A key of ``groups``, used verbatim.
        groups: Merged group map, group name to raw member tokens.

    Returns:
        A ``(matchers, errors)`` tuple for the group's members.
    """
    return _expand_name(name, groups, set())


def _expand_ref(
    token: str,
    groups: Mapping[str, Sequence[str]],
    visited: set[str],
) -> tuple[list[Matcher], list[str]]:
    """Expand one ``@ref`` token via its whitespace-stripped group name.

    Args:
        token: A ``@group`` reference token.
        groups: Merged group map, group name to raw member tokens.
        visited: Group names already expanded; shared and mutated in place.

    Returns:
        A ``(matchers, errors)`` tuple for this ref's members.
    """
    return _expand_name(ref_name(token), groups, visited)


def _expand_name(
    name: str,
    groups: Mapping[str, Sequence[str]],
    visited: set[str],
) -> tuple[list[Matcher], list[str]]:
    """Recursive worker: expand group ``name``, recording visited group names.

    Args:
        name: The exact group key.
        groups: Merged group map, group name to raw member tokens.
        visited: Group names already expanded; shared and mutated in place.

    Returns:
        A ``(matchers, errors)`` tuple for this group's members.
    """
    if name in visited:
        return [], []
    if name not in groups:
        return [], [f"unknown group reference '@{name}'"]
    visited.add(name)
    matchers: list[Matcher] = []
    errors: list[str] = []
    for member in groups[name]:
        if is_ref(member):
            sub_matchers, sub_errors = _expand_ref(member, groups, visited)
        else:
            sub_matchers, sub_errors = parse_matcher(member)
        matchers.extend(sub_matchers)
        errors.extend(sub_errors)
    return matchers, errors
