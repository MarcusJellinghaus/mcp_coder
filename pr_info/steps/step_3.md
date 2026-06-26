# Step 3 — Layered issue-state + transition + decision + composition (`assess_session`) — pure

**Read first:** [summary.md](./summary.md) (sections "Explicit layered assessment
model", "The pipeline", "Key behavioural fixes" R1/R6 + git-status safety matrix,
"Liveness rule order"). This builds the remaining pure layers — each producing an
**immutable typed value** — and composes them into one frozen `SessionAssessment`, so
cleanup and status can never disagree on the same snapshot.

## WHERE
- Modify: `src/mcp_coder/workflows/vscodeclaude/assessment.py`
- Tests: `tests/workflows/vscodeclaude/test_assessment.py`
- Modify: `__init__.py` (export `IssueFacts`, `assess_issue_state`, `assess_transition`,
  `decide`, `assess_session`)

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

def assess_issue_state(issue_facts: IssueFacts) -> IssueState:
    """Pure: classify issue (open/stale/blocked/unassigned/eligible)."""

def assess_transition(prior_last_active: bool | None, verdict: LivenessVerdict) -> Transition:
    """Pure: the active->inactive flip flag (None prior => no flip)."""

def decide(
    verdict: LivenessVerdict,
    issue_state: IssueState,
    transition: Transition,
    git_status: str,          # "Clean"|"Dirty"|"Missing"|"No Git"|"Error"
    directory_empty: bool,
) -> Decision:
    """Pure: owns the FULL git-status safety matrix + zombie/keep/restart actions."""

def assess_session(
    folder: str,
    signals: DetectionSignals,
    issue_facts: IssueFacts,
    git_status: str,
    directory_empty: bool,
    prior_last_active: bool | None,
) -> SessionAssessment:
    """Pure composer: liveness -> issue-state -> transition -> decision,
    aggregated into one frozen SessionAssessment that EMBEDS the four sub-results."""
```

## HOW
- Each layer is a separate **pure** function returning a frozen typed value, and is
  individually unit-testable with injected inputs (no Windows).
- `assess_session` composes them:
  `verdict = assess_liveness(signals)`; `issue_state = assess_issue_state(issue_facts)`;
  `transition = assess_transition(prior_last_active, verdict)`;
  `decision = decide(verdict, issue_state, transition, git_status, directory_empty)`.
- `pid_needs_refresh = verdict.active and signals.found_pid is not None`; pass
  `found_pid` through. (The actual write happens in `apply_assessments`, Step 5.)
- `decision.destructive` is an **explicit bool**, set True **only** on `DELETE`.
- `decide` owns the **full safety matrix** (DECISION 2), mirroring today's
  `cleanup_stale_sessions` — no consumer re-derives it.
- The serializer `SessionAssessment.to_audit_record()` / `to_explain()` is finalised
  here as the **single** source feeding all three transparency surfaces.

## ALGORITHM (`decide`)
```
if verdict.active and not <folder present>:  return Decision(INVESTIGATE_ZOMBIE, "folder missing, process alive", False)
if verdict.active:                           return Decision(KEEP_ACTIVE, "active (%s)" % verdict.rule.value, False)
if git_status == "Missing":                  return Decision(REMOVE_MISSING, "folder missing", False)
if git_status == "Dirty":                    return Decision(SKIP, "dirty", False)
if not issue_state.is_eligible:              # stale/closed/blocked/unassigned -> destruction candidate
    if git_status == "Clean" or directory_empty:
        return Decision(DELETE, "<joined reasons>", True)        # the ONLY destructive branch
    # "No Git" / "Error" on a NON-empty folder -> destruction on weak evidence: refuse
    return Decision(SKIP, "unverified git status (%s), non-empty" % git_status, False)
return Decision(RESTART, "restartable", False)
```
Note: zombie vs. remove-missing distinguishes folder presence via `verdict.rule ==
NO_ARTIFACTS` / `signals.folder_exists`; `assess_session` passes what `decide` needs.
The full matrix is: `Clean → DELETE`, `Missing → REMOVE_MISSING`, `Dirty → SKIP`,
`No Git`/`Error` → DELETE only if `directory_empty` else `SKIP`, plus zombie /
keep-active / restart.

## DATA
Frozen `IssueState`, `Transition`, `Decision`; a fully-populated frozen
`SessionAssessment` embedding all four typed sub-results (Step 1 shape).

## Tests (write first)
- **Per-layer (injected inputs):** `assess_issue_state` maps each fact combo;
  `assess_transition(True, inactive verdict) → flipped_to_inactive=True`,
  `assess_transition(None, ...) → False`; `decide` matrix cases below.
- Zombie: `active via PID + folder gone` → `INVESTIGATE_ZOMBIE`, `destructive=False`.
- Remove-missing: inactive + `git_status="Missing"` → `REMOVE_MISSING`.
- Delete: inactive + folder exists + stale + `Clean` → `DELETE`, `destructive=True`,
  reason contains `stale_target`.
- Skip-dirty: inactive + `Dirty` + stale → `SKIP`, reason `"dirty"`, `destructive=False`.
- **No-Git non-empty (DECISION 2 fix):** inactive + stale + `git_status="No Git"` +
  `directory_empty=False` → `SKIP` (NOT delete), `destructive=False`.
- **No-Git empty:** inactive + stale + `"No Git"` + `directory_empty=True` → `DELETE`,
  `destructive=True`.
- Restart: inactive + `Clean` + eligible issue → `RESTART`.
- Keep-active: title hit + folder exists → `KEEP_ACTIVE`.
- Transition via composer: `prior_last_active=True`, now inactive →
  `transition.flipped_to_inactive=True`; `None` → `False` (backfill blind spot).
- `pid_needs_refresh`/`found_pid` propagation on an active cmdline match.
- **Typed invariant test:** assert across the decision matrix that **no** `Decision`
  has `destructive=True` unless `git_status == "Clean"` OR `directory_empty is True`.
- Serializer: `to_audit_record()` flattens verdict+issue_state+transition+decision+
  signals into a JSON-safe dict; `to_explain()` contains the winning rule and action.

## Done when
All three checks pass. One commit.
