# Plan Review Log — Issue #856

## Round 1 — 2026-04-19

**Findings**:
- (High) Step 4: incorrect insertion point for PROJECT section — `project_dir` not resolved at planned location (between ENVIRONMENT and CONFIG)
- (Medium) Step 3: post-mypy formatting gate nested inside `check_type_hints` block — semantics unclear
- (Medium) Step 3: vague instruction to "update existing tests to mock where needed" — ~7 tests affected
- (Low) Step 2: missing test for `process_task_with_retry` parameter forwarding
- (Low) Summary: potential stale `_load_pyproject()` reference (not found on inspection)
- (Low) Step 3: missing `RUN_MYPY_AFTER_EACH_TASK=True` interaction test in core (covered by step 2)

**Decisions**:
- Accept: Fix step 4 insertion point → "after PROMPTS section"
- Accept: Add note to step 3 explaining formatting nesting is intentional (matches existing code structure)
- Accept: Expand step 3 test update note to specify ~7 `TestRunImplementWorkflow` tests
- Accept: Add forwarding test to step 2
- Skip: `_load_pyproject()` reference — not found in summary
- Skip: `RUN_MYPY_AFTER_EACH_TASK=True` interaction test — already covered by step 2 per-task tests

**User decisions**: none (all straightforward improvements)

**Changes**: step_2.md, step_3.md, step_4.md updated

**Status**: committed (a88d899)

## Round 2 — 2026-04-19

**Findings**:
- (Medium) Step 3: test count "~7" is inaccurate (~25 tests affected), but most pass via graceful fallback without mocking
- (Medium) Step 3: config placement heading should specify "inside the try block"
- (Medium) Step 2: 3 existing tests will break due to False defaults — need explicit `format_code=True`/`check_type_hints=True`
- (Low) Step 3: `test_run_implement_workflow_success` assertion should also verify new keyword arguments

**Decisions**:
- Accept: Rewrite step 3 test guidance to explain graceful fallback (no blanket mocking)
- Accept: Fix config placement heading to "inside the try block, before Step 2 — prepare_task_tracker"
- Accept: Enumerate 3 breaking tests in step 2
- Accept: Add note about positional vs keyword arg assertions

**User decisions**: none (all straightforward improvements)

**Changes**: step_2.md, step_3.md updated

**Status**: committed (e422b82)

## Round 3 — 2026-04-19

**Findings**:
- All round 2 fixes verified correct against source code
- (Low) Step 3 test `test_run_implement_workflow_skips_final_formatting_when_disabled` should specify `check_type_hints=True, format_code=False` to properly test the nested gate

**Decisions**:
- Accept: Clarify test config combination
- Skip: RUN_MYPY_AFTER_EACH_TASK patch note already correct in step 2

**User decisions**: none

**Changes**: step_3.md updated (test description precision)

**Status**: pending commit
