"""Tests for the iCoder permission data model (Step 1, TDD).

These tests exercise ``mcp_coder.icoder.permissions.model`` — a pure data
module of frozen dataclasses / enum, no logic beyond ``Policy.rank``.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from mcp_coder.icoder.permissions import (
    WILDCARD,
    ArgPredicate,
    Decision,
    Default,
    Degraded,
    Frame,
    Layer,
    Matcher,
    PermissionConfig,
    PermissionFrame,
    Policy,
    Rule,
    Source,
    Specificity,
)

# --- Construction with defaults ---


def test_wildcard_sentinel() -> None:
    """WILDCARD is the literal ``*`` string sentinel."""
    assert WILDCARD == "*"


def test_arg_predicate_construction() -> None:
    """ArgPredicate stores name/value and defaults is_glob to False."""
    pred = ArgPredicate(name="path", value="/tmp")
    assert pred.name == "path"
    assert pred.value == "/tmp"
    assert pred.is_glob is False
    assert ArgPredicate(name="p", value="v", is_glob=True).is_glob is True


def test_matcher_construction_defaults() -> None:
    """Matcher defaults arg and origin to None."""
    m = Matcher(server="srv", tool="tool")
    assert m.server == "srv"
    assert m.tool == "tool"
    assert m.arg is None
    assert m.origin is None


def test_matcher_wildcard() -> None:
    """Matcher accepts the WILDCARD sentinel on server/tool."""
    m = Matcher(server=WILDCARD, tool=WILDCARD)
    assert m.server == "*"
    assert m.tool == "*"


def test_rule_construction_defaults() -> None:
    """Rule defaults source_path to None."""
    rule = Rule(
        matcher=Matcher(server="s", tool="t"), policy=Policy.ALWAYS, layer="user"
    )
    assert rule.policy is Policy.ALWAYS
    assert rule.layer == "user"
    assert rule.source_path is None


def test_permission_frame_construction_defaults() -> None:
    """PermissionFrame defaults allow/deny to empty tuples."""
    frame = PermissionFrame(base="inherit")
    assert frame.base == "inherit"
    assert frame.allow == ()
    assert frame.deny == ()


def test_permission_config_empty_is_valid() -> None:
    """PermissionConfig() with no args is a valid empty config."""
    cfg = PermissionConfig()
    assert cfg.rules == ()
    assert cfg.default_policy is None
    assert cfg.groups == {}
    assert cfg.scenarios == {}
    assert cfg.degraded is False
    assert cfg.errors == ()


def test_decision_construction_defaults() -> None:
    """Decision(policy, source) is valid with matched_rule/lifted_never None."""
    d = Decision(policy=Policy.NEVER, source=Default())
    assert d.policy is Policy.NEVER
    assert isinstance(d.source, Default)
    assert d.matched_rule is None
    assert d.lifted_never is None


# --- Frozen ---


def test_matcher_frozen() -> None:
    """Mutating a Matcher field raises FrozenInstanceError."""
    m = Matcher(server="s", tool="t")
    with pytest.raises(FrozenInstanceError):
        m.server = "x"  # type: ignore[misc]


def test_rule_frozen() -> None:
    """Mutating a Rule field raises FrozenInstanceError."""
    rule = Rule(
        matcher=Matcher(server="s", tool="t"), policy=Policy.ALWAYS, layer="user"
    )
    with pytest.raises(FrozenInstanceError):
        rule.layer = "project"  # type: ignore[misc]


def test_permission_config_frozen() -> None:
    """Mutating a PermissionConfig field raises FrozenInstanceError."""
    cfg = PermissionConfig()
    with pytest.raises(FrozenInstanceError):
        cfg.degraded = True  # type: ignore[misc]


def test_decision_frozen() -> None:
    """Mutating a Decision field raises FrozenInstanceError."""
    d = Decision(policy=Policy.ALWAYS, source=Default())
    with pytest.raises(FrozenInstanceError):
        d.policy = Policy.NEVER  # type: ignore[misc]


# --- Hashable (value types with only hashable fields) ---


def test_policy_hashable() -> None:
    """Policy enum members are hashable."""
    assert hash(Policy.ALWAYS) == hash(Policy.ALWAYS)


def test_matcher_hashable() -> None:
    """Matcher is hashable when all fields are hashable."""
    m = Matcher(server="s", tool="t", arg=ArgPredicate(name="a", value="b"))
    assert hash(m) == hash(
        Matcher(server="s", tool="t", arg=ArgPredicate(name="a", value="b"))
    )


def test_rule_hashable() -> None:
    """Rule is hashable (with a Path source_path)."""
    rule = Rule(
        matcher=Matcher(server="s", tool="t"),
        policy=Policy.NEVER,
        layer="user",
        source_path=Path("x.json"),
    )
    assert hash(rule) == hash(rule)


def test_decision_hashable() -> None:
    """Decision is hashable."""
    d = Decision(policy=Policy.ALWAYS, source=Layer("user"))
    assert hash(d) == hash(Decision(policy=Policy.ALWAYS, source=Layer("user")))


def test_source_members_hashable() -> None:
    """Each Source union member is hashable."""
    assert hash(Default()) == hash(Default())
    assert hash(Layer("user")) == hash(Layer("user"))
    assert hash(Frame()) == hash(Frame())
    assert hash(Degraded(layer="project", errors=("x",))) == hash(
        Degraded(layer="project", errors=("x",))
    )


def test_permission_config_not_hashable() -> None:
    """PermissionConfig carries dict fields, so it is NOT hashable."""
    with pytest.raises(TypeError):
        hash(PermissionConfig())


# --- Policy.rank ordering ---


def test_policy_rank_ordering() -> None:
    """NEVER outranks AFTER_APPROVAL outranks ALWAYS."""
    assert Policy.NEVER.rank > Policy.AFTER_APPROVAL.rank
    assert Policy.AFTER_APPROVAL.rank > Policy.ALWAYS.rank


def test_policy_rank_values() -> None:
    """Explicit rank values: NEVER=2, AFTER_APPROVAL=1, ALWAYS=0."""
    assert Policy.NEVER.rank == 2
    assert Policy.AFTER_APPROVAL.rank == 1
    assert Policy.ALWAYS.rank == 0


def test_policy_values() -> None:
    """Policy values match the config-string aliases."""
    assert Policy.ALWAYS.value == "always"
    assert Policy.AFTER_APPROVAL.value == "ask"
    assert Policy.NEVER.value == "never"


# --- Specificity ---


def test_specificity_exposes_arg_rank() -> None:
    """Specificity exposes the .arg_rank field name."""
    spec = Specificity(arg_rank=1, concrete_tool=0, concrete_server=0)
    assert spec.arg_rank == 1
    assert spec.concrete_tool == 0
    assert spec.concrete_server == 0


def test_specificity_lexicographic_comparison() -> None:
    """Specificity compares lexicographically (arg_rank dominates)."""
    assert Specificity(1, 0, 0) > Specificity(0, 1, 1)
    assert Specificity(0, 1, 0) > Specificity(0, 0, 1)
    assert Specificity(1, 1, 1) == Specificity(1, 1, 1)


# --- Source union: Decision built with each member ---


def test_decision_with_each_source_member() -> None:
    """A Decision can carry any Source union member."""
    sources: list[Source] = [
        Default(),
        Layer("user"),
        Frame(),
        Degraded(layer="project", errors=("x",)),
    ]
    for src in sources:
        d = Decision(policy=Policy.AFTER_APPROVAL, source=src)
        assert d.source is src


def test_degraded_defaults() -> None:
    """Degraded defaults layer to None and errors to empty tuple."""
    deg = Degraded()
    assert deg.layer is None
    assert deg.errors == ()


def test_layer_carries_name() -> None:
    """Layer carries its name identity."""
    assert Layer("runtime").name == "runtime"


# --- Structural fields exist & are populatable ---


def test_matcher_origin_populatable() -> None:
    """Matcher.origin can be populated with a Rule (provenance hook)."""
    rule = Rule(
        matcher=Matcher(server="s", tool="t"), policy=Policy.ALWAYS, layer="user"
    )
    m = Matcher(server="s", tool="t", origin=rule)
    assert m.origin is rule


def test_rule_source_path_populatable() -> None:
    """Rule.source_path can be populated with a Path."""
    rule = Rule(
        matcher=Matcher(server="s", tool="t"),
        policy=Policy.ALWAYS,
        layer="local",
        source_path=Path("settings.json"),
    )
    assert rule.source_path == Path("settings.json")


def test_permission_config_groups_and_scenarios_populatable() -> None:
    """PermissionConfig stores groups and scenarios mappings."""
    grp = {"g1": (Matcher(server="s", tool="t"),)}
    scn = {"s1": (Matcher(server="a", tool="b"),)}
    cfg = PermissionConfig(groups=grp, scenarios=scn)
    assert cfg.groups == grp
    assert cfg.scenarios == scn


def test_decision_lifted_never_populatable() -> None:
    """Decision.lifted_never can carry a Policy (frame elevation record)."""
    d = Decision(
        policy=Policy.ALWAYS,
        source=Frame(),
        lifted_never=Policy.NEVER,
    )
    assert d.lifted_never is Policy.NEVER


def test_decision_matched_rule_populatable() -> None:
    """Decision.matched_rule can carry the winning Rule."""
    rule = Rule(
        matcher=Matcher(server="s", tool="t"), policy=Policy.NEVER, layer="user"
    )
    d = Decision(policy=Policy.NEVER, source=Layer("user"), matched_rule=rule)
    assert d.matched_rule is rule
