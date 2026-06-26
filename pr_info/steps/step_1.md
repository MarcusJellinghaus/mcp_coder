# Step 1 — Types & persistence backfill

**Read first:** [summary.md](./summary.md) (sections "The pipeline", "Persistence",
"Liveness rule order"). This step adds the data boundaries and the persisted
fields. No behaviour changes yet — pure additions, fully unit-testable.

## WHERE
- Modify: `src/mcp_coder/workflows/vscodeclaude/types.py`
- Modify: `src/mcp_coder/workflows/vscodeclaude/sessions.py` (`load_sessions` only)
- Modify: `src/mcp_coder/workflows/vscodeclaude/helpers.py` (`build_session` — init new fields)
- Modify: `src/mcp_coder/workflows/vscodeclaude/__init__.py` (export new symbols)
- Tests: `tests/workflows/vscodeclaude/test_types.py`, `tests/workflows/vscodeclaude/test_sessions.py`

## WHAT
In `types.py`:
```python
from dataclasses import dataclass
from enum import Enum

class LivenessRule(str, Enum):
    TITLE = "title"
    PID = "pid"
    CMDLINE = "cmdline"
    NO_ARTIFACTS = "no_artifacts"
    NO_MATCH = "no_match"

class SessionAction(str, Enum):
    KEEP_ACTIVE = "keep_active"
    RESTART = "restart"
    DELETE = "delete"
    REMOVE_MISSING = "remove_missing"
    INVESTIGATE_ZOMBIE = "investigate_zombie"
    SKIP = "skip"

@dataclass(frozen=True)
class DetectionSignals:
    folder_exists: bool
    title_match: bool
    cmdline_match: bool
    pid_alive: bool
    found_pid: int | None
    age_seconds: float
    within_grace: bool       # plain bool, computed in gather_signals (Step 4)
    directory_empty: bool    # plain bool, computed in gather_signals (Step 4)

# --- typed layer results (all frozen) ---
@dataclass(frozen=True)
class LivenessVerdict:
    active: bool
    rule: LivenessRule

@dataclass(frozen=True)
class IssueState:
    is_open: bool
    is_stale: bool
    is_blocked: bool
    is_unassigned: bool
    is_eligible: bool
    stale_target: str | None = None

@dataclass(frozen=True)
class Transition:
    flipped_to_inactive: bool   # active -> inactive flip flag

@dataclass(frozen=True)
class Decision:
    action: SessionAction
    reason: str
    destructive: bool

@dataclass(frozen=True)
class SessionAssessment:
    folder: str
    signals: DetectionSignals
    verdict: LivenessVerdict
    issue_state: IssueState
    transition: Transition
    decision: Decision
    pid_needs_refresh: bool
    found_pid: int | None

    def to_audit_record(self, session: "VSCodeClaudeSession") -> dict[str, Any]:
        """ONE serializer feeding audit trail, --explain, and the VSCode column."""
    def to_explain(self) -> str:
        """Human-readable single-session dump (delegates to the same flattening)."""
```
**All assessment dataclasses are frozen** so `apply()` cannot mutate an assessment
after it is computed. `SessionAssessment` **embeds** the four typed sub-results
(`verdict`/`issue_state`/`transition`/`decision`) — it is not a flattened bag of
fields. Consumers read `a.verdict.active`, `a.verdict.rule`, `a.decision.action`,
`a.decision.reason`, `a.decision.destructive`, `a.transition.flipped_to_inactive`.
Extend `VSCodeClaudeSession` (TypedDict) with:
```python
last_active: bool | None
last_active_rule: str | None
```

## HOW
- `within_grace` and `directory_empty` are **plain bool fields**, not computed
  properties — they are gathered at the IO boundary (Step 4 `gather_signals`). This
  keeps `types.py` **dependency-free**: no import from `sessions` (no
  `LAUNCH_GRACE_SECONDS` import, no types→sessions cycle).
- `load_sessions`: in the existing per-session `setdefault` loop, add
  `session.setdefault("last_active", None)` and `session.setdefault("last_active_rule", None)`.
- `build_session` (helpers.py): add `"last_active": None, "last_active_rule": None`.
- Export `LivenessRule`, `SessionAction`, `DetectionSignals`, `LivenessVerdict`,
  `IssueState`, `Transition`, `Decision`, `SessionAssessment` from `__init__.py`
  (`from .types import ...` + `__all__`).
- The `to_audit_record`/`to_explain` serializer bodies may be stubbed here and filled
  in Step 3 (composition) / Step 9 (audit); the signature is fixed now so it is the
  single drift-proof source.

## ALGORITHM
None (declarative). The frozen layer dataclasses and embedded `SessionAssessment`
are pure data holders; the serializer flattens `signals` + `verdict` + `issue_state`
+ `transition` + `decision` into one JSON-safe dict.

## DATA
- New enums, frozen dataclasses (`DetectionSignals`, `LivenessVerdict`, `IssueState`,
  `Transition`, `Decision`, `SessionAssessment`), two new optional `VSCodeClaudeSession` keys.
- `load_sessions` returns a store whose sessions always carry `last_active`/
  `last_active_rule` (backfilled `None`).

## Tests (write first)
- Each layer dataclass and `SessionAssessment` is frozen (assert `FrozenInstanceError`
  on attribute set).
- `load_sessions` backfills `last_active=None` / `last_active_rule=None` on a JSON
  file that lacks them (write a temp file via the existing fixture pattern).
- `build_session` output contains the new keys set to `None`.

## Done when
`run_pylint_check`, `run_pytest_check(extra_args=["-n","auto","-m","not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration and not langchain_integration"])`, and `run_mypy_check` all pass. One commit.
