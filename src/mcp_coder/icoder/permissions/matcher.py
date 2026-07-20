"""Matcher engine for the iCoder permission system (pure string logic).

Parse + rank + match over server/tool matchers. This module imports only from
:mod:`.model` and performs no I/O: parse failures are returned **as data**
(``tuple[list[Matcher], list[str]]``) — the caller (I2.2/I2.4) emits any warning.

Grammar (server/tool granularity)::

    mcp__<server>__<tool>            # <server>/<tool> may be the WILDCARD "*"
    mcp__<server>__<tool>(<name>=<value>)   # optional single arg predicate

A ``<value>`` of ``{a,b,...}`` is a value-set that expands into one exact
matcher per member. A trailing ``*`` in a plain value marks a glob predicate.
The arg predicate is parsed but **not** evaluated in M2.
"""

from __future__ import annotations

from mcp_coder.icoder.permissions.model import (
    WILDCARD,
    ArgPredicate,
    Matcher,
    Specificity,
)

_PREFIX = "mcp__"
_INVALID_TOKEN_CHARS = frozenset("(){},")


def parse_matcher(text: str) -> tuple[list[Matcher], list[str]]:
    """Parse a matcher string into 1+ Matchers, or return errors.

    Value-sets expand into N exact matchers. Returns ``(matchers, errors)``;
    on any error, ``matchers`` is ``[]`` (fail-closed) — the caller emits the
    warning.

    Args:
        text: The matcher string to parse.

    Returns:
        A ``(matchers, errors)`` tuple. Success yields ``(>=1 matchers, [])``;
        failure yields ``([], [reason, ...])``.
    """
    text = text.strip()

    token = text
    arg_clause: str | None = None
    if "(" in text:
        if text.count("(") > 1 or text.count(")") != 1 or not text.endswith(")"):
            return [], [f"malformed matcher (unbalanced parentheses): {text!r}"]
        open_idx = text.index("(")
        token = text[:open_idx].strip()
        arg_clause = text[open_idx + 1 : -1].strip()

    parsed = _parse_token(token)
    if parsed is None:
        return [], [f"malformed matcher token: {token!r}"]
    server, tool = parsed

    if arg_clause is None:
        return [Matcher(server=server, tool=tool, arg=None)], []

    predicates, errors = _parse_arg_clause(arg_clause)
    if errors:
        return [], errors
    if tool == WILDCARD:
        return [], [f"arg predicate not allowed on wildcard tool: {text!r}"]
    return [Matcher(server=server, tool=tool, arg=pred) for pred in predicates], []


def specificity(m: Matcher) -> Specificity:
    """Return the ``(arg_rank, concrete_tool, concrete_server)`` specificity.

    Args:
        m: The matcher to rank.

    Returns:
        A :class:`Specificity` with each field 0 or 1; it compares
        lexicographically (``arg_rank`` dominates).
    """
    return Specificity(
        arg_rank=1 if m.arg is not None else 0,
        concrete_tool=0 if m.tool == WILDCARD else 1,
        concrete_server=0 if m.server == WILDCARD else 1,
    )


def matches(m: Matcher, canonical_tool: str) -> bool:
    """Return True if ``m`` matches a canonical ``mcp__server__tool`` name.

    Wildcards on server/tool are honoured. The arg predicate is NOT evaluated
    in M2.

    Args:
        m: The matcher to test.
        canonical_tool: A canonical ``mcp__server__tool`` name.

    Returns:
        True if the matcher's server and tool accept the canonical name.
    """
    parsed = _parse_token(canonical_tool)
    if parsed is None:
        return False
    server, tool = parsed
    return m.server in (WILDCARD, server) and m.tool in (WILDCARD, tool)


def _parse_token(token: str) -> tuple[str, str] | None:
    """Parse ``mcp__server__tool`` into ``(server, tool)``.

    Args:
        token: The bare matcher token (no arg clause).

    Returns:
        A ``(server, tool)`` tuple, or None if the shape is wrong.
    """
    if _INVALID_TOKEN_CHARS.intersection(token):
        return None
    if not token.startswith(_PREFIX):
        return None
    parts = token[len(_PREFIX) :].split("__")
    if len(parts) != 2:
        return None
    server, tool = parts
    if not server or not tool:
        return None
    return server, tool


def _parse_arg_clause(clause: str) -> tuple[list[ArgPredicate], list[str]]:
    """Parse a single ``name=value`` arg clause into 1+ predicates.

    A ``{a,b,...}`` value expands into one exact predicate per member; a plain
    value with a trailing ``*`` is a glob.

    Args:
        clause: The content between the parentheses.

    Returns:
        A ``(predicates, errors)`` tuple; on error ``predicates`` is ``[]``.
    """
    if clause.count("=") != 1:
        return [], [f"expected exactly one arg predicate: {clause!r}"]
    name, value = clause.split("=", 1)
    name = name.strip()
    value = value.strip()
    if not name or not value:
        return [], [f"malformed arg predicate: {clause!r}"]

    if value.startswith("{") and value.endswith("}"):
        members = [member.strip() for member in value[1:-1].split(",")]
        members = [member for member in members if member]
        if not members:
            return [], [f"empty value-set: {clause!r}"]
        return [ArgPredicate(name=name, value=member) for member in members], []

    return [ArgPredicate(name=name, value=value, is_glob=value.endswith("*"))], []
