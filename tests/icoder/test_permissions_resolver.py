"""Tests for the iCoder permission resolver (Steps 3 & 4, TDD).

Step 3 exercises ``mcp_coder.icoder.permissions.resolver.resolve`` on the
``frame=None`` config path: config rule precedence — specificity (primary) ->
``never>ask>allow`` -> layer order -> declaration order — plus the default
fallback and the fail-closed degrade path. Step 4 adds the frame-first branch
(models A/B/C, intra-frame deny>allow, elevation-over-never with
``lifted_never``, and the frame x degrade / degrade x sandbox interactions).
``args`` is intentionally passed and intentionally unread in M2.
"""

from __future__ import annotations

from mcp_coder.icoder.permissions import (
    WILDCARD,
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


def _matcher(server: str, tool: str) -> Matcher:
    """Build a bare server/tool Matcher for a frame allow/deny list."""
    return Matcher(server=server, tool=tool)


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


# ======================================================================
# Step 4 — frame semantics
# ======================================================================


# --- Model A: base="inherit", allow, no deny ---


def test_model_a_declared_allow_elevates_to_always() -> None:
    """base='inherit' + allow-declared tool -> ALWAYS from the frame."""
    frame = PermissionFrame(base="inherit", allow=(_matcher("git", "commit"),))
    config = PermissionConfig(rules=(), default_policy=Policy.ALWAYS)

    decision = resolve("mcp__git__commit", None, frame, config)

    assert decision.policy is Policy.ALWAYS
    assert decision.source == Frame()
    assert decision.matched_rule is None
    assert decision.lifted_never is None


def test_model_a_undeclared_inherits_authored_never_from_config() -> None:
    """base='inherit' does not touch undeclared tools; an authored never applies."""
    frame = PermissionFrame(base="inherit", allow=(_matcher("git", "commit"),))
    authored = _rule("git", "push", Policy.NEVER, "user")
    config = PermissionConfig(rules=(authored,))

    decision = resolve("mcp__git__push", None, frame, config)

    assert decision.policy is Policy.NEVER
    assert decision.source == Layer("user")
    assert decision.matched_rule is authored


# --- Model B: base="inherit", deny ---


def test_model_b_denied_tool_is_never_within_frame() -> None:
    """base='inherit' + deny-declared tool -> NEVER from the frame."""
    frame = PermissionFrame(base="inherit", deny=(_matcher("git", "push"),))
    config = PermissionConfig(rules=(), default_policy=Policy.ALWAYS)

    decision = resolve("mcp__git__push", None, frame, config)

    assert decision.policy is Policy.NEVER
    assert decision.source == Frame()
    assert decision.matched_rule is None


def test_model_b_non_denied_tool_resolves_via_config() -> None:
    """A tool the frame does not deny falls through to the config path."""
    frame = PermissionFrame(base="inherit", deny=(_matcher("git", "push"),))
    allow = _rule("git", "commit", Policy.AFTER_APPROVAL, "project")
    config = PermissionConfig(rules=(allow,))

    decision = resolve("mcp__git__commit", None, frame, config)

    assert decision.policy is Policy.AFTER_APPROVAL
    assert decision.source == Layer("project")
    assert decision.matched_rule is allow


# --- Model C: base="none" (sandbox) ---


def test_model_c_declared_tool_elevates_to_always() -> None:
    """base='none' + declared tool -> ALWAYS from the frame."""
    frame = PermissionFrame(base="none", allow=(_matcher("git", "commit"),))
    config = PermissionConfig(rules=(), default_policy=Policy.ALWAYS)

    decision = resolve("mcp__git__commit", None, frame, config)

    assert decision.policy is Policy.ALWAYS
    assert decision.source == Frame()
    assert decision.matched_rule is None


def test_model_c_undeclared_tool_is_never() -> None:
    """base='none' + undeclared tool -> NEVER (the sandbox denies by default)."""
    frame = PermissionFrame(base="none", allow=(_matcher("git", "commit"),))
    # Even a config rule that would allow the tool is sandboxed away.
    config = PermissionConfig(
        rules=(_rule("git", "push", Policy.ALWAYS, "user"),),
        default_policy=Policy.ALWAYS,
    )

    decision = resolve("mcp__git__push", None, frame, config)

    assert decision.policy is Policy.NEVER
    assert decision.source == Frame()
    assert decision.matched_rule is None


def test_frame_none_is_config_only_regression() -> None:
    """frame=None resolves via the config path exactly as in Step 3."""
    rule = _rule("git", "commit", Policy.AFTER_APPROVAL, "user")
    config = PermissionConfig(rules=(rule,))

    decision = resolve("mcp__git__commit", None, None, config)

    assert decision.policy is Policy.AFTER_APPROVAL
    assert decision.source == Layer("user")
    assert decision.matched_rule is rule


# --- Elevation over an authored never (lifted_never) ---


def test_frame_allow_elevates_over_config_never_records_lifted_never() -> None:
    """An allow-declared tool whose config base is never -> ALWAYS, lifted_never=NEVER."""
    frame = PermissionFrame(base="inherit", allow=(_matcher("git", "push"),))
    authored = _rule("git", "push", Policy.NEVER, "user")
    config = PermissionConfig(rules=(authored,))

    decision = resolve("mcp__git__push", None, frame, config)

    assert decision.policy is Policy.ALWAYS
    assert decision.source == Frame()
    assert decision.matched_rule is None
    assert decision.lifted_never is Policy.NEVER


def test_frame_allow_over_non_never_base_leaves_lifted_never_none() -> None:
    """An allow-declared tool whose config base is not never -> lifted_never stays None."""
    frame = PermissionFrame(base="inherit", allow=(_matcher("git", "commit"),))
    authored = _rule("git", "commit", Policy.AFTER_APPROVAL, "user")
    config = PermissionConfig(rules=(authored,))

    decision = resolve("mcp__git__commit", None, frame, config)

    assert decision.policy is Policy.ALWAYS
    assert decision.lifted_never is None


# --- Intra-frame precedence: deny beats allow (DC5) ---


def test_intra_frame_deny_beats_allow() -> None:
    """A tool present in both allow and deny -> NEVER (deny wins)."""
    tool = _matcher("git", "push")
    frame = PermissionFrame(base="inherit", allow=(tool,), deny=(tool,))
    config = PermissionConfig(rules=(), default_policy=Policy.ALWAYS)

    decision = resolve("mcp__git__push", None, frame, config)

    assert decision.policy is Policy.NEVER
    assert decision.source == Frame()
    assert decision.matched_rule is None


# --- matched_rule is None on every frame-sourced decision (C2 biconditional) ---


def test_frame_sourced_decisions_have_no_matched_rule() -> None:
    """Every frame-governed decision carries source=Frame() and matched_rule=None."""
    tool = _matcher("git", "commit")
    denied = _matcher("git", "push")

    # Model A/C declared allow, model B deny, and allow elevation over a never.
    model_a = resolve(
        "mcp__git__commit",
        None,
        PermissionFrame(base="inherit", allow=(tool,)),
        PermissionConfig(rules=()),
    )
    model_b = resolve(
        "mcp__git__push",
        None,
        PermissionFrame(base="inherit", deny=(denied,)),
        PermissionConfig(rules=()),
    )
    model_c = resolve(
        "mcp__git__commit",
        None,
        PermissionFrame(base="none", allow=(tool,)),
        PermissionConfig(rules=()),
    )
    elevation = resolve(
        "mcp__git__push",
        None,
        PermissionFrame(base="inherit", allow=(denied,)),
        PermissionConfig(rules=(_rule("git", "push", Policy.NEVER, "user"),)),
    )

    for decision in (model_a, model_b, model_c, elevation):
        assert decision.source == Frame()
        assert decision.matched_rule is None


# --- Degrade x frame (F4): frame elevation beats degrade ---


def test_degrade_does_not_override_frame_declared_tool() -> None:
    """A degraded config still lets a frame-declared tool resolve to ALWAYS (F4)."""
    frame = PermissionFrame(base="inherit", allow=(_matcher("git", "commit"),))
    config = PermissionConfig(rules=(), degraded=True, errors=("boom",))

    decision = resolve("mcp__git__commit", None, frame, config)

    assert decision.policy is Policy.ALWAYS
    assert decision.source == Frame()
    assert decision.matched_rule is None


def test_degrade_forces_ask_for_non_frame_tool() -> None:
    """A non-declared tool under a degraded config falls through to ASK."""
    frame = PermissionFrame(base="inherit", allow=(_matcher("git", "commit"),))
    config = PermissionConfig(rules=(), degraded=True, errors=("boom",))

    decision = resolve("mcp__git__push", None, frame, config)

    assert decision.policy is Policy.AFTER_APPROVAL
    assert decision.source == Degraded(errors=("boom",))
    assert decision.matched_rule is None


def test_degrade_forces_ask_when_frame_is_none() -> None:
    """frame=None under a degraded config -> ASK (config-path degrade)."""
    config = PermissionConfig(rules=(), degraded=True, errors=("boom",))

    decision = resolve("mcp__git__push", None, None, config)

    assert decision.policy is Policy.AFTER_APPROVAL
    assert decision.source == Degraded(errors=("boom",))


# --- Degrade masks base for lifted_never (Q3) ---


def test_degrade_masks_never_base_so_lifted_never_stays_none() -> None:
    """A degraded config masks a would-be never base: ALWAYS, lifted_never=None."""
    frame = PermissionFrame(base="inherit", allow=(_matcher("git", "push"),))
    authored = _rule("git", "push", Policy.NEVER, "user")
    config = PermissionConfig(rules=(authored,), degraded=True, errors=("boom",))

    decision = resolve("mcp__git__push", None, frame, config)

    assert decision.policy is Policy.ALWAYS
    assert decision.source == Frame()
    assert decision.lifted_never is None


# --- Degrade x sandbox (decision #8): degrade loosens base="none" ---


def test_sandbox_undeclared_degraded_loosens_to_ask() -> None:
    """base='none' + undeclared tool + degraded -> ASK (degrade loosens the sandbox)."""
    frame = PermissionFrame(base="none", allow=(_matcher("git", "commit"),))
    config = PermissionConfig(rules=(), degraded=True, errors=("boom",))

    decision = resolve("mcp__git__push", None, frame, config)

    assert decision.policy is Policy.AFTER_APPROVAL
    assert decision.source == Degraded(errors=("boom",))
    assert decision.matched_rule is None


def test_sandbox_undeclared_healthy_is_never() -> None:
    """base='none' + undeclared tool + healthy config -> NEVER (regression pair)."""
    frame = PermissionFrame(base="none", allow=(_matcher("git", "commit"),))
    config = PermissionConfig(rules=())

    decision = resolve("mcp__git__push", None, frame, config)

    assert decision.policy is Policy.NEVER
    assert decision.source == Frame()
