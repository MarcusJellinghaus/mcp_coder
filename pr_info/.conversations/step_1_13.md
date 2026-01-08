# Implementation Task: Verify `resolve_project_dir` raises `ValueError` (not `sys.exit`)

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

Current task from TASK_TRACKER.md: Verify `resolve_project_dir` raises `ValueError` (not `sys.exit`)

Please implement this task step by step.

## LLM Response:
## Task Completed ✓

**Sub-task:** Verify `resolve_project_dir` raises `ValueError` (not `sys.exit`)

**Verification Results:**

| Check | Status |
|-------|--------|
| No `sys.exit` in `resolve_project_dir` | ✅ Verified |
| Function raises `ValueError` for all error conditions | ✅ Verified |
| Tests expect `ValueError` | ✅ Verified in both test files |
| Callers have try/except wrapper | ✅ Verified (`validate_labels.py`) |

The sub-task has been marked complete in `pr_info/TASK_TRACKER.md`. The next unchecked sub-task in Step 5 is:
- `Verify apply_labels raises RuntimeError on API errors`

---
Generated on: 2026-01-08T23:50:27.759884