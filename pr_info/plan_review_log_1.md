# review-plan review log 1

## Round 1 — 2026-10-26
**Findings**:
`pr_info/steps/summary.md:21` — medium — The `run_ruff_fix(select=["F401"])` call has no `target_directories`, so it runs on the whole project and can delete unused imports in files outside this split. Every diff would then include edits the issue does not allow. Limit it to the source and destination files touched in each step.

`pr_info/steps/step_4.md:51` — low — Moving `MODULE` on its own first will make `move_symbol` add `from …test_commit_push import MODULE` to `test_commit.py` for a while. The check only covers the opposite direction (`test_commit_push.py` must not import from `test_commit`). Add a check that `test_commit.py` ends with no import from `test_commit_push`.
**Decisions**:
Verdict(decision='tasks', tasks=['In pr_info/steps/summary.md:21 (and every step that calls it), pass `target_directories` to `run_ruff_fix(select=["F401"])` so it covers only the source and destination test files touched in that step, not the whole project.', 'In pr_info/steps/step_4.md near line 51, add a check that after all moves, `test_commit.py` has no import from `test_commit_push`. This catches the temporary `MODULE` import that `move_symbol` adds.'], escalate_reason=None)
**Changes**:
applied
