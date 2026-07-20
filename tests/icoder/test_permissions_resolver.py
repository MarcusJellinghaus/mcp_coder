"""Tests for the iCoder permission resolver (Step 3, TDD).

These tests exercise ``mcp_coder.icoder.permissions.resolver.resolve`` on the
``frame=None`` path only (frame semantics land in Step 4). They cover config
rule precedence — specificity (primary) -> ``never>ask>allow`` -> layer order
-> declaration order — plus the default fallback and the fail-closed degrade
path. ``args`` is intentionally passed and intentionally unread in M2.
"""

from __future__ import annotations

from mcp_coder.icoder.permissions import (
    WILDCARD,
    Decision,
    Default,
    Degraded,
    Layer,
    Matcher,
    PermissionConfig,
    Policy,
    Rule,
    resolve,
)


def _rule(
    server: str,
    tool: str,
    policy: Policy,
    layer: str,
    *,
    origin: Rule | None = None,
) -> Rule:
    """Build a Rule from a concrete/wildcard server+tool and a policy."""
    return Rule(
        matcher=Matcher(server=server, tool=tool, origin=origin),
        policy=policy,
        layer=layer,
    )


# --- Equal-specificity policy precedence: never > ask > allow ---


def test_equal_specificity_never_beats_ask_and_allow() -> None:
    """Same-specificity rules resolve to NEVER over AFTER_APPROVAL over ALWAYS."""
    allow = _rule("git", "commit", Policy.ALWAYS, "user")
    ask = _rule("git", "commit", Policy.AFTER_APPROVAL, "user")
    never = _rule("git", "commit", Policy.NEVER, "user")
    config = PermissionConfig(rules=(allow, ask, never))

    decision = resolve("mcp__git__commit", None, None, config)

    assert decision.policy is Policy.NEVER
    assert decision.matched_rule is never


def test_equal_specificity_ask_beats_allow() -> None:
    """With only allow + ask at equal specificity, AFTER_APPROVAL wins."""
    allow = _rule("git", "commit", Policy.ALWAYS, "user")
    ask = _rule("git", "commit", Policy.AFTER_APPROVAL, "user")
    config = PermissionConfig(rules=(allow, ask))

    decision = resolve("mcp__git__commit", None, None, config)

    assert decision.policy is Policy.AFTER_APPROVAL
    assert decision.matched_rule is ask


# --- Specificity primary (beats policy rank) ---


def test_specific_tool_beats_server_wildcard() -> None:
    """A concrete-tool rule outranks a server-wildcard rule on the same server."""
    specific = _rule("git", "commit", Policy.ALWAYS, "user")
    broad = _rule("git", WILDCARD, Policy.NEVER, "user")
    config = PermissionConfig(rules=(broad, specific))

    decision = resolve("mcp__git__commit", None, None, config)

    assert decision.policy is Policy.ALWAYS
    assert decision.matched_rule is specific


def test_specific_always_beats_broad_ask() -> None:
    """A specific ``always`` beats a broad (server-wildcard) ``ask`` — specificity first."""
    specific = _rule("git", "commit", Policy.ALWAYS, "user")
    broad = _rule("git", WILDCARD, Policy.AFTER_APPROVAL, "user")
    config = PermissionConfig(rules=(broad, specific))

    decision = resolve("mcp__git__commit", None, None, config)

    assert decision.policy is Policy.ALWAYS
    assert decision.matched_rule is specific
    assert decision.lifted_never is None


# --- Layering: equal specificity + equal policy -> later layer wins ---


def test_later_layer_wins_at_equal_specificity_and_policy() -> None:
    """user -> project -> local -> runtime: the latest layer wins the tie."""
    user = _rule("git", "commit", Policy.ALWAYS, "user")
    project = _rule("git", "commit", Policy.ALWAYS, "project")
    local = _rule("git", "commit", Policy.ALWAYS, "local")
    runtime = _rule("git", "commit", Policy.ALWAYS, "runtime")
    config = PermissionConfig(rules=(user, project, local, runtime))

    decision = resolve("mcp__git__commit", None, None, config)

    assert decision.matched_rule is runtime
    assert decision.source == Layer("runtime")


# --- Declaration order: full tie -> earlier-declared rule wins ---


def test_declaration_order_breaks_full_tie() -> None:
    """Equal specificity, policy, and layer -> the earlier-declared rule wins."""
    first = _rule("git", "commit", Policy.ALWAYS, "user")
    second = _rule("git", "commit", Policy.ALWAYS, "user")
    config = PermissionConfig(rules=(first, second))

    decision = resolve("mcp__git__commit", None, None, config)

    assert decision.matched_rule is first


# --- Wildcards ---


def test_server_wildcard_matches_all_tools_of_that_server() -> None:
    """``mcp__git__*`` matches any tool of server ``git``."""
    wild = _rule("git", WILDCARD, Policy.NEVER, "user")
    config = PermissionConfig(rules=(wild,))

    decision = resolve("mcp__git__push", None, None, config)

    assert decision.policy is Policy.NEVER
    assert decision.matched_rule is wild


def test_wildcard_of_other_server_falls_through_to_default() -> None:
    """A tool of a different server does not match -> default fallback."""
    wild = _rule("git", WILDCARD, Policy.NEVER, "user")
    config = PermissionConfig(rules=(wild,), default_policy=Policy.ALWAYS)

    decision = resolve("mcp__fs__read", None, None, config)

    assert decision.policy is Policy.ALWAYS
    assert decision.source == Default()
    assert decision.matched_rule is None


# --- Default fallback ---


def test_default_policy_unset_maps_to_always() -> None:
    """No match + ``default_policy=None`` -> ALWAYS (mapping lives in resolver)."""
    config = PermissionConfig(rules=(), default_policy=None)

    decision = resolve("mcp__git__commit", None, None, config)

    assert decision.policy is Policy.ALWAYS
    assert decision.source == Default()
    assert decision.matched_rule is None


def test_explicit_default_policy_never_is_honoured() -> None:
    """No match + explicit ``default_policy=NEVER`` -> NEVER."""
    config = PermissionConfig(rules=(), default_policy=Policy.NEVER)

    decision = resolve("mcp__git__commit", None, None, config)

    assert decision.policy is Policy.NEVER
    assert decision.source == Default()
    assert decision.matched_rule is None


# --- Degrade (non-frame): fail-closed -> ASK ---


def test_degraded_config_forces_ask_even_when_a_rule_matches() -> None:
    """A degraded config forces the whole config path to ASK (fail-closed)."""
    match = _rule("git", "commit", Policy.ALWAYS, "user")
    config = PermissionConfig(
        rules=(match,),
        degraded=True,
        errors=("boom",),
    )

    decision = resolve("mcp__git__commit", None, None, config)

    assert decision.policy is Policy.AFTER_APPROVAL
    assert decision.source == Degraded(errors=("boom",))
    assert decision.matched_rule is None


# --- after-approval is truthful (not pre-collapsed) ---


def test_ask_rule_returns_after_approval_not_collapsed() -> None:
    """An ``ask`` rule resolves to the true AFTER_APPROVAL policy."""
    ask = _rule("git", "commit", Policy.AFTER_APPROVAL, "user")
    config = PermissionConfig(rules=(ask,))

    decision = resolve("mcp__git__commit", None, None, config)

    assert isinstance(decision, Decision)
    assert decision.policy is Policy.AFTER_APPROVAL


# --- origin provenance hook ---


def test_matched_rule_reports_matcher_origin_when_set() -> None:
    """When the matched rule's matcher has an origin Rule, that origin is reported."""
    origin = _rule("git", "commit", Policy.ALWAYS, "user")
    matched = _rule("git", "commit", Policy.ALWAYS, "user", origin=origin)
    config = PermissionConfig(rules=(matched,))

    decision = resolve("mcp__git__commit", None, None, config)

    assert decision.matched_rule is origin


def test_args_are_ignored_on_config_path() -> None:
    """``args`` is accepted but unread in M2: it does not affect the decision."""
    rule = _rule("git", "commit", Policy.NEVER, "user")
    config = PermissionConfig(rules=(rule,))

    with_args = resolve("mcp__git__commit", {"message": "x"}, None, config)
    without_args = resolve("mcp__git__commit", None, None, config)

    assert with_args == without_args
    assert with_args.policy is Policy.NEVER
