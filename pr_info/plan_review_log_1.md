# Plan Review Log — Issue #725

## Round 1 — 2026-04-08

**Findings**:

1. [STRAIGHTFORWARD] Step 1 setup.py skeleton missing `import shutil` and `from pathlib import Path`.
2. [DESIGN] Step 1 setup.py tests approach (unit via importlib vs integration via `python -m build`).
3. [STRAIGHTFORWARD] Step 2 `execute_init()` rename `_args` → `args` will trigger `unused-argument` pylint error before step 4 consumes the new attributes.
4. [STRAIGHTFORWARD] Step 3 `_find_claude_source_dir` should mirror `src/mcp_coder/utils/data_files.py` pattern (importlib.resources) and import `files` explicitly.
5. [STRAIGHTFORWARD] Step 3 contradiction: "at most 3 levels" note conflicts with unbounded `.parents` walk.
6. [DESIGN] Step 3/4 deploy failure path: terse `sys.exit(1)` message vs detailed (paths tried, reinstall hint).
7. [DESIGN] Step 4 self-deploy case: running `mcp-coder init` inside the mcp-coder source repo copies `.claude/` onto itself.
8. [DESIGN] Step 2/4 missing `--project-dir` path: behavior unspecified when path does not exist.
9. [STRAIGHTFORWARD] Step 3 `DEPLOY_SUBDIRS` constant defined in step 3 but only consumed in step 4 → unused-constant lint risk.
10. [STRAIGHTFORWARD] Step 4 duplicate `test_deploy_failure_exits_1` overlaps with a step 3 resolver test without a rationale note.
11. [DESIGN] MANIFEST.in reliability for including `resources/claude/**` in sdist/wheel.
12. [MINOR] Cosmetic phrasing inconsistencies in plan files.
13. [MINOR] Minor docstring wording drift.
14. [MINOR] Import-linter: no new layer needed; covered by existing checks.
15. [DESIGN] package-data glob `"resources/claude/**/*"` reliability vs explicit MANIFEST.in.

**Decisions**:
- Findings #1, #3, #4, #5, #9, #10: accepted, applied directly (straightforward fixes)
- Findings #6, #7, #8: escalated to user as design questions
- Finding #2 (setup.py test approach): escalated to user
- Finding #11, #15: escalated to user (MANIFEST.in + package-data reliability)
- Findings #12, #13 (minor/cosmetic): skipped
- Finding #14 (import-linter): no action, covered by existing checks

**User decisions**:
1. Deploy failure → exit 1 with detailed error message (paths tried, reinstall hint)
2. Self-deploy → detect source==target via .resolve(), skip silently with info log
3. Missing --project-dir → exit 1 with clear error message
4. setup.py tests → both unit (importlib) + integration (python -m build + wheel inspection)
5. MANIFEST.in → skip, rely on wheel integration test

**Changes**:
- `pr_info/steps/step_1.md`: added `shutil`/`Path` imports to skeleton; split TESTS into unit + slow wheel-build integration test asserting `skills/`, `knowledge_base/`, `commands/` inside the wheel; noted MANIFEST.in intentionally omitted.
- `pr_info/steps/step_2.md`: documented `_args` → `args` rename and harmless no-op access (`_ = (args.just_skills, args.project_dir)`) to avoid `unused-argument` pre-step-4.
- `pr_info/steps/step_3.md`: removed "at most 3 levels"; switched to unbounded `.parents` walk; required `data_files.py` pattern with explicit `from importlib.resources import files`; validate all three `DEPLOY_SUBDIRS` under resolved source; detailed sys.exit(1) error listing paths tried + reinstall hint; updated tests.
- `pr_info/steps/step_4.md`: added early `--project-dir` existence check; added self-deploy detection via `.resolve()` comparison with info-log skip; added three new test cases (`test_missing_project_dir_exits_1`, `test_self_deploy_is_skipped`); annotated `test_deploy_failure_exits_1` as integration smoke test complementing step 3.

**Status**: committed (log committed separately after round closes)

## Round 2 — 2026-04-08

**Findings**: [MINOR] Typo `commands/` should be `agents/` in step_1.md integration-test text and Decisions.md #4.
**Decisions**: Accepted — straightforward typo fix.
**User decisions**: None.
**Changes**: Fixed `commands/` → `agents/` in step_1.md and Decisions.md.
**Status**: committed.

## Final Status

**Rounds run:** 3
**Commits produced:**
- Round 1: plan(725): incorporate round-1 review decisions
- Round 2: plan(725): fix commands/ → agents/ typo
- Final: plan(725): finalize review log

**Outcome:** Plan is stable and ready for approval. All round-1 design decisions (deploy failure error, self-deploy detection, --project-dir validation, setup.py test strategy, MANIFEST.in omission) applied. Round 2 caught one typo (`commands/` → `agents/`). Round 3 found zero new issues.
