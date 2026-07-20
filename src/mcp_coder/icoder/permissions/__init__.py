"""Pure, provider-agnostic core of the iCoder permission system.

This leaf package (``model`` + downstream ``matcher``/``resolver``) imports
nothing from ``icoder.ui``, ``icoder.services``, langchain, or Textual — the
boundary is pinned by the ``permissions_leaf_isolation`` import-linter contract.
"""

from __future__ import annotations

from mcp_coder.icoder.permissions.model import (
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

__all__ = [
    "WILDCARD",
    "ArgPredicate",
    "Decision",
    "Default",
    "Degraded",
    "Frame",
    "Layer",
    "Matcher",
    "PermissionConfig",
    "PermissionFrame",
    "Policy",
    "Rule",
    "Source",
    "Specificity",
]
