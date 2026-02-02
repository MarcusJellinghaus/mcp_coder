# Implementation Task: Add DEFAULT_PROMPT_TIMEOUT constant to types.py

## Prompt Sent to LLM:
Implement ONE step from the task tracker.

**1. SELECT STEP**
- Read `pr_info/TASK_TRACKER.md`
- Find the first Step with unchecked sub-tasks (`- [ ]`)
- Work through ALL sub-tasks in that step sequentially
- Announce which task you're working on

**2. FOR EACH SUB-TASK**
- Read linked files in `pr_info/steps/` if referenced
- Implement only what's described
- Run code checks (pylint, pytest, mypy) when required
- Fix all issues before proceeding
- Mark sub-task complete: `- [ ]` → `- [x]`

**3. COMPLETE THE STEP**
- All sub-tasks must be `[x]` before finishing
- Write commit message to `pr_info/.commit_message.txt`
- Do NOT commit - just write the message to the file

**RULES:**
- ONE step per run (but complete all its sub-tasks)
- Mark each sub-task `[x]` immediately after completing it
- Use MCP tools for all operations

Current task from TASK_TRACKER.md: Add DEFAULT_PROMPT_TIMEOUT constant to types.py

Please implement this task step by step.

## LLM Response:
I have completed **Step 16: Update Workspace Setup for V2 Templates**. Here's a summary of what was implemented:

## Completed Tasks

1. **Added `DEFAULT_PROMPT_TIMEOUT` constant to types.py** - Set to 300 seconds (5 minutes) for mcp-coder prompt timeouts

2. **Updated `create_startup_script()` to use V2 templates** - The function now uses:
   - `VENV_SECTION_WINDOWS` for virtual environment setup
   - `AUTOMATED_SECTION_WINDOWS_V2` for mcp-coder prompt with session-id output
   - `DISCUSSION_SECTION_WINDOWS` for /discuss with session resume
   - `INTERACTIVE_SECTION_WINDOWS_V2` for claude --resume
   - `INTERVENTION_SCRIPT_WINDOWS_V2` for intervention mode

3. **Added timeout parameter to `create_startup_script()`** - With default value `DEFAULT_PROMPT_TIMEOUT`

4. **Updated callers in orchestrator.py** - Both `prepare_and_launch_session()` and `regenerate_session_files()` now explicitly pass `timeout=DEFAULT_PROMPT_TIMEOUT`

5. **Added tests for V2 script generation** - New `TestCreateStartupScriptV2` class with tests for:
   - Venv section inclusion
   - mcp-coder prompt usage
   - Claude resume command
   - Custom timeout handling
   - Intervention mode behavior
   - Correct initial command for status
   - Discussion section inclusion

6. **Fixed mypy unreachable code error** - Restructured the function to avoid unreachable code after `NotImplementedError` for Linux

7. **Prepared commit message** - Written to `pr_info/.commit_message.txt`

All sub-tasks for Step 16 are now marked complete in the task tracker.

---
Generated on: 2026-01-30T14:59:21.901392