"""Resolver for the iCoder permission system (the single ``resolve()`` entry).

Deterministic ``tool_name -> Decision`` mapping. This module imports only from
:mod:`.matcher` and :mod:`.model`; it performs no I/O and holds no global state.

``resolve`` runs the frame-first branch (:func:`_resolve_frame`) when a frame is
active, then falls through to the config path (:func:`_resolve_config`). The
config path applies config-rule precedence — specificity (primary) ->
``never>ask>allow`` -> layer order (``user->project->local``) -> declaration
order — with ``runtime`` sitting above that contest as its own top-priority
stage (bounded by a winning authored ``never``), a fail-closed degrade path, and
the ``None -> ALWAYS`` default mapping (§8.4) living here, not in the model.
Frame elevation beats
degrade (F4): a frame-declared tool resolves even under a degraded config, while
the fall-through and ``base="none"`` sandbox paths consult ``config.degraded``.
"""

from __future__ import annotations

from typing import Mapping

from mcp_coder.icoder.permissions.matcher import matches, specificity
from mcp_coder.icoder.permissions.model import (
    Decision,
    Default,
    Degraded,
    Frame,
    Layer,
    PermissionConfig,
    PermissionFrame,
    Policy,
    Rule,
    Specificity,
)

_LAYER_ORDER = {"user": 0, "project": 1, "local": 2, "runtime": 3}


def _rule_sort_key(ir: tuple[int, Rule]) -> tuple[Specificity, int, int, int]:
    """Rank one ``(index, rule)`` candidate for the ``max()`` contest.

    Args:
        ir: An ``(declaration index, rule)`` pair from the candidate list.

    Returns:
        The 4-key precedence tuple: specificity, then ``never>ask>allow``, then
        layer order, then the negated index (earlier declaration wins).
    """
    index, rule = ir
    return (
        specificity(rule.matcher),
        rule.policy.rank,
        _LAYER_ORDER[rule.layer],
        # Final tie-break: earlier declaration wins, so negate the index — a
        # lower index must score higher under ``max``.
        -index,
    )


def resolve(
    tool_name: str,
    args: Mapping[str, object] | None,
    frame: PermissionFrame | None,
    config: PermissionConfig,
) -> Decision:  # pylint: disable=unused-argument
    """Map a tool call to a deterministic 3-valued :class:`Decision`.

    The frame (when present) is consulted first: a frame-governed tool resolves
    via :func:`_resolve_frame`; anything the frame does not govern (base
    ``"inherit"`` undeclared) falls through to the config path. ``args`` is
    intentionally unread in M2 (arg-predicate evaluation is deferred to I5.4).

    Args:
        tool_name: Canonical ``mcp__server__tool`` name of the call.
        args: The call arguments; accepted but unread in M2.
        frame: The active permission frame, or ``None`` for the config-only path.
        config: The merged permission config.

    Returns:
        The resolved :class:`Decision` (policy plus its source).
    """
    if frame is not None:
        framed = _resolve_frame(tool_name, frame, config)
        if framed is not None:
            return framed
    return _resolve_config(tool_name, config)


def _resolve_frame(
    tool_name: str,
    frame: PermissionFrame,
    config: PermissionConfig,
) -> Decision | None:
    """Resolve ``tool_name`` against the active frame (frame-first precedence).

    Intra-frame ``deny`` beats ``allow`` (DC5). A frame elevates only what it
    declares: an ``allow``-declared tool -> ALWAYS, recording ``lifted_never``
    when it overrides a config base of ``NEVER`` (Q3: a degraded config masks the
    base, so no never is lifted). Frame elevation runs before degrade (F4). An
    undeclared tool under ``base="none"`` is sandboxed to NEVER (AFTER_APPROVAL
    with a ``Degraded`` source when the config is degraded — not a loosening:
    the gateway denies every ``Degraded``-sourced decision outright (R15), so
    the branch is an effective NEVER that merely carries the errors along);
    under ``base="inherit"`` it falls through to the config path (``None``).

    Args:
        tool_name: Canonical ``mcp__server__tool`` name of the call.
        frame: The active permission frame.
        config: The merged permission config (consulted for the base policy).

    Returns:
        A :class:`Decision` when the frame governs this tool, else ``None``.
    """
    if any(matches(m, tool_name) for m in frame.deny):
        return Decision(Policy.NEVER, Frame(), None, None)

    if any(matches(m, tool_name) for m in frame.allow):
        base = _resolve_config(tool_name, config).policy
        lifted = Policy.NEVER if base is Policy.NEVER else None
        return Decision(Policy.ALWAYS, Frame(), None, lifted)

    if frame.base == "none":
        if config.degraded:
            return Decision(
                Policy.AFTER_APPROVAL,
                Degraded(errors=config.errors),
                None,
                None,
            )
        return Decision(Policy.NEVER, Frame(), None, None)

    return None


def _resolve_config(tool_name: str, config: PermissionConfig) -> Decision:
    """Resolve ``tool_name`` against the config rules (fail-closed when degraded).

    Matching rules are partitioned on ``layer == "runtime"``: the runtime group
    is its own top-priority stage and contests alone whenever it is non-empty
    and the top-ranked authored candidate is not ``never`` (R14). Everything
    else — including the runtime rules among themselves — is decided by the
    ordinary 4-key contest of :func:`_rule_sort_key`.

    Args:
        tool_name: Canonical ``mcp__server__tool`` name of the call.
        config: The merged permission config.

    Returns:
        A :class:`Decision`: ``Degraded`` -> ASK; a matching rule -> its policy
        with a ``Layer`` source; otherwise the default policy with a ``Default``
        source (``None`` default maps to ``ALWAYS``).
    """
    if config.degraded:
        return Decision(
            Policy.AFTER_APPROVAL,
            Degraded(errors=config.errors),
            None,
        )

    cands = [
        (i, rule)
        for i, rule in enumerate(config.rules)
        if matches(rule.matcher, tool_name)
    ]
    if cands:
        # ``runtime`` is a stage, not just a layer: ``_LAYER_ORDER`` is only the
        # *third* sort key and ``Policy.rank`` puts AFTER_APPROVAL (1) above
        # ALWAYS (0), so without this partition a session grant
        # ``Rule(..., ALWAYS, "runtime")`` would lose to an authored ``ask`` on
        # the same matcher and the user would be re-prompted every turn (R14).
        runtime = [ir for ir in cands if ir[1].layer == "runtime"]
        authored = [ir for ir in cands if ir[1].layer != "runtime"]
        # Bound the widening: R14 only needs runtime to beat ``ask``, and letting
        # a *broad* runtime ``always`` shadow a *specific* authored ``never`` is
        # a security-relevant widening this issue does not need. Keyed on the
        # WINNING authored rule rather than "any authored never" — a config
        # holding both a broad ``never`` and a specific ``ask`` must not skip the
        # short-circuit, or the ``ask`` beats the grant on ``Policy.rank``. When
        # the bound engages, the authored ``never`` falls through to the ordinary
        # 4-key contest, so it loses only to a *strictly more specific* runtime
        # rule, never to a broader one.
        top_authored = max(authored, key=_rule_sort_key) if authored else None
        blocked = top_authored is not None and top_authored[1].policy is Policy.NEVER
        if runtime and not blocked:
            cands = runtime

        _, best = max(cands, key=_rule_sort_key)
        matched = best.matcher.origin or best
        return Decision(best.policy, Layer(best.layer), matched, None)

    pol = config.default_policy or Policy.ALWAYS
    return Decision(pol, Default(), None, None)
