# Implementation Task: Implement count_lines() function

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

Current task from TASK_TRACKER.md: Implement count_lines() function

Please implement this task step by step.

## LLM Response:
I have completed the task. Here's a summary of what was done:

## Task Completed: Implement count_lines() function

**Sub-task:** `- [x] Implement count_lines() function`

### Changes Made:

**File:** `src/mcp_coder/checks/file_sizes.py`

Implemented the `count_lines()` function with the following logic:
```python
def count_lines(file_path: Path) -> int:
    try:
        with file_path.open(encoding="utf-8") as f:
            return sum(1 for _ in f)
    except UnicodeDecodeError:
        return -1
```

**Implementation follows the specification:**
1. Opens file with UTF-8 encoding
2. Counts lines using `sum(1 for _ in f)` - memory efficient generator
3. Returns -1 for binary/non-UTF-8 files (catches `UnicodeDecodeError`)
4. Other exceptions are re-raised (default Python behavior)

**Task tracker updated:** `pr_info/TASK_TRACKER.md` - marked sub-task complete

**Commit message written:** `pr_info/.commit_message.txt`

---
Generated on: 2026-01-28T16:31:18.459625