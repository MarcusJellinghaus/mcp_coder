# Step 3 — Issue-state + transition + decision (`assess_session`) — pure

**Read first:** [summary.md](./summary.md) (sections "The pipeline", "Key
behavioural fixes" R1/R6, "Liveness rule order"). This unifies what cleanup and
status currently recompute independently into **one pure decision**, so they can
never disagree on the same snapshot.

## WHERE
- Modify: `src/mcp_coder/workflows/vscodeclaude/assessment.py`
- Tests: `tests/workflows/vscodeclaude/test_assessment.py`
- Modify: `__init__.py` (export `IssueFacts`, `assess_session`)

## WHAT
```python
@dataclass(frozen=True)
class IssueFacts:
    is_closed: bool
    is_stale: bool
    is_blocked: bool
    is_unassigned: bool
    is_ineligible: bool
    stale_target: str | None = None   # e.g. "status-05:bot-pickup" for the reason string

def assess_session(
    folder: str,
    signals: DetectionSignals,
    issue_facts: IssueFacts,
    git_status: str,                  # "Clean"|"Dirty"|"Missing"|"No Git"|"Error"
    prior_last_active: bool | None,
) -> SessionAssessment:
    """Pure: liveness -> transition -> decision, aggregated into one object."""
```

## HOW
- Calls `assess_liveness(signals)` for `(active, rule)`.
- `flipped_to_inactive = bool(prior_last_active) and not active` (None → no flip).
- `pid_needs_refresh = active and signals.found_pid is not None`; pass `found_pid`
  through. (The actual write happens in `apply_assessments`, Step 5.)
- `destructive = action is SessionAction.DELETE`.
- Decision precedence mirrors today's `get_next_action` + `get_stale_sessions`
  reason logic, now centralised. Branch skip-reasons stay in restart (Step 7).

## ALGORITHM (decision section)
```
active, rule = assess_liveness(signals)
if active and not signals.folder_exists: action, reason = INVESTIGATE_ZOMBIE, "folder missing, process alive"
elif active:                              action, reason = KEEP_ACTIVE, "active (%s)" % rule.value
elif not signals.folder_exists:           action, reason = REMOVE_MISSING, "folder missing"
elif git_status == "Dirty":               action, reason = SKIP, "dirty"
elif issue_facts says stale/closed/blocked/unassigned/ineligible:
                                          action, reason = DELETE, "<joined reasons>"   # destructive
else:                                     action, reason = RESTART, "restartable"
```

## DATA
A fully-populated `SessionAssessment` (Step 1 shape).

## Tests (write first)
- Zombie: `active via PID + folder_exists=False` → `INVESTIGATE_ZOMBIE`,
  `destructive=False`.
- Remove-missing: inactive + folder gone → `REMOVE_MISSING`.
- Delete: inactive + folder exists + `is_stale=True` + Clean → `DELETE`,
  `destructive=True`, reason contains `stale_target`.
- Skip-dirty: inactive + Dirty + stale → `SKIP`, reason `"dirty"`, `destructive=False`.
- Restart: inactive + Clean + no issue problems → `RESTART`.
- Keep-active: title hit + folder exists → `KEEP_ACTIVE`.
- Transition: `prior_last_active=True`, now inactive → `flipped_to_inactive=True`;
  `prior_last_active=None` → `False` (backfill blind spot).
- `pid_needs_refresh`/`found_pid` propagation on an active cmdline match.

## Done when
All three checks pass. One commit.
