# Step 2 — Liveness layer (`assess_liveness`) — pure

**Read first:** [summary.md](./summary.md) (sections "Liveness rule order",
"Key behavioural fixes"). This is the **#38 de-risker**: the rule matrix becomes a
pure function unit-tested without Windows.

## WHERE
- Create: `src/mcp_coder/workflows/vscodeclaude/assessment.py`
- Tests: `tests/workflows/vscodeclaude/test_assessment.py`
- Modify: `src/mcp_coder/workflows/vscodeclaude/__init__.py` (export)

## WHAT
```python
from .types import DetectionSignals, LivenessRule

def assess_liveness(signals: DetectionSignals) -> tuple[bool, LivenessRule]:
    """Pure liveness verdict. Returns (active, winning_rule)."""
```

## HOW
- Pure function: no imports of `sessions`/`psutil`/`win32`. Only `types`.
- Ordering is the contract (a live process is detectable regardless of folder):
  title → pid → cmdline → folder-existence. PID is a tie-breaker, **not** a gate.
- `within_grace` does **not** change the verdict here — the grace special-case is
  handled at signal-gathering time (Step 4) by simply not penalising a missing
  title; the rule order already falls through to pid/cmdline.

## ALGORITHM
```
if signals.title_match:   return True,  LivenessRule.TITLE
if signals.pid_alive:     return True,  LivenessRule.PID
if signals.cmdline_match: return True,  LivenessRule.CMDLINE
if not signals.folder_exists: return False, LivenessRule.NO_ARTIFACTS
return False, LivenessRule.NO_MATCH
```

## DATA
`tuple[bool, LivenessRule]`.

## Tests (write first) — full matrix, no Windows
- title hit, cmdline miss (the **#38 restore case**) → `(True, TITLE)`.
- bare folder: title miss, cmdline hit → `(True, CMDLINE)` (fallthrough).
- pid alive only → `(True, PID)`.
- everything miss, folder exists → `(False, NO_MATCH)`.
- everything miss, folder gone → `(False, NO_ARTIFACTS)`.
- **zombie precursor**: folder gone but pid alive → `(True, PID)` (proves no
  folder-gone short-circuit; decision layer turns this into the zombie action in Step 3).

## Done when
All three checks pass (use the pytest exclusion marker string from Step 1). One commit.
