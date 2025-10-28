# Implementation Task: Write test: `test_coordinator_run_requires_all_or_repo()`

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

Current task from TASK_TRACKER.md: Write test: `test_coordinator_run_requires_all_or_repo()`

Please implement this task step by step.

## LLM Response:
## Summary

I've successfully implemented the task: **Write test: `test_coordinator_run_requires_all_or_repo()`**

### What was done:

1. ✅ **Added test in tests/cli/test_main.py:470-471** - The test `test_coordinator_run_requires_all_or_repo()` verifies that argparse raises a `SystemExit` error when neither `--all` nor `--repo` is provided to the `coordinator run` command.

2. ✅ **All code quality checks passed:**
   - **Pytest**: All 1110 tests pass (including the new test)
   - **Pylint**: No issues found
   - **Mypy**: No type errors found

3. ✅ **Task marked complete in TASK_TRACKER.md** - Updated the checkbox from `[ ]` to `[x]`

### Test implementation:
```python
def test_coordinator_run_requires_all_or_repo(self) -> None:
    """Test error when neither --all nor --repo provided."""
    parser = create_parser()

    # Should raise SystemExit when neither --all nor --repo is provided
    with pytest.raises(SystemExit):
        parser.parse_args(["coordinator", "run"])
```

The test validates that the mutually exclusive group with `required=True` properly enforces that at least one of `--all` or `--repo` must be provided when running the `coordinator run` command.

All CLAUDE.md requirements followed.

---
Generated on: 2025-10-28T14:55:53.151563