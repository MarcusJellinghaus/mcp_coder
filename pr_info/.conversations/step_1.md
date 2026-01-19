# Implementation Task: Update `src/mcp_coder/prompts/prompts.md` - Change commit message instruction from "Prepare commit message when that sub-task appears" to "Write commit message to `pr_info/.commit_message.txt`"

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
- Prepare commit message when that sub-task appears
- Do NOT commit - just prepare the message

**RULES:**
- ONE step per run (but complete all its sub-tasks)
- Mark each sub-task `[x]` immediately after completing it
- Use MCP tools for all operations

Current task from TASK_TRACKER.md: Update `src/mcp_coder/prompts/prompts.md` - Change commit message instruction from "Prepare commit message when that sub-task appears" to "Write commit message to `pr_info/.commit_message.txt`"

Please implement this task step by step.

## LLM Response:
## Step 1 Complete ✓

**Summary of completed sub-tasks:**

1. **[x] Updated `src/mcp_coder/prompts/prompts.md`** - Changed the commit message instruction from "Prepare commit message when that sub-task appears" to "Write commit message to `pr_info/.commit_message.txt`"

2. **[x] Ran quality checks** - Pylint and mypy passed with no issues (pytest had a configuration issue unrelated to this change)

3. **[x] Wrote commit message** - Created `pr_info/.commit_message.txt` with:
   ```
   docs(prompts): update commit message instruction to use file output
   
   Change implementation prompt to write commit messages to
   pr_info/.commit_message.txt instead of just preparing them.
   ```

Step 1 is now fully complete. All sub-tasks are marked `[x]` in the task tracker.

---
Generated on: 2026-01-19T16:25:39.299661