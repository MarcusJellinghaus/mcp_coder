# Implementation Task: Add coordinator run subparser in `create_parser()`

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

Current task from TASK_TRACKER.md: Add coordinator run subparser in `create_parser()`

Please implement this task step by step.

## LLM Response:
Perfect! Now let me prepare a git commit message as required by Step 5 of the workflow:

## Commit Message

```
feat(cli): add coordinator run subparser with --all/--repo options

Add coordinator run command to CLI with mutually exclusive --all and --repo arguments.
Updated routing logic in main() to handle the new run subcommand.
Fixed existing test expectations to reflect improved error messages.

Files modified:
- src/mcp_coder/cli/main.py: Added run subparser and routing logic
- tests/cli/test_main.py: Updated error message expectations

All code quality checks pass (pylint, pytest, mypy).
```

This is a concise commit message that describes what was done. The task is now complete!

## Summary

I have successfully completed the task "Add coordinator run subparser in `create_parser()`". Here's what was accomplished:

### What was implemented:
1. ✅ **Added coordinator run subparser** in `create_parser()` with help text "Monitor and dispatch workflows for GitHub issues"
2. ✅ **Added mutually exclusive group** for `--all` and `--repo` options (one required)
3. ✅ **Updated routing logic** in `main()` function to handle the "run" subcommand and route to `execute_coordinator_run()`
4. ✅ **Fixed existing test** that broke due to improved error message (now mentions both 'test' and 'run' examples)

### Code quality verification:
- ✅ **Pylint**: No issues found
- ✅ **Pytest**: All 1106 tests pass (fast unit tests)
- ✅ **Mypy**: No type errors found

### Files modified:
- `src/mcp_coder/cli/main.py` - Added run subparser in lines 246-263, updated routing logic in lines 321-339
- `tests/cli/test_main.py` - Updated test expectation on line 374

### Prepared commit message:
```
feat(cli): add coordinator run subparser with --all/--repo options
```

All CLAUDE.md requirements have been followed - MCP tools were used exclusively for all operations.

---
Generated on: 2025-10-28T14:28:54.603020