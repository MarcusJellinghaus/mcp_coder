# Implementation Task: Step 6.1: Create `.claude/commands/check_branch_status.md` slash command wrapper

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

Current task from TASK_TRACKER.md: Step 6.1: Create `.claude/commands/check_branch_status.md` slash command wrapper

Please implement this task step by step.

## LLM Response:
Perfect! I have successfully implemented Step 6.1 from the task tracker. Here's what I accomplished:

✅ **Created `.claude/commands/check_branch_status.md` slash command wrapper**

The slash command follows the established patterns from other commands in the `.claude/commands/` directory and includes:

- **Metadata header** with allowed tools and workflow stage
- **Clear usage instructions** with the specific CLI command to execute
- **Comprehensive documentation** of what the command does (CI checks, rebase detection, task validation, GitHub labels, auto-fix capabilities)
- **Output format explanation** optimized for LLM consumption
- **Integration context** showing how it fits into Claude Code workflows

The command will execute `mcp-coder check-branch-status --fix --llm-truncate` when used, providing Claude Code with comprehensive branch status information and automatic fixing capabilities.

Step 6.1 is now complete and marked as `[x]` in the task tracker.

---
Generated on: 2026-01-24T21:59:47.384071