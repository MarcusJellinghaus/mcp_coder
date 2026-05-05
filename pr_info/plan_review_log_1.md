# Plan Review Log — Run 1

**Issue**: #949 — user_config: full ~/.mcp_coder cleanup via mcp_coder_utils.user_app_data
**Branch**: 949-user-config-full-mcp-coder-cleanup-via-mcp-coder-utils-user-app-data
**Started**: 2026-05-05

Plan files reviewed: `pr_info/steps/summary.md`, `pr_info/steps/step_1.md` … `step_5.md`.
Implementation state: not started (TASK_TRACKER empty).


## Round 1 — 2026-05-05

**Findings** (from engineer review subagent):
1. Docs sweep file list overstated — only 4 of 9 listed files actually contain `.config/mcp_coder` patterns.
2. `docs/configuration/mlflow-integration.md` table collapses from 2 rows to 1, not just a path swap.
3. `get_config_file_path` docstring rewrite needs to be explicit (delete platform bullets + XDG comment).
4. `test_path_consistency` deletion — coverage already preserved by replacement test (skip).
5. Tool name typos: `mcp__tools-py__` and `mcp__workspace__` should be `mcp__mcp-tools-py__` / `mcp__mcp-workspace__`.
6. `tools/get_recent_mlflow_runs.py` and `get_mlflow_config.py` have no phantom fallback — only 4 of 6 files collapse a list.
7. `import platform` cleanup in `tests/utils/test_user_config_integration.py` should be definitive, not hedged.
8. Step 2 has a contradictory "update docstring … leaves literal as-is" sentence for `session_finder.py`.
9. Acceptance wording about "all `Path.home() / ".mcp_coder"` patterns replaced" is acceptable as-is (skip).

**Decisions**:
- Accept 1, 2, 3, 5, 7, 8 — mechanical / clarity fixes.
- Skip 4, 9 — coverage preserved / wording fine.
- Finding 6 → folded into Fix G: keep step 4 flat, add a one-sentence clarification distinguishing the 4 phantom-fallback files from the 2 single-literal files.

**User decisions**: None — all triage decisions were mechanical or polish-tier; defaulted to simpler plan per supervisor guidance. The three open questions raised by the engineer (docs-list trim, verify-output test, step-4 split) were resolved autonomously: trim to 4 + grep guard, rely on existing fixture update, keep step 4 flat with a clarifying sentence.

**Changes** (from engineer plan-update subagent):
- Fix A: trimmed docs list to 4 files in `step_5.md` and `summary.md`; kept final grep-guard.
- Fix B: added bullet about mlflow-integration.md table collapse.
- Fix C: explicit deletion call-out for old docstring platform bullets + XDG comment + `r` prefix in `step_1.md`.
- Fix D: replaced 20× `mcp__tools-py__` and 1× `mcp__workspace__` across all 5 step files.
- Fix E: definitive `import platform` deletion wording in `step_1.md`.
- Fix F: removed contradictory `session_finder.py` docstring sentence in `step_2.md`; same hedge removed from `summary.md`.
- Fix G: one-sentence pattern clarification near top of `step_4.md` WHAT section.

**Status**: changes applied to plan files; commit pending via commit agent.


## Round 2 — 2026-05-05

**Findings** (from engineer review subagent):
1. `summary.md:93` step-plan table row still says "9 docs files" — orphan from round 1 Fix A (which trimmed the prose list but missed the trailing table).
2. `docs/configuration/mlflow-integration.md` artifact is a 2-bullet list under a `**Location**:` heading, not a Markdown table; round 1 Fix B used the word "table" in 3 plan spots — wording mismatch that would mislead the implementer.

**Decisions**: Accept both. Pure mechanical text edits, no design implications.

**User decisions**: None.

**Changes** (from engineer plan-update subagent):
- Fix 1: `summary.md` step-plan table row 5 → "4 docs files".
- Fix 2: replaced "table" with "bullet list" in 3 originally-flagged spots — `summary.md` line 74, `step_5.md` line 19 parenthetical, `step_5.md` lines 37–39 explanatory bullet — plus a fourth consistency fix at `step_5.md` line 7 (LLM prompt) that the round-2 reviewer didn't flag but used the same wrong wording.

Round-1 Fix verification (per round-2 reviewer):
- Fixes C, D, E, F, G — fully applied.
- Fixes A, B — landed in prose but had orphan/mismatch artifacts; closed by round-2 fixes above.

**Status**: changes applied; commit pending via commit agent.


## Round 3 — 2026-05-05

**Findings**: none.
**Decisions**: n/a.
**User decisions**: none.
**Changes**: none.
**Status**: CONVERGED — round-2 fixes verified applied, all acceptance items still covered, no new issues.

---

## Final Status

**Rounds run**: 3 (rounds 1 and 2 each produced plan edits; round 3 converged with zero changes).

**Commits produced**:
- `90cca00` — `docs(plan): refine #949 plan after review round 1` (6 plan files; 70 insertions / 41 deletions)
- `853e782` — `docs(plan): correct step 5 file count and fix bullet-list-vs-table wording` (2 plan files; 6 insertions / 6 deletions)
- (this log committed separately)

**No user escalation required** during the review — every decision was either a mechanical text fix, a clarity improvement, or a borderline call resolved by defaulting to the simpler plan (per supervisor guidance).

**Outcome**: plan is ready for approval. All issue #949 acceptance items remain covered across `pr_info/steps/step_1.md` … `step_5.md` and `pr_info/steps/summary.md`.
