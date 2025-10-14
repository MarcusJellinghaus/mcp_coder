# Implementation Task: Create workflows/validate_labels.py with proper imports and structure

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

Current task from TASK_TRACKER.md: Create workflows/validate_labels.py with proper imports and structure

Please implement this task step by step.

## LLM Response:
## Summary

✅ **Task completed successfully!**

I've implemented the first subtask of Step 2: **Create workflows/validate_labels.py with proper imports and structure**

### What was created:

1. **workflows/validate_labels.py** (workflows/validate_labels.py:1)
   - Module docstring and proper imports
   - STALE_TIMEOUTS constant dict with timeout thresholds
   - parse_arguments() function with --project-dir, --log-level, --dry-run
   - resolve_project_dir() helper function with validation
   - main() function with basic setup (argument parsing, logging, config loading, issue fetching)
   - TODOs left for process_issues() and display_results() (next steps)

2. **tests/workflows/test_validate_labels.py** (tests/workflows/test_validate_labels.py:1)
   - 6 unit tests covering:
     - STALE_TIMEOUTS constant validation
     - Argument parsing with defaults
     - --dry-run flag
     - --project-dir argument
     - --log-level argument
     - All options combined

### Quality checks:
- ✅ **Pylint**: No issues found
- ✅ **Pytest**: All 6 new tests pass
- ✅ **Mypy**: No type errors

### Commit message prepared:
```
feat(workflows): create validate_labels.py script structure

- Add workflows/validate_labels.py with proper imports and module docstring
- Define STALE_TIMEOUTS constant dict for bot_busy label timeouts
- Implement parse_arguments() with --project-dir, --log-level, --dry-run
- Implement main() function with basic setup (parse, logging, config, fetch issues)
- Add tests/workflows/test_validate_labels.py with 6 tests covering argument parsing
- Leave TODOs for process_issues() and display_results() (next steps)
```

**All CLAUDE.md requirements followed**

---
Generated on: 2025-10-14T10:59:47.222231