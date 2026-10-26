# Implementation review log 2 — issue #1299

Supervisor-driven review after rebasing onto `origin/main` @ 5d259e4 (branch head b016b6d).
Rebase notes: `main` (#1312) moved `_reset_hard` into `workflow_steps/rebase.py` with a raw
`git reset --hard`; migrated to the shim's `reset_hard`, and `workflows/rebase.py` uses a
`_restore_note` wrapper so a failed reset stays visible in the abort message.

## Round 1 — 2026-10-26
**Findings**:
- No critical/should-fix issues; rebase merge of `_reset_hard` / `_restore_note` verified correct (never raises, all five post-rebase failure paths covered).
- Minor: `_check_pr_info_absent_on_base` drops git stderr from the `list_tree` failure message.
- Minor: `_preflight` reports a failed status query as "Working tree not clean".
**Decisions**:
- Accept both minor items: both paths are new fail-closed behaviour from this PR; bounded fixes that make the error actionable.
**Changes**:
- `workflows/rebase.py`: pr_info guard error includes stderr (fallback `error`); `_preflight` returns "Could not read working tree status: …" on `success=False`, keeps "Working tree not clean" for a dirty tree.
- `tests/workflows/rebase/test_guards.py`: tests for both messages.
**Status**: committed

## Round 2 — 2026-10-26
**Findings**:
- No critical/should-fix issues; 51290c2 verified (stderr fallback safe — `GitResult.stderr` always present, `error` always set on failure).
- Minor: `_preflight` calls `is_rebase_in_progress` outside the orchestrator's try; raises `ValueError` only if the dir stops being a repo between two calls.
**Decisions**:
- Skip: practically unreachable, speculative.
**Changes**: none
**Status**: no changes needed

## Final Status
- Rounds: 2 (one with code changes, one clean).
- Commits: `b016b6d` (post-rebase format), `51290c2` (round 1 fixes), plus this log.
- vulture: clean. lint-imports: 19 contracts kept, 0 broken.
- CI green on 51290c2; branch up to date with `main`.
- No open issues.
