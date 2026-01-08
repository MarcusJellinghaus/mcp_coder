# Implementation Task: Implement `ignore_files` parameter in `is_working_directory_clean()` function

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

Current task from TASK_TRACKER.md: Implement `ignore_files` parameter in `is_working_directory_clean()` function

Please implement this task step by step.

## LLM Response:
## Summary

**Step 2 is now complete!** All sub-tasks have been marked as `[x]` in the TASK_TRACKER.md.

### Changes Made:
1. **Implemented `ignore_files` parameter** in `is_working_directory_clean()` at `src/mcp_coder/utils/git_operations/repository.py:187-226`
   - Added optional `list[str] | None` parameter with default `None`
   - Filters out matching filenames from staged, modified, and untracked lists
   - Updated docstring with parameter documentation

2. **Updated 4 caller locations** to pass `ignore_files=["uv.lock"]`:
   - `src/mcp_coder/workflows/create_plan.py:71`
   - `src/mcp_coder/workflows/implement/prerequisites.py:44`
   - `src/mcp_coder/workflows/create_pr/core.py:247` 
   - `src/mcp_coder/workflows/create_pr/core.py:592`

3. **Removed `uv.lock` from `.gitignore`** - now handled by the `ignore_files` parameter

4. **Code checks passed**:
   - Pylint: No issues in modified files
   - Mypy: No type errors in modified files

### Prepared Commit Message:
```
feat(git): Add ignore_files parameter to is_working_directory_clean()

Implement the ignore_files parameter in is_working_directory_clean()
function to filter out specified files from the dirty-check logic.
This allows workflows to ignore auto-generated files like uv.lock.

Changes:
- Add optional ignore_files parameter to is_working_directory_clean()
- Update all 4 callers to pass ignore_files=["uv.lock"]:
  - src/mcp_coder/workflows/create_plan.py
  - src/mcp_coder/workflows/implement/prerequisites.py  
  - src/mcp_coder/workflows/create_pr/core.py (2 locations)
- Remove uv.lock from .gitignore since it's now handled by ignore_files

Fixes #254

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
```

---
Generated on: 2026-01-09T00:42:29.476726