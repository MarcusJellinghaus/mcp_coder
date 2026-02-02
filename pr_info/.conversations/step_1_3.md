# Implementation Task: Add vscodeclaude object to `status-07:code-review` label in labels.json

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

Current task from TASK_TRACKER.md: Add vscodeclaude object to `status-07:code-review` label in labels.json

Please implement this task step by step.

## LLM Response:
I'll start by reading the task tracker to understand the current task and its context.I can see the current task is: **Add vscodeclaude object to `status-07:code-review` label in labels.json**

This is part of Step 1. Let me read the step details to understand the exact implementation needed.Now let me read the current labels.json to see the existing structure and what's already been added.I can see the current state:
- `status-01:created` has vscodeclaude ✓
- `status-04:plan-review` has vscodeclaude ✓
- `status-07:code-review` does NOT have vscodeclaude yet - this is my task
- `status-10:pr-created` does NOT have vscodeclaude yet

According to the step_1.md table, for `status-07:code-review` I need to add:
- emoji: 🔍
- display_name: CODE REVIEW
- stage_short: review
- initial_command: /implementation_review
- followup_command: /discuss

Let me add the vscodeclaude object to `status-07:code-review`:The edit was successful. Now let me verify the JSON is valid by reading the file:The JSON is valid. The `status-07:code-review` label now has the vscodeclaude object with all required fields:
- emoji: 🔍
- display_name: CODE REVIEW
- stage_short: review
- initial_command: /implementation_review
- followup_command: /discuss

Now I need to mark this sub-task as complete in the TASK_TRACKER.md:Task completed successfully.

## Summary

**Completed:** Add vscodeclaude object to `status-07:code-review` label in labels.json

**Changes made:**
- Added `vscodeclaude` object to `status-07:code-review` in `src/mcp_coder/config/labels.json` with:
  - emoji: 🔍
  - display_name: CODE REVIEW
  - stage_short: review
  - initial_command: /implementation_review
  - followup_command: /discuss

**Status:** Sub-task marked as `[x]` in TASK_TRACKER.md

**Next sub-task:** Add vscodeclaude object to `status-10:pr-created` label in labels.json (with null commands)

---
Generated on: 2026-02-02T09:36:15.421856