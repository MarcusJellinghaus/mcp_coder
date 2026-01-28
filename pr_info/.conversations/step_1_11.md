# Implementation Task: Implement check_file_sizes() function

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

Current task from TASK_TRACKER.md: Implement check_file_sizes() function

Please implement this task step by step.

## LLM Response:
## Summary

I have completed the task **"Implement check_file_sizes() function"**:

### What was done:
1. **Implemented `check_file_sizes()` function** in `src/mcp_coder/checks/file_sizes.py`:
   - Gets all project files using `list_files()` from the mcp_server_filesystem wrapper
   - Collects line count metrics via `get_file_metrics()`
   - Identifies files exceeding the `max_lines` threshold
   - Filters out allowlisted files from violations
   - Detects stale allowlist entries (non-existent files or files now under limit)
   - Returns violations sorted by line count (descending)

2. **Added the required import** for `list_files` from `mcp_coder.mcp_server_filesystem`

3. **Verified code quality**:
   - ✅ Mypy type checking passes
   - ✅ Pylint passes with no issues

4. **Updated TASK_TRACKER.md**: Marked `- [x] Implement check_file_sizes() function`

5. **Wrote commit message** to `pr_info/.commit_message.txt`

### Next sub-task in Step 2:
`- [ ] Write tests for render_output() function`

---
Generated on: 2026-01-28T16:49:07.601432