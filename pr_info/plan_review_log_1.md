# Plan Review Log — Issue #624

CLI: add '--help' hint to argument error messages

## Round 1 — 2026-03-29
**Findings**:
- 1 Critical: `_handle_coordinator_command` has 3 error paths, not 1 — plan must enumerate all three explicitly
- 10 Accept: overall structure, subclass approach, algorithm, manual error paths, dead code skipping, test strategies, exit codes, new test file, YAGNI compliance all sound
- 1 Skip: line count estimates (irrelevant per planning principles)

**Decisions**:
- Critical #7: Accept and fix — straightforward factual correction, no design decision needed
- All Accept items: no changes needed
- Skip #10: ignored

**User decisions**: none needed

**Changes**: Updated `pr_info/steps/step_2.md` — expanded coordinator table to list all 3 error paths, updated test entry to note parameterized coverage of all 3 paths

**Status**: committed (7241951)

## Round 2 — 2026-03-29
**Findings**: Re-verified step_2.md against source code — all 3 coordinator error paths now correctly enumerated, test section updated with parameterized coverage note.
**Decisions**: No further changes needed.
**User decisions**: none
**Changes**: none
**Status**: no changes needed

## Round 3 — 2026-03-29
**Findings**: Dead "unknown subcommand" else branches identified in 6 locations across `main.py`. These are unreachable because argparse validates subcommand choices during `parse_args()`.
**Decisions**: Add as new Step 3 in the plan per user request.
**User decisions**: User requested dead code removal be added to the plan. Instructed that the implementation step should only remove code that is verified to be truly dead — if analysis is wrong and a branch is reachable, leave it alone.
**Changes**: Added `step_3.md`, updated `summary.md` and `TASK_TRACKER.md`
**Status**: committed

## Final Status

- **Rounds**: 3 (2 with changes, 1 verification)
- **Commits**: 3
- **Plan status**: Ready for approval. All review findings resolved. Plan has 3 steps: parser subclass, CLI wiring, dead code removal.
