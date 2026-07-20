"""Resolver for the iCoder permission system (the single ``resolve()`` entry).

Deterministic ``tool_name -> Decision`` mapping. This module imports only from
:mod:`.matcher` and :mod:`.model`; it performs no I/O and holds no global state.

``resolve`` runs the frame-first branch (:func:`_resolve_frame`) when a frame is
active, then falls through to the config path (:func:`_resolve_config`). The
config path applies config-rule precedence — specificity (primary) ->
``never>ask>allow`` -> layer order (``user->project->local->runtime``) ->
declaration order — with a fail-closed degrade path and the ``None -> ALWAYS``
default mapping (§8.4) living here, not in the model. Frame elevation beats
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
)

_LAYER_ORDER = {"user": 0, "project": 1, "local": 2, "runtime": 3}


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
    undeclared tool under ``base="none"`` is sandboxed to NEVER (ASK when the
    config is degraded — the one place degrade loosens); under ``base="inherit"``
    it falls through to the config path (return ``None``).

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
        _, best = max(
            cands,
            key=lambda ir: (
                specificity(ir[1].matcher),
                ir[1].policy.rank,
                _LAYER_ORDER[ir[1].layer],
                # Final tie-break: earlier declaration wins, so negate the
                # index — a lower index must score higher under ``max``.
                -ir[0],
            ),
        )
        matched = best.matcher.origin or best
        return Decision(best.policy, Layer(best.layer), matched, None)

    pol = config.default_policy or Policy.ALWAYS
    return Decision(pol, Default(), None, None)
