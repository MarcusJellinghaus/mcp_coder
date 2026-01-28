# Implementation Task: Update src/mcp_coder/cli/main.py with check command group

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

Current task from TASK_TRACKER.md: Update src/mcp_coder/cli/main.py with check command group

Please implement this task step by step.

## LLM Response:
I have completed the sub-task. Here's a summary of what was done:

## Completed: Update src/mcp_coder/cli/main.py with check command group

### Changes made to `src/mcp_coder/cli/main.py`:

1. **Added import** (line 9):
   ```python
   from .commands.check_file_sizes import execute_check_file_sizes
   ```

2. **Added check command group** (lines 404-440):
   - Created `check` parser with subparsers
   - Added `file-size` subcommand with arguments:
     - `--max-lines` (default: 600)
     - `--allowlist-file` (default: `.large-files-allowlist`)
     - `--generate-allowlist` (flag)
     - `--project-dir` (optional)

3. **Added command routing** (lines 519-530):
   - Routes `check file-size` to `execute_check_file_sizes(args)`
   - Handles missing/unknown subcommands with appropriate error messages

### Verification:
- ✅ Mypy type checking passed
- ✅ Pylint shows no new errors (existing warnings in other files)
- ✅ Task tracker updated
- ✅ Commit message written to `pr_info/.commit_message.txt`

---
Generated on: 2026-01-28T17:02:13.826695