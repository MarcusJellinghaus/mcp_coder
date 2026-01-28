# Implementation Task: Implement get_file_metrics() function

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

Current task from TASK_TRACKER.md: Implement get_file_metrics() function

Please implement this task step by step.

## LLM Response:
I have completed the task. Here's a summary of what was done:

## Task Completed: Implement get_file_metrics() function

**What I implemented:**
- The `get_file_metrics()` function in `src/mcp_coder/checks/file_sizes.py:69-79`
- Takes a list of relative file paths and a project directory
- For each file: calculates the absolute path, counts lines using `count_lines()`
- Excludes binary files (those with line count -1)
- Returns a list of `FileMetrics` objects

**Implementation:**
```python
def get_file_metrics(files: list[Path], project_dir: Path) -> list[FileMetrics]:
    result: list[FileMetrics] = []
    for file_path in files:
        absolute_path = project_dir / file_path
        line_count = count_lines(absolute_path)
        if line_count >= 0:
            result.append(FileMetrics(path=file_path, line_count=line_count))
    return result
```

**Verification:**
- Mypy check: ✅ No type errors
- Pylint check: ✅ No issues

**Updated:**
- Marked task `[x]` in `pr_info/TASK_TRACKER.md`
- Wrote commit message to `pr_info/.commit_message.txt`

---
Generated on: 2026-01-28T16:42:31.246245