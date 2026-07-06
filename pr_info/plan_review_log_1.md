# Plan Review Log — Issue #1021

Split `cli/commands/verify.py` + `test_verify_orchestration.py`

Supervised automated plan review. Base branch: `main`. Branch up to date (no rebase needed).

---

## Round 1 — 2026-07-06

**Findings** (from `/plan_review` engineer):
- Plan verified internally consistent with all issue requirements (move-don't-change, no re-exports, Step 2 constant-move caveat + `_VALUE_COLUMN_INDENT` ordering, allowlist-removal timing, Step 3 split-by-test-class). Importer lists, projected file sizes, and class spans all confirmed against source.
- #1 (medium): Step 2 asserts as a hard premise that `move_symbol` won't move constants, but the tool docs say it moves variables too. Should be a `dry_run` check, not a premise.
- #2 (medium): Step 2 passes through a deliberately-broken intermediate state; checks only green after full sequence. One-commit atomicity is fine but implementer must not run checks mid-sequence.
- #3 (low): `summary.md` pytest verification excludes only 6 markers vs. the 10-marker canonical in `CLAUDE.md`.
- #4 (low): Step 3 regroups non-contiguous classes — mechanical only, collection-count safeguard already present.
- #5 (info): 2 pre-existing stale allowlist entries unrelated to this issue.

**Decisions**:
- #1 → accept (reframe as `dry_run` check; safe, no scope change)
- #2 → accept (add note; keep single step/commit)
- #3 → accept (align marker list with `CLAUDE.md` canonical — prevents running integration suites)
- #4 → skip (no change needed; safeguard already present)
- #5 → skip (pre-existing, out of scope)

**User decisions**: none — all findings were bounded plan improvements, no design/requirements escalation needed.

**Changes**:
- `step_2.md`: reframed constant move as a `dry_run`-driven decision (manual move only if constants left behind); `_VALUE_COLUMN_INDENT` ordering caveat retained; added note that quality checks must not run mid-sequence.
- `summary.md`: constant-move caveat reworded to `dry_run` check; pytest marker exclusion string replaced with 11-marker canonical.

**Status**: applied — to be committed.

## Round 2 — 2026-07-06

**Findings** (from `/plan_review` engineer):
- All three Round-1 fixes verified correctly applied, no new inconsistencies introduced.
- Independent cross-checks all passed: Step 2 import-back list is exactly precise (over-broad would trip pylint `unused-import`); Step 3 covers all 11 classes exactly once with per-group spans (~624 / ~634 / ~566) under 750; in-function imports and `conftest.py` handling consistent; allowlist-removal timing correct.
- Non-blocking notes only: line-count estimates slightly stale but immaterial to any threshold decision; one pre-existing stale docstring in `test_verify_orchestration.py` (out of scope).

**Decisions**: no plan changes required — all remaining notes are immaterial or out of scope.

**User decisions**: none.

**Changes**: none to plan files. (Log wording corrected: "11-marker" → "10-marker" canonical.)

**Status**: no changes needed — loop terminates.

---

## Final Status

- **Rounds run:** 2
- **Round 1:** 5 findings; 3 accepted and applied (constant-move reframed as `dry_run` check, intermediate-broken-state note, pytest marker list aligned to `CLAUDE.md`), 2 skipped (no change needed / out of scope). Committed as `2582161`.
- **Round 2:** zero plan changes — plan verified internally consistent and implementation-ready.
- **User escalations:** none — all findings were bounded, safe plan improvements.
- **Verdict:** Plan is a faithful, mechanically-accurate move refactor consistent with issue #1021 requirements (move-don't-change, no re-exports, constant-move caveat, allowlist-removal timing, Step 3 split-by-test-class). **Ready for approval.**
