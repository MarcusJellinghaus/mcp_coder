"""Data model for the iCoder permission system (pure, provider-agnostic).

Frozen dataclasses / enum only — no logic beyond :attr:`Policy.rank`, no I/O,
no global state. Mirrors the frozen-dataclass + tagged-union style used in
``icoder/core/types.py`` (``Action = Quit | ClearOutput | ...``).

Group/scenario *matching*, ``@ref`` expansion, and arg-predicate *evaluation*
are deferred to downstream issues; the structure is defined and populatable
here, but not exercised.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Mapping, NamedTuple

WILDCARD = "*"


class Policy(Enum):
    """Three-valued permission policy (with Claude config-string aliases)."""

    ALWAYS = "always"  # Claude alias: allow
    AFTER_APPROVAL = "ask"  # Claude alias: ask
    NEVER = "never"  # Claude alias: deny

    @property
    def rank(self) -> int:
        """Tie-break rank: NEVER (2) > AFTER_APPROVAL (1) > ALWAYS (0).

        Returns:
            Integer rank used to resolve equal-specificity ties.
        """
        return {Policy.NEVER: 2, Policy.AFTER_APPROVAL: 1, Policy.ALWAYS: 0}[self]


class Specificity(NamedTuple):
    """Matcher specificity — compares lexicographically for free.

    ``arg_rank`` dominates, then ``concrete_tool``, then ``concrete_server``.
    """

    arg_rank: int
    concrete_tool: int
    concrete_server: int


@dataclass(frozen=True)
class ArgPredicate:
    """A parsed argument predicate. Parsed only — not evaluated in M2."""

    name: str
    value: str
    is_glob: bool = False


@dataclass(frozen=True)
class Rule:
    """A single permission rule carrying its layer and provenance."""

    matcher: "Matcher"
    policy: Policy
    layer: str  # "user" | "project" | "local" | "runtime"
    source_path: Path | None = None  # declared here, populated by I2.2


@dataclass(frozen=True)
class Matcher:
    """A server/tool(/arg) matcher; ``*`` on server/tool means wildcard."""

    server: str  # concrete or WILDCARD
    tool: str  # concrete or WILDCARD
    arg: ArgPredicate | None = None
    origin: Rule | None = None  # provenance hook; populated downstream (I2.2/I4.1)


@dataclass(frozen=True)
class PermissionFrame:
    """A permission frame layered above config rules."""

    base: str  # "inherit" | "none"
    allow: tuple[Matcher, ...] = ()
    deny: tuple[Matcher, ...] = ()


@dataclass(frozen=True)
class PermissionConfig:
    """Merged permission config across all layers.

    Not required to be hashable: its ``dict``-valued ``groups``/``scenarios``
    fields make ``hash()`` raise ``TypeError`` even though the dataclass is
    frozen.
    """

    rules: tuple[Rule, ...] = ()  # all layers, declaration-ordered
    default_policy: Policy | None = None  # from defaultMode (None stays None here;
    # the None -> ALWAYS mapping is resolver-only, Step 3)
    groups: Mapping[str, tuple[Matcher, ...]] = field(
        default_factory=dict
    )  # stored, matched in I4.1
    scenarios: Mapping[str, tuple[Matcher, ...]] = field(
        default_factory=dict
    )  # stored, matched in I4.1
    degraded: bool = False
    errors: tuple[str, ...] = ()


# Source: tagged union (decision #3) — members carry data


@dataclass(frozen=True)
class Default:
    """Decision came from the config default policy (no matching rule)."""


@dataclass(frozen=True)
class Layer:
    """Decision came from a config rule in the named layer."""

    name: str  # "user" | "project" | "local" | "runtime"


@dataclass(frozen=True)
class Frame:
    """Decision came from the active permission frame."""


@dataclass(frozen=True)
class Degraded:
    """Decision forced by a degraded config (fail-closed)."""

    layer: str | None = None  # offending-layer identity; stays None in I2.1 (the pure
    # resolver has no per-layer attribution — populated later by I2.2 when it
    # constructs the degraded config). Not a bug.
    errors: tuple[str, ...] = ()


Source = Default | Layer | Frame | Degraded


@dataclass(frozen=True)
class Decision:
    """The resolved 3-valued permission decision plus its source."""

    policy: Policy
    source: Source
    matched_rule: Rule | None = None
    lifted_never: Policy | None = None
