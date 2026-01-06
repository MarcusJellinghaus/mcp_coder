# Implementation Task: Create `coordinator/command_templates.py` with all template strings

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

Current task from TASK_TRACKER.md: Create `coordinator/command_templates.py` with all template strings

Please implement this task step by step.

## LLM Response:
I have completed the first sub-task of Step 6. Here's a summary:

## Completed: Create `coordinator/command_templates.py` with all template strings

**File created:** `src/mcp_coder/cli/commands/coordinator/command_templates.py`

**Contents include all template constants:**

| Constant | Description |
|----------|-------------|
| `DEFAULT_TEST_COMMAND` | Linux test command template |
| `DEFAULT_TEST_COMMAND_WINDOWS` | Windows test command template |
| `TEST_COMMAND_TEMPLATES` | Dict mapping OS to test template |
| `CREATE_PLAN_COMMAND_TEMPLATE` | Linux create-plan workflow |
| `IMPLEMENT_COMMAND_TEMPLATE` | Linux implement workflow |
| `CREATE_PR_COMMAND_TEMPLATE` | Linux create-pr workflow |
| `CREATE_PLAN_COMMAND_WINDOWS` | Windows create-plan workflow |
| `IMPLEMENT_COMMAND_WINDOWS` | Windows implement workflow |
| `CREATE_PR_COMMAND_WINDOWS` | Windows create-pr workflow |
| `PRIORITY_ORDER` | Issue processing priority list |

**Quality checks passed:**
- Pylint: No issues in new file
- Mypy: No type errors

The file is ready for the next sub-tasks which will update `commands.py` and `core.py` to import from this new module instead of defining templates locally.

---
Generated on: 2026-01-06T23:40:38.989343