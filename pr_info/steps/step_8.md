# Step 8 — Status migration (enriched `VSCode` column, write-free)

**Read first:** [summary.md](./summary.md) (sections "Transparency" surface 1,
"`status` is write-free", R1). Status becomes the 5th consumer and the always-on
transparency surface.

## WHERE
- Modify: `src/mcp_coder/workflows/vscodeclaude/status.py` (`display_status_table`)
- Modify: `src/mcp_coder/cli/commands/coordinator/commands.py` (status entrypoint
  already builds assessments in Step 5 — pass them in)
- Tests: `tests/workflows/vscodeclaude/test_status_display.py`,
  `tests/workflows/vscodeclaude/test_next_action.py`

## WHAT
`display_status_table(..., assessments: dict[str, SessionAssessment], ...)` replaces
the `active_set` parameter. The `VSCode`/`Next Action` columns render the assessment.

## HOW
- One consumer migration: flip `display_status_table`'s signature **and** its
  `commands.py` status call site in the **same** commit (green-state ordering, Step 5).
  This is the last consumer; `active_set` / `build_active_session_set` can be retired.
- Per session row, read `a = assessments[folder]`; **do not** recompute liveness,
  staleness, closed, or next action (R1). Prefer the shared serializer
  (`a.to_explain()` / fields off `a.to_audit_record()`) so the column cannot drift from
  audit/`--explain`. Map to display:
  - `VSCode` column: enrich with the winning rule —
    `a.verdict.active` → `f"Running ({a.verdict.rule.value})"`; inactive →
    `f"Closed ({a.verdict.rule.value})"`; `INVESTIGATE_ZOMBIE` → `"Running (zombie)"`.
  - `Next Action` column: derive from `a.decision.action` (KEEP_ACTIVE → `(active)`,
    RESTART → `-> Restart`, DELETE → `-> Delete (with --cleanup)`,
    REMOVE_MISSING → `-> Remove`, INVESTIGATE_ZOMBIE → `-> Investigate zombie`,
    SKIP → `!! <reason>`).
- Keep `get_next_action` only for the **eligible-issues-without-session** rows (no
  assessment exists for those); session rows use the assessment.
- **Write-free:** confirm no `update_session_pid` / `save_sessions` reachable from
  the status path (the old write happened via `build_active_session_set`; Step 5
  already removed it from status).
- Remove the now-dead `display_status_table` recompute block that called
  `is_session_stale` / `is_issue_closed` / `check_folder_dirty` for the action
  (git status string may still be shown in the `Git` column via `get_folder_git_status`).

## ALGORITHM (session row)
```
a = assessments.get(session["folder"])
vscode = ("Running (%s)" % a.verdict.rule.value if a.verdict.active
          else "Closed (%s)" % a.verdict.rule.value)
action = (ACTION_DISPLAY[a.decision.action] if a.decision.action is not SKIP
          else "!! %s" % a.decision.reason)
row = [repo, issue, status_label, folder, git_status, vscode, action]
```

## DATA
Prints the table; returns `None`.

## Tests (write first)
- Restore case: assessment `active, rule=TITLE` → `VSCode` cell == `"Running (title)"`.
- Closed no-match → `"Closed (no_match)"`.
- Zombie → `"Running (zombie)"`, action `-> Investigate zombie`.
- Status path performs **no** disk writes (patch `save_sessions`, assert not called).
- Status and cleanup produce the same action for the same assessment (shared-object test).

## Done when
All three checks pass. One commit.
