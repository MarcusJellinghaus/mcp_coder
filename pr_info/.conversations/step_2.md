# Implementation Task: Step 2 implementation: Add mcp_config parameter to build_cli_command and ask_claude_code_cli

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

Current task from TASK_TRACKER.md: Step 2 implementation: Add mcp_config parameter to build_cli_command and ask_claude_code_cli

Please implement this task step by step.

## LLM Response:
Perfect! Now let me prepare the commit message. Let me read the step file to understand what was implemented:

## Summary

**Step 2 Implementation Complete**

I have successfully implemented Step 2: Add mcp_config parameter to build_cli_command and ask_claude_code_cli.

### Changes Made

**File Modified:** `src/mcp_coder/llm/providers/claude/claude_code_cli.py`

1. **Updated `build_cli_command()` function:**
   - Added `mcp_config: str | None = None` parameter
   - Added logic to append `--mcp-config`, config path, and `--strict-mcp-config` flags when mcp_config is provided
   - Updated docstring with parameter description and example

2. **Updated `ask_claude_code_cli()` function:**
   - Added `mcp_config: str | None = None` parameter
   - Passed mcp_config parameter to `build_cli_command()` call
   - Updated docstring with parameter description

### Verification

✅ **All unit tests pass** (5/5 tests in test_claude_mcp_config.py)
✅ **All pytest checks pass** (1126 tests)
✅ **Pylint check passed** (no errors or fatal issues)
✅ **Mypy check passed** (no type errors)

### Commit Message

```
feat(step 2): add mcp_config parameter to Claude CLI command building

Add optional mcp_config parameter to build_cli_command() and ask_claude_code_cli()
functions to support --mcp-config flag in Claude CLI commands. When provided, appends
--mcp-config and --strict-mcp-config flags to the command.

All unit tests pass and code quality checks complete successfully.
```

### Task Tracker Status

✅ Step 2 implementation: Complete
✅ Step 2 quality checks: Complete  
✅ Step 2 commit preparation: Complete

All CLAUDE.md requirements followed:
- Used MCP filesystem tools exclusively for file operations
- Used MCP code-checker tools for all quality checks
- All code quality checks passed (pylint, pytest, mypy)
- Task marked as complete in TASK_TRACKER.md

---
Generated on: 2025-10-30T12:23:34.568764