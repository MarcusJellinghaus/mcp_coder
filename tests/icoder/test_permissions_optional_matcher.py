"""Tests for the D15 ``Rule.matcher: Matcher | None`` widening (I4.1 step 1).

A matcher-less rule is a synthesised ``@group`` origin rule: provenance-only,
never a member of ``config.rules`` (D13). The resolver and gateway guards make
a regression degrade closed instead of crashing a live session.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

from mcp_coder.icoder.permissions import (
    ArgPredicate,
    Default,
    Layer,
    Matcher,
    PermissionConfig,
    Policy,
    Rule,
    resolve,
)
from mcp_coder.icoder.permissions.gateway import LangchainEnforcementGateway


def _tool(canonical: str) -> SimpleNamespace:
    """Build a fake tool object carrying its canonical name."""
    return SimpleNamespace(canonical=canonical)


def _canonical_of(tool: Any) -> str | None:
    """Resolve a fake tool's canonical name."""
    return tool.canonical  # type: ignore[no-any-return]


def test_resolve_skips_matcherless_rule() -> None:
    """A matcher-less rule is skipped; the ordinary matching rule wins."""
    config = PermissionConfig(
        rules=(
            Rule(None, Policy.NEVER, "user", ref="@git"),
            Rule(Matcher("git", "push"), Policy.AFTER_APPROVAL, "project"),
        )
    )

    decision = resolve("mcp__git__push", None, None, config)

    assert decision.policy is Policy.AFTER_APPROVAL
    assert decision.source == Layer("project")


def test_resolve_only_matcherless_rule_falls_to_default() -> None:
    """With only a matcher-less rule, resolution falls through to the default."""
    config = PermissionConfig(
        rules=(Rule(None, Policy.ALWAYS, "user", ref="@git"),),
        default_policy=Policy.NEVER,
    )

    decision = resolve("mcp__git__push", None, None, config)

    assert decision.policy is Policy.NEVER
    assert isinstance(decision.source, Default)


def test_filter_tools_hides_never_with_matcherless_matched_rule() -> None:
    """An arg-scoped member reached via a ``@group`` is hidden (§10 fail-closed).

    An ordinary arg-scoped ``never`` still stays visible.
    """
    arg = ArgPredicate(name="command", value="push")
    origin = Rule(None, Policy.NEVER, "project", ref="@git-write")
    config = PermissionConfig(
        rules=(
            Rule(Matcher("git", "push", arg=arg, origin=origin), Policy.NEVER, "user"),
            Rule(Matcher("git", "fetch", arg=arg), Policy.NEVER, "user"),
        )
    )
    gateway = LangchainEnforcementGateway(config)
    grouped = _tool("mcp__git__push")
    ordinary = _tool("mcp__git__fetch")

    decision = resolve("mcp__git__push", {}, None, config)
    assert decision.matched_rule is origin

    kept = gateway.filter_tools([grouped, ordinary], _canonical_of)

    assert grouped not in kept
    assert ordinary in kept
