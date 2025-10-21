# Implementation Task: Update `tests/workflows/create_plan/test_main.py` with new import paths and function name (step_5.md)

## Prompt Sent to LLM:
You are implementing tasks from a task tracker. Follow these steps in order:

**STEP 1: SELECT TASK**
- Read `pr_info/TASK_TRACKER.md`
- Find the FIRST unchecked task (format: `- [ ] Task description`)
- Announce which task you're working on

**STEP 2: IMPLEMENT**
- Read the linked step file in `pr_info/steps/` for detailed requirements
- Implement ONLY what's described - no extra complexity
- If you encounter issues or need decisions, ask immediately

**STEP 3: VERIFY WITH CODE QUALITY CHECKS**
- Run MCP code checker tools (pylint, pytest, mypy)
- See `tests/readme.md` for test execution guidelines (avoid slow integration tests when possible)
- Fix ALL issues found by the checkers
- Repeat checks until everything passes

**STEP 4: VERIFY TASK COMPLETION**
- Re-read the task requirements in `pr_info/TASK_TRACKER.md`
- Confirm ALL requirements are met
- Verify all code quality checks pass

**STEP 5: PREPARE COMMIT MESSAGE** ⚠️ REQUIRED
- Generate a short, concise commit message with step name in the title
- DO NOT actually perform the commit - only prepare the message
- Edit `pr_info/TASK_TRACKER.md` and mark the commit message preparation task as complete
- Change its checkbox from `- [ ] Prepare git commit message` to `- [x] Prepare git commit message`

**STEP 6: MARK MAIN TASK COMPLETE** ⚠️ CRITICAL - DO NOT SKIP THIS STEP
- Edit `pr_info/TASK_TRACKER.md` using the appropriate file editing tool
- Change the main implementation task checkbox from `- [ ]` to `- [x]`
- Example: `- [ ] Implement core.py` becomes `- [x] Implement core.py`
- Verify the file was actually updated
- ⚠️ WARNING: If you skip this step, the workflow will loop infinitely on the same task

**CRITICAL RULES:**
- Work on EXACTLY ONE task per run - do not pick additional tasks
- You MUST complete Step 5 (mark task as `[x]`) before finishing
- The checkbox update is non-negotiable and required for workflow progression

Current task from TASK_TRACKER.md: Update `tests/workflows/create_plan/test_main.py` with new import paths and function name (step_5.md)

Please implement this task step by step.

## LLM Response:
Perfect! Now let me provide a summary of what was accomplished:

---

## ✅ Task Complete: Update test_main.py (Step 5)

I have successfully updated `tests/workflows/create_plan/test_main.py` with the new import paths and function references. Here's what was done:

### Changes Made:

1. **Updated imports**: Changed from `workflows.create_plan` to `mcp_coder.workflows.create_plan`
2. **Updated function name**: Changed from `main` to `run_create_plan_workflow`
3. **Removed unnecessary mocks**: Removed mocks for `parse_arguments`, `resolve_project_dir`, and `setup_logging` (now handled by CLI layer)
4. **Updated all patch paths**: All `@patch` decorators and context managers now reference `mcp_coder.workflows.create_plan.*`
5. **Updated function calls**: Tests now call `run_create_plan_workflow(issue_number, project_dir, provider, method)` directly with parameters
6. **Updated assertions**: Changed from `pytest.raises(SystemExit)` to checking return values (`assert result == 0` or `assert result == 1`)
7. **Cleaned up**: Removed unused `mock_args` fixture and `MagicMock` import

### Verification:

✅ **All tests pass**: 70 tests in `tests/workflows/create_plan/` directory pass  
✅ **Mypy check passes**: No type errors found  
✅ **Pylint check**: Only shows expected import warning (module still being migrated)  

### Commit Message Prepared:

```
test: update test_main.py imports and function references (step 5)

Update tests/workflows/create_plan/test_main.py to use new workflow location:
- Change imports from workflows.create_plan to mcp_coder.workflows.create_plan
- Update function calls from main() to run_create_plan_workflow()
- Pass parameters directly instead of mocking parse_arguments
- Remove parse_arguments, resolve_project_dir, and setup_logging mocks
- Update all patch paths to use new module location
- Change assertions from SystemExit to return value checks
- Remove unused mock_args fixture and MagicMock import

All 70 workflow tests pass. Ready for next migration step.
```

### Next Steps:

The next subtask in Step 5 is to update `tests/workflows/create_plan/test_argument_parsing.py` by deleting the `TestParseArguments` class (as specified in the TASK_TRACKER.md).

All CLAUDE.md requirements followed ✅

---
Generated on: 2025-10-21T18:06:49.160387