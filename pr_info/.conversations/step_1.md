# Implementation Task: Implement slash command `.claude/commands/implementation_finalise.md`

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

Current task from TASK_TRACKER.md: Implement slash command `.claude/commands/implementation_finalise.md`

Please implement this task step by step.

## LLM Response:
## Step 1 Complete

I have completed all sub-tasks for **Step 1: Create Slash Command**:

| Sub-task | Status |
|----------|--------|
| Implement slash command `.claude/commands/implementation_finalise.md` | ✅ |
| Run pylint and fix all issues found | ✅ |
| Run pytest and fix all issues found | ✅ |
| Run mypy and fix all issues found | ✅ |
| Prepare git commit message for Step 1 | ✅ |

### Summary of Changes

1. **Created** `.claude/commands/implementation_finalise.md` - A new slash command that:
   - Reads `pr_info/TASK_TRACKER.md` for unchecked tasks
   - Processes commit message tasks (auto-marks if commits exist)
   - Handles other tasks by checking step files or analysing codebase
   - Runs quality checks only if code changed
   - Writes commit message to `pr_info/.commit_message.txt`
   - Does NOT auto-push (manual mode only)

2. **Updated** `pr_info/TASK_TRACKER.md` - Marked all Step 1 sub-tasks as complete

3. **Created** `pr_info/.commit_message.txt` with the commit message:
   ```
   feat(commands): add implementation_finalise slash command
   ```

The commit message is ready in `pr_info/.commit_message.txt`. As instructed, I did NOT commit the changes.

---
Generated on: 2026-01-19T17:14:35.899128