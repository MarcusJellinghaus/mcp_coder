"""Pure ``skill -> PermissionFrame`` builder (the semantic bridge for M2).

The *one* place that maps any skill declaration to a :class:`PermissionFrame`,
implementing the whole mapping table in ``pr_info/steps/summary.md``. It is
**pure** — no I/O, no logging, no clock — and it takes **data**
(a :class:`SkillToolsBlock` and/or a token sequence), not a ``ClaudeSkill``, so
a raw-frontmatter scan (I5.1) can call it too.

Blocked-ness is decided **here** and carried on :attr:`SkillFrame.blocked_reason`
(the deliberate deviation from D12 recorded in the summary): the two
"declared-but-nothing-survived" cases are only knowable after
:func:`parse_matcher` runs, which this module — not the string-only parser —
owns. This module imports only the permission leaf (``matcher``, ``model``,
``skill_tools``): no other ``icoder.*``, no langchain, no UI.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from mcp_coder.icoder.permissions.matcher import parse_matcher
from mcp_coder.icoder.permissions.model import Base, Matcher, PermissionFrame
from mcp_coder.icoder.permissions.skill_tools import SkillToolsBlock


@dataclass(frozen=True)
class SkillFrame:
    """A built permission frame plus its per-invocation feedback.

    Attributes:
        frame: The constructed frame, or ``None`` **only** when there is no
            declaration at all (inherit-everything status quo). A fail-closed
            ``base="none"`` frame is still returned for a blocked skill (for
            I5.1's effective-policy report).
        warnings: Per-invocation notes (surfaced as ``permission_warning`` in
            Step 3). Data only — never logged here.
        blocked_reason: Non-``None`` when the skill refuses to run (Step 4);
            ``None`` when the skill runs.
    """

    frame: PermissionFrame | None
    warnings: tuple[str, ...] = ()
    blocked_reason: str | None = None


def as_base(value: str | None) -> Base:
    """Narrow a raw ``str | None`` to the :data:`Base` literal.

    Any value that is not exactly ``"inherit"`` collapses to ``"none"`` — the
    fail-closed default — so callers at the string/typed boundary stay
    mypy-strict without importing :data:`Base` into the string-only parser.

    Args:
        value: The raw base string (``"inherit"``/``"none"``) or ``None``.

    Returns:
        ``"inherit"`` iff ``value == "inherit"``, otherwise ``"none"``.
    """
    return "inherit" if value == "inherit" else "none"


def two_empties(
    base: Base,
    declared: Sequence[str],
    parsed: Sequence[Matcher],
    *,
    deny_dropped: tuple[str, ...],
) -> str | None:
    """Return a block reason iff a declared ``allow`` filtered to nothing (D8).

    The predicate reads the **post-D3 forced** ``base``, so a dropped ``deny``
    entry that narrowed ``base`` to ``"none"`` can block a skill whose ``allow``
    also emptied. The reason must name the real cause, so two distinct strings
    are returned: a plain empty-``allow`` reason, and — when ``deny_dropped`` is
    non-empty — a deny-caused reason naming the offending entry.

    Args:
        base: The forced base after D3 (a dropped deny forces ``"none"``).
        declared: The raw ``allow`` tokens as declared by the skill.
        parsed: The matchers that survived parsing the ``allow`` tokens.
        deny_dropped: The ``deny`` tokens that were dropped (empty when the
            block, if any, is a plain empty-``allow`` case).

    Returns:
        A cause-specific block reason, or ``None`` when the skill may run.
    """
    if not (base == "none" and declared and not parsed):
        return None
    if deny_dropped:
        return (
            "base forced to none because a deny entry could not be resolved "
            f"({', '.join(deny_dropped)}), and no allow token survived"
        )
    return "base: none but no declared allow token survived parsing"


def _classify(token: str, *, side: str) -> tuple[list[Matcher], str | None, str | None]:
    """Classify one declared token into matchers, a warning, and a drop marker.

    The ``dropped`` element is the **token itself** when it was discarded (so
    the caller can name it in a warning/reason), else ``None``. ``side`` selects
    the arg-predicate wording — the same fact (an unenforced arg predicate) has
    opposite consequences per side: ``allow`` elevates the whole tool (the
    accepted #1053 over-grant), ``deny`` denies the whole tool (over-deny, safe).

    Args:
        token: A single raw declared tool token.
        side: ``"allow"`` or ``"deny"`` — selects the arg-predicate wording.

    Returns:
        A ``(matchers, warning, dropped)`` tuple.
    """
    if token.startswith("@"):
        return [], f"@ref {token!r} not supported until I4.1 (ignored)", token
    if not token.startswith("mcp__"):
        return [], None, None  # non-mcp token → silently ignored
    matchers, errors = parse_matcher(token)
    if errors:
        return [], f"unparseable tool token {token!r} ignored: {errors[0]}", token
    if any(m.arg is not None for m in matchers):
        warning = (
            f"allow: arg predicate not enforced until #1053 — "
            f"elevates the whole tool ({token!r})"
            if side == "allow"
            else f"deny: arg predicate not enforced until #1053 — "
            f"denies the whole tool ({token!r})"
        )
        return matchers, warning, None
    return matchers, None, None


def _classify_all(
    tokens: Sequence[str], *, side: str
) -> tuple[list[Matcher], list[str], tuple[str, ...]]:
    """Classify every token, accumulating matchers, warnings, and drops.

    A non-empty ``dropped`` tuple drives D3's ``base`` forcing in the caller.

    Args:
        tokens: The raw declared tokens for one side.
        side: ``"allow"`` or ``"deny"`` — passed through to :func:`_classify`.

    Returns:
        A ``(matchers, warnings, dropped)`` tuple accumulated over ``tokens``.
    """
    matchers: list[Matcher] = []
    warnings: list[str] = []
    dropped: list[str] = []
    for token in tokens:
        token_matchers, warning, drop = _classify(token, side=side)
        matchers.extend(token_matchers)
        if warning is not None:
            warnings.append(warning)
        if drop is not None:
            dropped.append(drop)
    return matchers, warnings, tuple(dropped)


def build_frame(
    tools_block: SkillToolsBlock | None,
    allowed_tools: Sequence[str] | None,
    *,
    enforce_skill_tools: bool,
) -> SkillFrame:
    """Map any skill declaration to a :class:`SkillFrame` (the mapping table).

    The rich ``tools:`` block wins over the legacy ``allowed_tools`` list and
    the switch is silent (D14). Blocked-ness (malformed block, bare ``use:``,
    and either "declared-but-nothing-survived" case) is decided here and carried
    on :attr:`SkillFrame.blocked_reason`; a blocked skill still gets a
    fail-closed ``base="none"`` frame for the effective-policy report.

    Args:
        tools_block: The parsed rich ``tools:`` block, or ``None`` when absent.
        allowed_tools: The legacy ``allowed-tools`` tokens, or ``None``/empty.
        enforce_skill_tools: On the legacy path only, selects ``base="none"``
            (when True) vs ``base="inherit"`` (when False).

    Returns:
        A :class:`SkillFrame`; ``frame`` is ``None`` only for no declaration.
    """
    if tools_block is None:
        if not allowed_tools:
            return SkillFrame(frame=None)  # neither block → status quo
        allow, warns, _ = _classify_all(allowed_tools, side="allow")
        base: Base = "none" if enforce_skill_tools else "inherit"
        return SkillFrame(
            PermissionFrame(base, tuple(allow)),
            tuple(warns),
            blocked_reason=two_empties(base, allowed_tools, allow, deny_dropped=()),
        )

    if tools_block.errors:  # malformed → fail-closed frame, blocked
        return SkillFrame(
            PermissionFrame("none"),
            tuple(tools_block.errors),
            blocked_reason="; ".join(tools_block.errors),
        )
    if tools_block.use is not None:  # bare use: → blocked (D7b)
        return SkillFrame(
            PermissionFrame("none"),
            (),
            blocked_reason="declares use: <...>, unsupported until I4.1",
        )

    allow, allow_warns, _ = _classify_all(tools_block.allow, side="allow")
    deny, deny_warns, deny_dropped = _classify_all(tools_block.deny, side="deny")
    # A dropped deny entry forces base=none (fail-closed, D3); otherwise the
    # stated base (guaranteed "inherit"/"none" here) is narrowed via as_base.
    base = "none" if deny_dropped else as_base(tools_block.base)
    warns = allow_warns + deny_warns
    if deny_dropped:
        warns = warns + [
            "deny narrowed to base=none because an entry was dropped "
            f"({', '.join(deny_dropped)})"
        ]
    return SkillFrame(
        PermissionFrame(base, tuple(allow), tuple(deny)),
        tuple(warns),
        blocked_reason=two_empties(
            base, tools_block.allow, allow, deny_dropped=deny_dropped
        ),
    )
