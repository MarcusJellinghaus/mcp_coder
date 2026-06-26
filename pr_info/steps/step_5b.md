# Step 5b — `build_assessments` + `apply_assessments`; wire entrypoints (observe/apply split)

**Read first:** [summary.md](./summary.md) (sections "The pipeline", R2 observe/apply,
"`status` is write-free") and [step_5.md](./step_5.md) (the `_issue_facts` helper this
step consumes). This is the orchestration half of the hinge: one read-only builder
feeds all five consumers; one apply step holds every mutation.

## WHERE
- Modify: `src/mcp_coder/workflows/vscodeclaude/assessment.py`
- Modify: `src/mcp_coder/workflows/vscodeclaude/sessions.py` (`build_active_session_set` → thin wrapper)
- Modify: `src/mcp_coder/cli/commands/coordinator/commands.py` (launch + status entrypoints)
- Tests: `tests/workflows/vscodeclaude/test_assessment.py`, update `tests/workflows/vscodeclaude/test_active_set_invariant.py`, `test_sessions.py`

## WHAT
```python
def build_assessments(
    sessions: list[VSCodeClaudeSession],
    cached_issues_by_repo: dict[str, dict[int, IssueData]] | None = None,
) -> dict[str, SessionAssessment]:
    """READ-ONLY. Snapshot once, gather+assess each session. No disk writes."""

def apply_assessments(
    assessments: dict[str, SessionAssessment],
    *, write_audit: bool,
) -> None:
    """apply()-runs only: refresh PIDs, advance last_active/last_active_rule.
    (Audit writing added in Step 9; write_audit param reserved.)"""
```

## HOW
- `build_assessments` calls `capture_detection_snapshot()` once, then per session:
  `gather_signals` → `_issue_facts(session, cached_issue, ...)` (Step 5 helper) +
  `git_status` (reuse `get_folder_git_status`) → `assess_session`.
- **`prior_last_active` wiring:** `build_assessments` reads `session["last_active"]`
  (backfilled `None` in Step 1) and passes it into `assess_session`, which forwards it
  to `assess_transition`. `directory_empty` comes from `signals.directory_empty`.
- `build_active_session_set` becomes a **thin read-only wrapper**:
  `return {f: a.verdict.active for f, a in build_assessments(sessions).items()}` —
  preserves the existing `dict[folder, bool]` contract while computing the snapshot
  once. **Keep this wrapper** (Steps 6/7/8 consumers and four test files rely on it; see
  Step 8).
- **Green-state ordering:** after building `assessments`, the launch path keeps feeding
  the **old-shape** `active_set = {f: a.verdict.active for f, a in assessments.items()}`
  to not-yet-migrated consumers so the build stays green. Steps 6/7/8 each then flip
  **one** consumer's signature **and** its `commands.py` call site together (one
  consumer per commit); the `active_set` shim is removed once the last consumer is
  migrated (the `build_active_session_set` wrapper itself stays — Step 8).
- `commands.py` launch path: replace `active_set = build_active_session_set(...)`
  with `assessments = build_assessments(sessions_list, cached_issues_by_repo)`;
  after cleanup/restart, call `apply_assessments(assessments, write_audit=True)`.
- `commands.py` status path: `assessments = build_assessments(...)`; **never** call
  `apply_assessments` (write-free).

## ALGORITHM (`apply_assessments`)
```
store = load_sessions()
for s in store["sessions"]:
    a = assessments.get(s["folder"])
    if a is None: continue
    if a.pid_needs_refresh and a.found_pid != s.get("vscode_pid"): update fields
    s["last_active"], s["last_active_rule"] = a.verdict.active, a.verdict.rule.value
save_sessions(store)   # single atomic write (no double-write like today)
```

## DATA
`dict[folder, SessionAssessment]`; `apply_assessments` returns `None` (side effects only).

## Tests (write first)
- `build_assessments` performs **no** disk writes (assert `sessions.json` mtime/content
  unchanged; patch `save_sessions` and assert not called).
- snapshot captured exactly once per `build_assessments` call (patch
  `capture_detection_snapshot`, assert call count == 1).
- `apply_assessments` advances `last_active`/`last_active_rule` and refreshes PID once.
- `build_active_session_set` still returns `dict[folder, bool]` (back-compat invariant test).

## Done when
All three checks pass; existing active-set invariant tests updated and green. One commit.
