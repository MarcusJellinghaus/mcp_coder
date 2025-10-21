# Implementation Task: Rename `main()` to `run_create_plan_workflow()` (step_2b.md)

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

Current task from TASK_TRACKER.md: Rename `main()` to `run_create_plan_workflow()` (step_2b.md)

Please implement this task step by step.

## LLM Response:
Perfect! All Step 2b tasks are now marked as complete. Let me create a summary of what was accomplished:

---

## ✅ Step 2b Complete: Refactor Main Function Signature

**Task completed successfully!** All requirements from step_2b.md have been implemented and verified.

### Summary of Changes

**File Modified:** `src/mcp_coder/workflows/create_plan.py:510-622`

**Key Changes:**
1. ✅ **Function Renamed:** `main()` → `run_create_plan_workflow()`
2. ✅ **New Signature:** Added 4 parameters (issue_number, project_dir, provider, method)
3. ✅ **Return Type:** Changed from `None` to `int` (returns 0 for success, 1 for error)
4. ✅ **Updated Docstring:** Added comprehensive Args and Returns sections
5. ✅ **Removed CLI Logic:** Removed argument parsing, project_dir resolution, and logging setup
6. ✅ **LLM Method Construction:** Added `llm_method = f"{provider}_code_{method}"`
7. ✅ **Parameter References:** Replaced all `args.issue_number` and `args.llm_method` with direct parameters
8. ✅ **Exit Code Handling:** Replaced all `sys.exit()` calls with return statements (7 total replacements)
9. ✅ **Backward Compatibility:** Updated `if __name__ == "__main__":` block to call new function (temporary, will be removed in Step 2c)

### Code Quality Verification

All code quality checks passed:
- ✅ **Pylint:** No issues found
- ✅ **Mypy:** No type errors found
- ✅ **Pytest:** 1088 tests passed, 4 skipped

### Commit Message Prepared

```
refactor(workflows): rename main() to run_create_plan_workflow() with new signature

- Rename function from main() to run_create_plan_workflow()
- Update signature to accept 4 parameters: issue_number, project_dir, provider, method
- Change return type from None to int (returns exit codes 0 or 1)
- Replace all sys.exit() calls with return statements
- Add llm_method construction from provider and method parameters
- Update docstring with Args and Returns sections
- Remove argument parsing, project_dir resolution, and logging setup (moved to CLI layer)
- Update __main__ block to call new function (temporary, will be removed in Step 2c)
```

### Next Steps

The next task is **Step 2c: Remove CLI Parsing Code** which will:
- Delete the `parse_arguments()` function
- Delete the `if __name__ == "__main__":` block
- Clean up any remaining CLI-specific code

**All CLAUDE.md requirements followed:** MCP tools used exclusively for file operations and code quality checks.

---
Generated on: 2025-10-21T15:24:50.250833