"""Tests for the iCoder permission matcher engine (Step 2, TDD).

These tests exercise ``mcp_coder.icoder.permissions.matcher`` — pure string
logic: ``parse_matcher`` (public), plus the module-internal ``specificity`` and
``matches``. Errors are returned as data (never logged); the arg predicate is
parsed but NOT evaluated in M2.
"""

from __future__ import annotations

import pytest

from mcp_coder.icoder.permissions import WILDCARD, ArgPredicate, Matcher, parse_matcher
from mcp_coder.icoder.permissions.matcher import matches, specificity

# --- parse_matcher: concrete / wildcard shapes ---


def test_parse_concrete_tool() -> None:
    """A concrete ``mcp__git__commit`` -> one Matcher, no errors."""
    matchers, errors = parse_matcher("mcp__git__commit")
    assert errors == []
    assert matchers == [Matcher(server="git", tool="commit", arg=None)]


def test_parse_tool_wildcard() -> None:
    """``mcp__git__*`` -> a tool-wildcard Matcher."""
    matchers, errors = parse_matcher("mcp__git__*")
    assert errors == []
    assert matchers == [Matcher(server="git", tool=WILDCARD, arg=None)]


def test_parse_both_wildcard() -> None:
    """``mcp__*__*`` -> a server+tool wildcard Matcher."""
    matchers, errors = parse_matcher("mcp__*__*")
    assert errors == []
    assert matchers == [Matcher(server=WILDCARD, tool=WILDCARD, arg=None)]


def test_parse_strips_whitespace() -> None:
    """Surrounding whitespace is stripped before parsing."""
    matchers, errors = parse_matcher("  mcp__git__commit  ")
    assert errors == []
    assert matchers == [Matcher(server="git", tool="commit", arg=None)]


# --- parse_matcher: arg predicates ---


def test_parse_single_arg_predicate() -> None:
    """A single ``name=value`` predicate -> one Matcher with an exact ArgPredicate."""
    matchers, errors = parse_matcher("mcp__git__commit(msg=hello)")
    assert errors == []
    assert matchers == [
        Matcher(
            server="git",
            tool="commit",
            arg=ArgPredicate(name="msg", value="hello", is_glob=False),
        )
    ]


def test_parse_value_set_expands_to_two_matchers() -> None:
    """``msg={a,b}`` value-set expands into two exact-predicate Matchers."""
    matchers, errors = parse_matcher("mcp__git__commit(msg={a,b})")
    assert errors == []
    assert matchers == [
        Matcher(
            server="git",
            tool="commit",
            arg=ArgPredicate(name="msg", value="a", is_glob=False),
        ),
        Matcher(
            server="git",
            tool="commit",
            arg=ArgPredicate(name="msg", value="b", is_glob=False),
        ),
    ]
    assert all(specificity(m).arg_rank == 1 for m in matchers)


def test_parse_glob_arg_predicate() -> None:
    """A trailing ``*`` in the value marks the ArgPredicate as a glob."""
    matchers, errors = parse_matcher("mcp__git__push(remote=orig*)")
    assert errors == []
    assert len(matchers) == 1
    assert matchers[0].arg is not None
    assert matchers[0].arg.is_glob is True
    assert matchers[0].arg.value == "orig*"


# --- parse_matcher: error rows (fail-closed) ---


@pytest.mark.parametrize(
    "text",
    [
        "mcp__git__commit(a=1,b=2)",  # two predicates (D-O)
        "mcp__git__*(x=1)",  # arg on wildcard tool (decision #5)
        "not_a_tool",  # malformed token
    ],
)
def test_parse_error_rows_fail_closed(text: str) -> None:
    """Each error case returns no matchers and a non-empty error list."""
    matchers, errors = parse_matcher(text)
    assert matchers == []
    assert errors  # non-empty


# --- specificity ranking ---


@pytest.mark.parametrize(
    "text, expected",
    [
        ("mcp__git__commit(msg=x)", (1, 1, 1)),  # arg-scoped
        ("mcp__git__commit", (0, 1, 1)),  # exact tool
        ("mcp__*__commit", (0, 1, 0)),  # server wildcard, concrete tool
        ("mcp__git__*", (0, 0, 1)),  # tool wildcard
        ("mcp__*__*", (0, 0, 0)),  # global
    ],
)
def test_specificity_values(text: str, expected: tuple[int, int, int]) -> None:
    """specificity() reports (arg_rank, concrete_tool, concrete_server)."""
    matchers, errors = parse_matcher(text)
    assert errors == []
    assert tuple(specificity(matchers[0])) == expected


def test_specificity_lexicographic_ordering() -> None:
    """arg-scoped > exact-tool > server-wildcard > global (lexicographic)."""
    arg_scoped = specificity(parse_matcher("mcp__git__commit(msg=x)")[0][0])
    exact_tool = specificity(parse_matcher("mcp__git__commit")[0][0])
    server_wild = specificity(parse_matcher("mcp__git__*")[0][0])
    global_wild = specificity(parse_matcher("mcp__*__*")[0][0])
    assert arg_scoped > exact_tool > server_wild > global_wild


def test_specificity_primary_key_same_server() -> None:
    """An exact-tool matcher outranks a server-wildcard matcher on the same server.

    §8.3 manager, S1: ``mcp__git__commit`` (0,1,1) outranks ``mcp__git__*`` (0,0,1)
    on the same server A.
    """
    exact = specificity(parse_matcher("mcp__git__commit")[0][0])
    server_wild = specificity(parse_matcher("mcp__git__*")[0][0])
    assert exact == (0, 1, 1)
    assert server_wild == (0, 0, 1)
    assert exact > server_wild


# --- matches ---


@pytest.mark.parametrize(
    "text, canonical, expected",
    [
        ("mcp__git__*", "mcp__git__commit", True),
        ("mcp__git__*", "mcp__fs__read", False),
        ("mcp__*__*", "mcp__git__commit", True),
        ("mcp__*__*", "mcp__anything__at_all", True),
        ("mcp__git__commit", "mcp__git__commit", True),
        ("mcp__git__commit", "mcp__git__push", False),
        ("mcp__git__commit", "mcp__fs__commit", False),
    ],
)
def test_matches(text: str, canonical: str, expected: bool) -> None:
    """matches() honours server/tool wildcards against a canonical name."""
    matchers, errors = parse_matcher(text)
    assert errors == []
    assert matches(matchers[0], canonical) is expected


def test_matches_ignores_arg_predicate() -> None:
    """C1: a Matcher carrying an ArgPredicate still matches the bare tool name.

    ``matches()`` never evaluates the arg predicate in M2.
    """
    from_pred, _ = parse_matcher("mcp__git__commit(msg=x)")
    assert matches(from_pred[0], "mcp__git__commit") is True

    from_set, _ = parse_matcher("mcp__git__commit(msg={a,b})")
    assert all(matches(m, "mcp__git__commit") for m in from_set)
