# Implementation Task: Add error handling note to `.claude/commands/plan_approve.md`

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

Current task from TASK_TRACKER.md: Add error handling note to `.claude/commands/plan_approve.md`

Please implement this task step by step.

## LLM Response:
**Step 3 Complete!** 

Here's a summary of what was accomplished:

## Step 3: Update Slash Command Documentation ✅

All sub-tasks completed:
1. ✅ Added error handling note to `.claude/commands/plan_approve.md`
2. ✅ Added error handling note to `.claude/commands/implementation_needs_rework.md`
3. ✅ Added error handling note to `.claude/commands/implementation_approve.md`
4. ✅ Ran quality checks (pylint and mypy passed; pytest has an environment issue unrelated to these doc changes)
5. ✅ Prepared git commit message in `pr_info/.commit_message.txt`

Each file now includes the note:
```markdown
**Note:** If the command fails, report the error to the user. Do not use `--force` unless explicitly asked.
```

This note is placed directly before the `**Effect:**` section in each file, as specified.

---
Generated on: 2026-01-23T07:31:08.209305