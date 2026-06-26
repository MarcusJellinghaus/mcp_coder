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
    @property
    def within_grace(self) -> bool: ...   # age_seconds < LAUNCH_GRACE_SECONDS

@dataclass(frozen=True)
class SessionAssessment:
    folder: str
    signals: DetectionSignals
    active: bool
    rule: LivenessRule
    action: SessionAction
    reason: str
    destructive: bool
    flipped_to_inactive: bool
    pid_needs_refresh: bool
    found_pid: int | None
```
Extend `VSCodeClaudeSession` (TypedDict) with:
```python
last_active: bool | None
last_active_rule: str | None
```

## HOW
- Keep `LAUNCH_GRACE_SECONDS` defined in `sessions.py`; `DetectionSignals.within_grace`
  imports it lazily (function-local import) to avoid a types→sessions import cycle.
- `load_sessions`: in the existing per-session `setdefault` loop, add
  `session.setdefault("last_active", None)` and `session.setdefault("last_active_rule", None)`.
- `build_session` (helpers.py): add `"last_active": None, "last_active_rule": None`.
- Export `LivenessRule`, `SessionAction`, `DetectionSignals`, `SessionAssessment`
  from `__init__.py` (`from .types import ...` + `__all__`).

## ALGORITHM
None (declarative). `within_grace`:
```
from .sessions import LAUNCH_GRACE_SECONDS
return self.age_seconds < LAUNCH_GRACE_SECONDS
```

## DATA
- New enums, two frozen dataclasses, two new optional `VSCodeClaudeSession` keys.
- `load_sessions` returns a store whose sessions always carry `last_active`/
  `last_active_rule` (backfilled `None`).

## Tests (write first)
- `DetectionSignals.within_grace` True below / False above grace.
- `load_sessions` backfills `last_active=None` / `last_active_rule=None` on a JSON
  file that lacks them (write a temp file via the existing fixture pattern).
- `build_session` output contains the new keys set to `None`.

## Done when
`run_pylint_check`, `run_pytest_check(extra_args=["-n","auto","-m","not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration and not langchain_integration"])`, and `run_mypy_check` all pass. One commit.
