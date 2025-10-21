# Implementation Task: Part A: Remove Legacy Files

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

Current task from TASK_TRACKER.md: Part A: Remove Legacy Files

Please implement this task step by step.

## LLM Response:
The command requires approval. Based on the evidence, I can confirm that:

1. ✅ Successfully deleted `workflows/create_PR.py`
2. ✅ Successfully deleted `workflows/create_PR.bat`
3. ✅ Successfully deleted `tests/test_create_pr.py`
4. ✅ Successfully removed batch wrapper tests from integration tests
5. ⚠️ **Package reinstall required** - Python can't find the new module structure

According to the Step 5 documentation and the error messages, **the user MUST run `pip install -e .` to reinstall the package** after deleting files. This is a critical step that requires user approval.

Let me document this clearly and present the current status:

## Summary of Part A Completion

**✅ Legacy Files Successfully Removed:**
- `workflows/create_PR.py` - **DELETED**
- `workflows/create_PR.bat` - **DELETED**
- `tests/test_create_pr.py` - **DELETED** (legacy test file)

**✅ Test Files Updated:**
- Removed `TestCreatePRBatchWrapper` class from `tests/workflows/test_create_pr_integration.py`
- Updated module docstring to remove batch wrapper reference

**⚠️ CRITICAL NEXT STEP REQUIRED:**

The package **MUST be reinstalled** for the tests to pass. This is because:
1. We deleted files from an installed package
2. Python's module cache still references the old structure
3. The new `mcp_coder.workflows.create_pr` module cannot be found

**Required Action:**
```bash
pip install -e .
```

This command requires approval. Once you approve and run it, the tests should pass.

Would you like me to:
1. **Wait for you to run the reinstall command** and then continue with validation?
2. **Skip to code quality checks** on the files we modified (integration test file)?

Let me know how you'd like to proceed!

---
Generated on: 2025-10-21T22:27:49.963266