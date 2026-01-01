# Implementation Task: Run pylint on coordinator.py and fix all issues

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

Current task from TASK_TRACKER.md: Run pylint on coordinator.py and fix all issues

Please implement this task step by step.

## LLM Response:
Perfect! I have successfully completed the task. Here's a summary of what was accomplished:

## Task Completed: Run pylint on coordinator.py and fix all issues

**Issues Found and Fixed:**

1. **R0917 (too-many-positional-arguments)**: The `dispatch_workflow` function had 7 positional arguments, but pylint allows only 5 by default.
   - **Fix**: Refactored the function signature to use keyword-only arguments after the 4th parameter by adding `*,` which forces the last 3 parameters to be keyword-only arguments.

2. **W0718 (broad exception handling)**: Multiple instances of catching `Exception` which is too general.
   - **Fix**: Replaced all broad `except Exception as e:` clauses with more specific exception types:
     - Cache-related exceptions: `(ValueError, KeyError, TypeError)`
     - Jenkins/network-related exceptions: `(ConnectionError, TimeoutError, ValueError)`
     - Workflow dispatch exceptions: `(ValueError, ConnectionError, TimeoutError, RuntimeError)`
     - General error handling: `(ConnectionError, TimeoutError, RuntimeError)`

**All pylint issues in coordinator.py have been resolved.** The remaining W0718 issues shown in the final pylint output are in other files (commit.py, create_plan.py, create_pr.py, implement.py, prompt.py) which are outside the scope of this specific task.

The task tracker has been updated to mark "Run pylint on coordinator.py and fix all issues" as complete ✅.

---
Generated on: 2026-01-01T20:03:14.409876