"""Resolver for the iCoder permission system (the single ``resolve()`` entry).

Deterministic ``tool_name -> Decision`` mapping. This module imports only from
:mod:`.matcher` and :mod:`.model`; it performs no I/O and holds no global state.

This step covers the ``frame=None`` config path (frame semantics land in Step 4):
``resolve`` delegates to :func:`_resolve_config`, which applies config-rule
precedence — specificity (primary) -> ``never>ask>allow`` -> layer order
(``user->project->local->runtime``) -> declaration order — with a fail-closed
degrade path and the ``None -> ALWAYS`` default mapping (§8.4) living here, not
in the model.
"""

from __future__ import annotations

from typing import Mapping

from mcp_coder.icoder.permissions.matcher import matches, specificity
from mcp_coder.icoder.permissions.model import (
    Decision,
    Default,
    Degraded,
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

    This step resolves the config path only; ``frame`` is ignored (Step 4 wires
    the frame-first branch above the config path) and ``args`` is intentionally
    unread in M2 (arg-predicate evaluation is deferred to I5.4).

    Args:
        tool_name: Canonical ``mcp__server__tool`` name of the call.
        args: The call arguments; accepted but unread in M2.
        frame: The active permission frame; ignored in this step.
        config: The merged permission config.

    Returns:
        The resolved :class:`Decision` (policy plus its source).
    """
    return _resolve_config(tool_name, config)


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
                -ir[0],
            ),
        )
        matched = best.matcher.origin or best
        return Decision(best.policy, Layer(best.layer), matched, None)

    pol = config.default_policy or Policy.ALWAYS
    return Decision(pol, Default(), None, None)
