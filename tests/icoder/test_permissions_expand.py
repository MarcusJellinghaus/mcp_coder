"""Tests for the pure ``@group`` token expander (``permissions.expand``).

All cases use a plain dict as the raw-token-valued ``groups`` map. Errors are
returned as data and are pathless; the loader adds the source path.
"""

from __future__ import annotations

import pytest

from mcp_coder.icoder.permissions import Matcher, expand
from mcp_coder.icoder.permissions.expand import is_ref, ref_name


def test_non_ref_token_delegates_to_parse_matcher() -> None:
    """A plain matcher token parses exactly as ``parse_matcher`` would."""
    matchers, errors = expand("mcp__git__log", {})
    assert errors == []
    assert matchers == [Matcher(server="git", tool="log", arg=None)]


def test_malformed_non_ref_token_returns_parse_error() -> None:
    """A malformed non-ref token returns its ``parse_matcher`` error unchanged."""
    matchers, errors = expand("not_a_matcher", {})
    assert matchers == []
    assert errors == ["malformed matcher token: 'not_a_matcher'"]


def test_ref_expands_to_group_members() -> None:
    """``@git`` yields one matcher per member."""
    groups = {"git": ["mcp__git__status", "mcp__git__log"]}
    matchers, errors = expand("@git", groups)
    assert errors == []
    assert matchers == [
        Matcher(server="git", tool="status", arg=None),
        Matcher(server="git", tool="log", arg=None),
    ]


def test_ref_expands_transitively() -> None:
    """A group referencing another group yields both groups' members."""
    groups = {"write": ["@read", "mcp__git__commit"], "read": ["mcp__git__log"]}
    matchers, errors = expand("@write", groups)
    assert errors == []
    assert matchers == [
        Matcher(server="git", tool="log", arg=None),
        Matcher(server="git", tool="commit", arg=None),
    ]


def test_unknown_ref_is_error() -> None:
    """An unknown top-level ref yields no matchers and one error naming it."""
    matchers, errors = expand("@nope", {"git": ["mcp__git__log"]})
    assert matchers == []
    assert len(errors) == 1
    assert "@nope" in errors[0]


def test_unknown_nested_ref_is_error() -> None:
    """An unknown ref at depth surfaces its error."""
    groups = {"a": ["@b"], "b": ["mcp__git__log", "@missing"]}
    _, errors = expand("@a", groups)
    assert len(errors) == 1
    assert "@missing" in errors[0]


def test_cycle_terminates_with_no_tools_error() -> None:
    """A pure cycle terminates and reports that it resolves to no tools."""
    groups = {"a": ["@b"], "b": ["@a"]}
    matchers, errors = expand("@a", groups)
    assert matchers == []
    assert len(errors) == 1
    assert "resolves to no tools" in errors[0]


def test_diamond_contributes_shared_group_once() -> None:
    """A group reached by two routes contributes its members once."""
    groups = {"a": ["@c", "@b"], "b": ["@c"], "c": ["mcp__fs__read"]}
    matchers, errors = expand("@a", groups)
    assert errors == []
    assert matchers == [Matcher(server="fs", tool="read", arg=None)]


def test_empty_group_referenced_directly_is_error() -> None:
    """A defined-but-empty group referenced at top level resolves to no tools."""
    matchers, errors = expand("@spare", {"spare": []})
    assert matchers == []
    assert len(errors) == 1
    assert "resolves to no tools" in errors[0]


def test_nested_empty_group_does_not_poison_sibling() -> None:
    """A nested empty group is not an error when a sibling member resolved."""
    groups = {"a": ["@spare", "mcp__git__log"], "spare": []}
    matchers, errors = expand("@a", groups)
    assert errors == []
    assert matchers == [Matcher(server="git", tool="log", arg=None)]


def test_ref_tolerates_whitespace() -> None:
    """``" @git"`` resolves exactly like ``"@git"``."""
    groups = {"git": ["mcp__git__status"]}
    assert expand(" @git", groups) == expand("@git", groups)
    assert expand(" @git", groups)[1] == []


def test_value_set_member_expands_to_many_matchers() -> None:
    """A value-set member inside a group expands to N matchers."""
    groups = {"fs": ["mcp__fs__read(path={a,b})"]}
    matchers, errors = expand("@fs", groups)
    assert errors == []
    assert len(matchers) == 2


@pytest.mark.parametrize(
    ("token", "expected_is_ref", "expected_name"),
    [("@git", True, "git"), (" @git", True, "git")],
)
def test_is_ref_and_ref_name(
    token: str, expected_is_ref: bool, expected_name: str
) -> None:
    """``is_ref``/``ref_name`` recognise and strip the ``@`` convention."""
    assert is_ref(token) is expected_is_ref
    assert ref_name(token) == expected_name


def test_is_ref_false_for_matcher_token() -> None:
    """A plain matcher token is not a ref."""
    assert is_ref("mcp__git__log") is False
