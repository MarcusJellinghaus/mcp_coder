"""Tests for the pure ``skill -> PermissionFrame`` builder (Step 2, TDD).

Exercises ``mcp_coder.icoder.permissions.skill_frame`` — the single place that
maps any skill declaration (rich ``tools:`` block *or* legacy ``allowed-tools``
list) to a :class:`PermissionFrame`, deciding blocked-ness in one spot. It is
pure: it takes **data** (``SkillToolsBlock`` / token sequence), not a
``ClaudeSkill``, and performs no I/O.

One test per row of the summary's mapping table / per acceptance criterion.
"""

from __future__ import annotations

from mcp_coder.icoder.permissions.model import (
    Matcher,
    PermissionFrame,
    ScenarioBlock,
)
from mcp_coder.icoder.permissions.skill_frame import (
    as_base,
    build_frame,
    two_empties,
)
from mcp_coder.icoder.permissions.skill_tools import SkillToolsBlock, parse_tools_block

# --- Models A / B / C (valid rich blocks) ---


def test_model_a_inherit_allow() -> None:
    """A (``base: inherit`` + ``allow``) → inherit frame with parsed allow."""
    block = SkillToolsBlock(base="inherit", allow=("mcp__srv__tool",))
    result = build_frame(block, None, enforce_skill_tools=False)
    assert result.frame is not None
    assert result.frame.base == "inherit"
    assert len(result.frame.allow) == 1
    assert result.frame.deny == ()
    assert result.blocked_reason is None


def test_model_b_inherit_deny() -> None:
    """B (``base: inherit`` + ``deny``) → inherit frame with parsed deny."""
    block = SkillToolsBlock(base="inherit", deny=("mcp__srv__danger",))
    result = build_frame(block, None, enforce_skill_tools=False)
    assert result.frame is not None
    assert result.frame.base == "inherit"
    assert len(result.frame.deny) == 1
    assert result.blocked_reason is None


def test_model_c_none_allow() -> None:
    """C (``base: none`` + surviving ``allow``) → none frame, runs."""
    block = SkillToolsBlock(base="none", allow=("mcp__srv__tool",))
    result = build_frame(block, None, enforce_skill_tools=False)
    assert result.frame is not None
    assert result.frame.base == "none"
    assert len(result.frame.allow) == 1
    assert result.blocked_reason is None


# --- Zero-tool sandbox vs D8 blocking ---


def test_none_empty_allow_runs_no_warning() -> None:
    """``base: none, allow: []`` is a valid sandbox — runs, no warning."""
    block = SkillToolsBlock(base="none", allow=())
    result = build_frame(block, None, enforce_skill_tools=False)
    assert result.blocked_reason is None
    assert result.warnings == ()
    assert result.frame is not None
    assert result.frame.base == "none"
    assert result.frame.allow == ()


def test_none_declared_allow_all_dropped_is_blocked() -> None:
    """``base: none`` with a declared allow that all drops → BLOCKED (D8)."""
    block = SkillToolsBlock(base="none", allow=("@x",))
    result = build_frame(block, None, enforce_skill_tools=False)
    assert result.blocked_reason is not None
    assert result.frame is not None
    assert result.frame.base == "none"  # fail-closed frame still returned


# --- bare use: ---


def test_bare_use_block_without_scenarios_is_blocked() -> None:
    """A ``use:`` with no scenario map is BLOCKED as an unknown scenario."""
    block = SkillToolsBlock(base=None, use="team_defaults")
    result = build_frame(block, None, enforce_skill_tools=False)
    assert result.blocked_reason is not None
    assert "team_defaults" in result.blocked_reason
    assert result.frame is not None
    assert result.frame.base == "none"


# --- inherit, everything dropped → no-op frame, runs ---


def test_inherit_everything_dropped_runs_noop_frame() -> None:
    """``base: inherit`` with every allow token dropped → runs, empty frame."""
    block = SkillToolsBlock(base="inherit", allow=("@x",))
    result = build_frame(block, None, enforce_skill_tools=False)
    assert result.blocked_reason is None
    assert result.frame is not None
    assert result.frame.base == "inherit"  # allow-side drop never forces none
    assert result.frame.allow == ()
    assert result.frame.deny == ()


# --- Dropped deny entry forces base=none (fail-closed, D3) ---


def test_dropped_deny_at_ref_forces_base_none() -> None:
    """A dropped ``@ref`` deny entry forces ``base=none`` (skill still runs)."""
    block = SkillToolsBlock(base="inherit", allow=("mcp__s__t",), deny=("@x",))
    result = build_frame(block, None, enforce_skill_tools=False)
    assert result.frame is not None
    assert result.frame.base == "none"
    assert result.blocked_reason is None  # allow survived, so it runs
    assert any("@x" in warning for warning in result.warnings)


def test_dropped_deny_unparseable_mcp_forces_base_none() -> None:
    """A dropped unparseable ``mcp__`` deny entry also forces ``base=none``."""
    block = SkillToolsBlock(base="inherit", allow=("mcp__s__t",), deny=("mcp__oops",))
    result = build_frame(block, None, enforce_skill_tools=False)
    assert result.frame is not None
    assert result.frame.base == "none"
    assert result.blocked_reason is None


# --- Deny-caused block names the deny cause, not the empty allow ---


def test_deny_caused_block_names_deny_cause_not_empty_allow() -> None:
    """A deny-drop that forces none *and* empties allow → deny-caused reason.

    ``{base: inherit, allow: ["Bash(x)"], deny: ["@x"]}`` — the deny drop
    forces ``base=none`` and the declared ``allow`` filters to empty. The
    ``blocked_reason`` must name the dropped deny entry, never the empty allow.
    """
    block = SkillToolsBlock(base="inherit", allow=("Bash(x)",), deny=("@x",))
    result = build_frame(block, None, enforce_skill_tools=False)
    assert result.blocked_reason is not None
    assert "@x" in result.blocked_reason

    empty_allow_reason = two_empties("none", ("Bash(x)",), (), deny_dropped=())
    deny_caused_reason = two_empties("none", ("Bash(x)",), (), deny_dropped=("@x",))
    assert empty_allow_reason is not None
    assert deny_caused_reason is not None
    assert empty_allow_reason != deny_caused_reason  # two distinct strings
    assert result.blocked_reason == deny_caused_reason


# --- @ref without a group map: unknown → dropped + warned ---


def test_at_ref_in_allow_without_groups_dropped_and_warned() -> None:
    """Omitting ``groups`` makes an ``@ref`` unknown → dropped + warned."""
    block = SkillToolsBlock(base="inherit", allow=("mcp__s__t", "@grp"))
    result = build_frame(block, None, enforce_skill_tools=False)
    assert result.frame is not None
    assert len(result.frame.allow) == 1  # only the mcp__ token survives
    assert result.frame.base == "inherit"  # allow-side drop doesn't force none
    assert any("@grp" in w and "unknown" in w for w in result.warnings)
    assert result.blocked_reason is None


# --- @ref lookup against the expanded group map ---

_GIT_LOG = Matcher("git", "log")
_GROUPS = {"git": (_GIT_LOG,)}


def test_known_ref_in_allow_resolves_without_warning() -> None:
    """A known ``@git`` in ``allow`` contributes its members, no warning."""
    block = SkillToolsBlock(base="none", allow=("@git",))
    result = build_frame(block, None, enforce_skill_tools=False, groups=_GROUPS)
    assert result.frame is not None
    assert result.frame.allow == (_GIT_LOG,)
    assert result.warnings == ()
    assert result.blocked_reason is None


def test_known_ref_in_deny_resolves_without_forcing_none() -> None:
    """A known ``@git`` in ``deny`` resolves; ``base`` is not forced."""
    block = SkillToolsBlock(base="inherit", deny=("@git",))
    result = build_frame(block, None, enforce_skill_tools=False, groups=_GROUPS)
    assert result.frame is not None
    assert result.frame.deny == (_GIT_LOG,)
    assert result.frame.base == "inherit"
    assert result.warnings == ()
    assert result.blocked_reason is None


def test_unknown_ref_in_allow_dropped_skill_runs() -> None:
    """An unknown ``@nope`` in ``allow`` drops + warns; the skill still runs."""
    block = SkillToolsBlock(base="none", allow=("@git", "@nope"))
    result = build_frame(block, None, enforce_skill_tools=False, groups=_GROUPS)
    assert result.frame is not None
    assert result.frame.allow == (_GIT_LOG,)
    assert result.frame.base == "none"
    assert any("@nope" in w for w in result.warnings)
    assert result.blocked_reason is None


def test_unknown_ref_in_deny_forces_base_none() -> None:
    """An unknown ``@nope`` in ``deny`` forces ``base=none`` (I2.4's D3)."""
    block = SkillToolsBlock(base="inherit", allow=("@git",), deny=("@nope",))
    result = build_frame(block, None, enforce_skill_tools=False, groups=_GROUPS)
    assert result.frame is not None
    assert result.frame.base == "none"
    assert any("deny narrowed" in w and "@nope" in w for w in result.warnings)
    assert result.blocked_reason is None


def test_unknown_ref_only_allow_under_none_blocked_by_two_empties() -> None:
    """An unknown ``@nope`` as the only ``allow`` under ``none`` → blocked."""
    block = SkillToolsBlock(base="none", allow=("@nope",))
    result = build_frame(block, None, enforce_skill_tools=False, groups=_GROUPS)
    assert result.blocked_reason == two_empties("none", ("@nope",), (), deny_dropped=())


# --- use: <scenario> substitution ---


def test_use_known_scenario_substitutes_whole_block() -> None:
    """``use: review`` → the scenario's whole block, including ``base``."""
    scenario = ScenarioBlock("inherit", (_GIT_LOG,), (Matcher("git", "push"),))
    block = SkillToolsBlock(base=None, use="review")
    result = build_frame(
        block, None, enforce_skill_tools=False, scenarios={"review": scenario}
    )
    assert result.frame == PermissionFrame("inherit", scenario.allow, scenario.deny)
    assert result.warnings == ()
    assert result.blocked_reason is None


def test_use_scenario_base_none_lands() -> None:
    """A scenario's ``base: none`` lands on the frame verbatim."""
    scenario = ScenarioBlock("none", (_GIT_LOG,))
    block = SkillToolsBlock(base=None, use="review")
    result = build_frame(
        block, None, enforce_skill_tools=False, scenarios={"review": scenario}
    )
    assert result.frame is not None
    assert result.frame.base == "none"
    assert result.blocked_reason is None


def test_use_unknown_scenario_is_blocked() -> None:
    """An unknown ``use: nope`` is blocked, naming the scenario."""
    block = SkillToolsBlock(base=None, use="nope")
    result = build_frame(
        block,
        None,
        enforce_skill_tools=False,
        scenarios={"review": ScenarioBlock("none")},
    )
    assert result.blocked_reason is not None
    assert "nope" in result.blocked_reason
    assert "I4.1" not in result.blocked_reason
    assert result.frame is not None
    assert result.frame.base == "none"


def test_use_with_inline_keys_blocked_via_errors() -> None:
    """Regression (D5): ``use:`` + inline keys → blocked via ``errors``."""
    block = parse_tools_block({"tools": {"use": "review", "allow": ["mcp__s__t"]}})
    assert block is not None
    result = build_frame(
        block,
        None,
        enforce_skill_tools=False,
        scenarios={"review": ScenarioBlock("inherit")},
    )
    assert result.blocked_reason is not None
    assert "cannot combine" in result.blocked_reason


def test_use_scenario_allow_failed_to_expand_is_blocked() -> None:
    """A scenario whose ``allow`` failed to expand blocks the skill."""
    error = "scenario 'review': unknown group reference '@nope'"
    scenario = ScenarioBlock("none", (), (), errors=(error,))
    block = SkillToolsBlock(base=None, use="review")
    result = build_frame(
        block, None, enforce_skill_tools=False, scenarios={"review": scenario}
    )
    assert result.frame is not None
    assert result.frame.base == "none"
    assert error in result.warnings
    assert result.blocked_reason is not None
    assert error in result.blocked_reason


def test_use_scenario_deny_failed_to_expand_is_blocked() -> None:
    """A scenario whose ``deny`` failed is blocked; its ``allow`` is not granted."""
    error = "scenario 'review': unknown group reference '@nope'"
    scenario = ScenarioBlock("none", (_GIT_LOG,), (), errors=(error,))
    block = SkillToolsBlock(base=None, use="review")
    result = build_frame(
        block, None, enforce_skill_tools=False, scenarios={"review": scenario}
    )
    assert result.frame is not None
    assert result.frame.allow == ()
    assert result.blocked_reason is not None
    assert error in result.blocked_reason
    assert error in result.warnings


# --- non-mcp token ignored (silent) ---


def test_non_mcp_token_ignored_no_warning() -> None:
    """A non-``mcp__`` token is silently ignored (no warning, no matcher)."""
    block = SkillToolsBlock(base="inherit", allow=("mcp__s__t", "Bash(x)", "gh"))
    result = build_frame(block, None, enforce_skill_tools=False)
    assert result.warnings == ()
    assert result.frame is not None
    assert len(result.frame.allow) == 1


# --- wildcard is enforced (produces a matcher) ---


def test_wildcard_produces_matcher() -> None:
    """An ``mcp__srv__*`` wildcard produces an enforced matcher."""
    block = SkillToolsBlock(base="inherit", allow=("mcp__srv__*",))
    result = build_frame(block, None, enforce_skill_tools=False)
    assert result.frame is not None
    assert len(result.frame.allow) == 1
    assert result.frame.allow[0].tool == "*"


# --- arg-scoped token: side-selected wording ---


def test_arg_scoped_allow_kept_warns_elevates() -> None:
    """An arg-scoped ``allow`` token is kept and warns naming #1053/elevates."""
    block = SkillToolsBlock(base="inherit", allow=("mcp__s__t(a=v)",))
    result = build_frame(block, None, enforce_skill_tools=False)
    assert result.frame is not None
    assert len(result.frame.allow) == 1
    assert any("#1053" in w and "elevat" in w for w in result.warnings)


def test_arg_scoped_deny_warns_denies_never_elevates() -> None:
    """An arg-scoped ``deny`` token warns naming #1053/denies, never elevation."""
    block = SkillToolsBlock(base="inherit", deny=("mcp__s__t(a=v)",))
    result = build_frame(block, None, enforce_skill_tools=False)
    assert result.frame is not None
    assert len(result.frame.deny) == 1
    predicate_warnings = [w for w in result.warnings if "#1053" in w]
    assert predicate_warnings
    assert any("den" in w for w in predicate_warnings)
    assert all("elevat" not in w for w in predicate_warnings)


# --- Legacy allowed-tools path (base forced by the enforce flag) ---


def test_legacy_base_inherit_when_enforce_off() -> None:
    """Legacy ``allowed-tools`` with the flag off → ``base=inherit``."""
    result = build_frame(None, ("mcp__s__t",), enforce_skill_tools=False)
    assert result.frame is not None
    assert result.frame.base == "inherit"
    assert len(result.frame.allow) == 1
    assert result.blocked_reason is None


def test_legacy_base_none_when_enforce_on() -> None:
    """Legacy ``allowed-tools`` with the flag on → ``base=none``."""
    result = build_frame(None, ("mcp__s__t",), enforce_skill_tools=True)
    assert result.frame is not None
    assert result.frame.base == "none"
    assert len(result.frame.allow) == 1
    assert result.blocked_reason is None


# --- Neither block → frame is None ---


def test_neither_block_yields_frame_none() -> None:
    """No declaration at all → ``SkillFrame(frame=None)`` (status quo)."""
    assert build_frame(None, None, enforce_skill_tools=False).frame is None
    assert build_frame(None, (), enforce_skill_tools=True).frame is None


# --- Malformed block → fail-closed frame + blocked ---


def test_malformed_block_fail_closed_and_blocked() -> None:
    """A malformed block → fail-closed ``base=none`` frame + blocked_reason."""
    block = SkillToolsBlock(base=None, errors=("tools: must be a non-empty mapping",))
    result = build_frame(block, None, enforce_skill_tools=False)
    assert result.frame is not None
    assert result.frame.base == "none"
    assert result.blocked_reason is not None
    assert "non-empty mapping" in result.blocked_reason


# --- Both blocks present → rich wins, silently (D14) ---


def test_both_blocks_present_rich_wins_silently() -> None:
    """When both blocks exist the rich block wins and no warning is emitted."""
    block = SkillToolsBlock(base="inherit", allow=("mcp__rich__tool",))
    result = build_frame(block, ("mcp__legacy__other",), enforce_skill_tools=True)
    assert result.frame is not None
    assert result.frame.base == "inherit"  # from the rich block, not enforce flag
    assert len(result.frame.allow) == 1
    assert result.frame.allow[0].server == "rich"  # legacy list ignored
    assert result.warnings == ()  # silent (D14)
    assert result.blocked_reason is None


# --- as_base narrowing helper ---


def test_as_base_narrows_str_or_none_to_base() -> None:
    """``as_base`` narrows any non-member (incl. None) to ``\"none\"``."""
    assert as_base("inherit") == "inherit"
    assert as_base("none") == "none"
    assert as_base(None) == "none"
    assert as_base("garbage") == "none"
