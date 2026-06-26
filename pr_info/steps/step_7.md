# Step 7 — Restart migration (zombie / remove-missing)

**Read first:** [summary.md](./summary.md) (sections "Key behavioural fixes" R6,
zombie self-resolution; "Out of scope" branch skip-reasons). Restart becomes the
4th assessment consumer.

## WHERE
- Modify: `src/mcp_coder/workflows/vscodeclaude/session_restart.py`
  (`restart_closed_sessions`)
- Tests: `tests/workflows/vscodeclaude/test_session_restart.py`,
  `tests/workflows/vscodeclaude/test_session_restart_closed_sessions.py`

## WHAT
`restart_closed_sessions(assessments: dict[str, SessionAssessment], cached_issues_by_repo=...)`
— replace the `active_set` parameter.

## HOW
- Replace `if active_set.get(folder): continue` with branch on
  `assessments[folder]`:
  - `active` (KEEP_ACTIVE or INVESTIGATE_ZOMBIE) → skip (do not restart; zombie is
    kept tracked + warned, never restarted).
  - `REMOVE_MISSING` → keep the existing `remove_session` orphan-cleanup branch
    (this is the folder-missing path it already has at `session_restart.py:261-268`).
  - `RESTART` → proceed with the existing restart flow.
  - `SKIP`/`DELETE` → skip (cleanup owns deletion).
- **Branch skip-reasons stay local:** the `!! No branch` / `!! Multi-branch` /
  `!! Dirty` git checks inside the restart flow are unchanged — they are launch-time
  git I/O, not session-state (see summary "Out of scope"). Assessment only decides
  *whether the session is a restart candidate*; the branch checks still gate the
  actual relaunch.
- `commands.py`: pass `assessments` instead of `active_set`; `current_count`
  computation uses `sum(1 for a in assessments.values() if a.active)`.

## ALGORITHM
```
for session in store["sessions"]:
    a = assessments.get(session["folder"])
    if a is None or a.active: continue          # keep-active + zombie skip here
    if a.action is REMOVE_MISSING: remove_session(...); continue
    if a.action is not RESTART: continue        # SKIP / DELETE handled elsewhere
    ... existing branch-verify + relaunch ...
```

## DATA
Returns `list[VSCodeClaudeSession]` (restarted) — unchanged.

## Tests (write first)
- Zombie assessment → **not** restarted, session retained, warning logged.
- `REMOVE_MISSING` → session removed (existing orphan behaviour preserved).
- `RESTART` candidate with a valid linked branch → restarted.
- Active (KEEP_ACTIVE) → skipped.

## Done when
All three checks pass. One commit.
