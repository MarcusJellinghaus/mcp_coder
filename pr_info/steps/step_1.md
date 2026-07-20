# Step 1 — Data model + package + import-linter contract

**Ref:** `pr_info/steps/summary.md`. One commit: tests + implementation + all checks
green.

## WHERE
- Create `src/mcp_coder/icoder/permissions/__init__.py`
- Create `src/mcp_coder/icoder/permissions/model.py`
- Create `tests/icoder/test_permissions_model.py`
- Modify `.importlinter`

## WHAT (model.py — frozen dataclasses / enum, stdlib only)

```python
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Mapping, NamedTuple

WILDCARD = "*"

class Policy(Enum):
    ALWAYS = "always"          # Claude alias: allow
    AFTER_APPROVAL = "ask"     # Claude alias: ask
    NEVER = "never"            # Claude alias: deny
    @property
    def rank(self) -> int: ...  # NEVER=2 > AFTER_APPROVAL=1 > ALWAYS=0 (tie-break)

class Specificity(NamedTuple):
    arg_rank: int
    concrete_tool: int
    concrete_server: int

@dataclass(frozen=True)
class ArgPredicate:            # parsed, NOT evaluated in M2
    name: str
    value: str
    is_glob: bool = False

@dataclass(frozen=True)
class Matcher:
    server: str               # concrete or WILDCARD
    tool: str                 # concrete or WILDCARD
    arg: ArgPredicate | None = None
    origin: "Rule | None" = None   # provenance hook; populated downstream (I2.2/I4.1)

@dataclass(frozen=True)
class Rule:
    matcher: Matcher
    policy: Policy
    layer: str                # "user" | "project" | "local" | "runtime"
    source_path: Path | None = None   # declared here, populated by I2.2

@dataclass(frozen=True)
class PermissionFrame:
    base: str                 # "inherit" | "none"
    allow: tuple[Matcher, ...] = ()
    deny: tuple[Matcher, ...] = ()

@dataclass(frozen=True)
class PermissionConfig:
    rules: tuple[Rule, ...] = ()            # all layers, declaration-ordered
    default_policy: Policy | None = None    # from defaultMode (unset stays None here;
                                            # the None -> ALWAYS mapping is resolver-only, Step 3)
    groups: Mapping[str, tuple[Matcher, ...]] = field(default_factory=dict)     # stored, matched in I4.1
    scenarios: Mapping[str, tuple[Matcher, ...]] = field(default_factory=dict)  # stored, matched in I4.1
    degraded: bool = False
    errors: tuple[str, ...] = ()

# Source: tagged union (decision #3) — members carry data
@dataclass(frozen=True)
class Default: ...
@dataclass(frozen=True)
class Layer:
    name: str                 # "user" | "project" | "local" | "runtime"
@dataclass(frozen=True)
class Frame: ...
@dataclass(frozen=True)
class Degraded:
    layer: str | None = None   # offending-layer identity; stays None in I2.1 (the pure
                               # resolver has no per-layer attribution — populated later by
                               # I2.2 when it constructs the degraded config). Not a bug.
    errors: tuple[str, ...] = ()

Source = Default | Layer | Frame | Degraded

@dataclass(frozen=True)
class Decision:
    policy: Policy
    source: Source
    matched_rule: Rule | None = None
    lifted_never: Policy | None = None
```

`__init__.py` re-exports the public names above.

## HOW (integration)
- Use `from __future__ import annotations` so `Matcher.origin: "Rule | None"` forward
  ref resolves cleanly (Rule references Matcher; Matcher references Rule).
- Mirror `icoder/core/types.py`: all `@dataclass(frozen=True)`, module docstring,
  `Source = Default | Layer | Frame | Degraded` union alias at module level.
- `.importlinter`: add a forbidden contract after the existing
  `textual_library_isolation` block:
  ```ini
  [importlinter:contract:permissions_leaf_isolation]
  name = iCoder Permissions Leaf Isolation
  type = forbidden
  source_modules =
      mcp_coder.icoder.permissions
  forbidden_modules =
      mcp_coder.icoder.ui
      mcp_coder.icoder.services
      textual
      langchain_core
      langchain_openai
      langchain_google_genai
      langchain_anthropic
  ```

## ALGORITHM
```
Policy.rank: return {NEVER:2, AFTER_APPROVAL:1, ALWAYS:0}[self]
```
No other logic in this step — model.py is pure data.

## DATA
- Frozen, hashable dataclasses. Defaults chosen so every type is constructible with
  minimal args (e.g. `PermissionConfig()` is a valid empty config; `Decision(policy,
  source)` valid with `matched_rule=None`, `lifted_never=None`).

## TESTS (write first — `test_permissions_model.py`)
- Construction of each type with defaults; `PermissionConfig()` empty is valid.
- Frozen: mutating a field raises `FrozenInstanceError`; instances are hashable.
- `Policy.rank` ordering: `NEVER.rank > AFTER_APPROVAL.rank > ALWAYS.rank`.
- `Specificity` compares lexicographically (e.g. `(1,0,0) > (0,1,1)`) and exposes
  `.arg_rank`.
- `Source` union: a `Decision` can be built with each of `Default()`, `Layer("user")`,
  `Frame()`, `Degraded(layer="project", errors=("x",))`.
- Structural fields exist & are populatable: `Matcher(origin=...)`,
  `Rule(source_path=Path(...))`, `PermissionConfig(groups=..., scenarios=...)`.

## CHECKS
Run and pass: `run_pylint_check`, `run_pytest_check` with the canonical fast-unit
selection from `.claude/CLAUDE.md`: `extra_args=["-n","auto","-m","not git_integration
and not claude_cli_integration and not claude_api_integration and not
copilot_cli_integration and not formatter_integration and not github_integration and not
jenkins_integration and not langchain_integration and not llm_integration and not
textual_integration"]`, `run_mypy_check`, and `run_lint_imports_check` (new contract must
pass).

## LLM PROMPT
> Read `pr_info/steps/summary.md` and `pr_info/steps/step_1.md`. Following TDD, first
> write `tests/icoder/test_permissions_model.py` covering the cases listed under TESTS,
> then implement `src/mcp_coder/icoder/permissions/model.py` and `__init__.py` exactly
> per the WHAT/HOW/DATA sections, and add the `permissions_leaf_isolation` contract to
> `.importlinter`. Use only stdlib and frozen dataclasses / `enum.Enum`, mirroring
> `src/mcp_coder/icoder/core/types.py`. Use MCP tools only. Then run pylint, pytest
> (with the canonical fast-unit marker exclusions from `.claude/CLAUDE.md`, see CHECKS),
> mypy(strict), and lint-imports, and fix everything until all are green. Commit as one
> change.
