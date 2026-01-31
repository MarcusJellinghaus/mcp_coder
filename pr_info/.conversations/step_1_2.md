# Implementation Task: Command registered under `mcp-coder gh-tool get-base-branch`

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

Current task from TASK_TRACKER.md: Command registered under `mcp-coder gh-tool get-base-branch`

Please implement this task step by step.

## LLM Response:
I have completed Step 2 of the task tracker. Here's a summary of what was implemented:

## Summary

**Task Completed:** Implement `gh-tool get-base-branch` Command (Step 2)

### Files Created:
- `src/mcp_coder/cli/commands/gh_tool.py` - New module with `execute_get_base_branch` function

### Files Modified:
- `src/mcp_coder/cli/main.py` - Added import, command parser registration, and routing

### Implementation Details:

1. **Command registered** under `mcp-coder gh-tool get-base-branch`

2. **Detection priority** (3-tier):
   - PR base branch (highest priority)
   - Issue's `### Base Branch` section
   - Default branch (main/master)

3. **Exit codes**:
   - 0: Success - branch name printed to stdout
   - 1: Could not detect base branch
   - 2: Error (not a git repo, API failure)

4. **Exit codes documented** in `--help` epilog

5. **Output format**: Branch name only to stdout (clean for shell scripting)

6. **Code patterns**: Uses `resolve_project_dir`, proper logging, follows existing CLI patterns

### Code Quality:
- Pylint: No errors or fatal issues
- Mypy: No type errors in source code

### Commit message written to:
- `pr_info/.commit_message.txt`

---
Generated on: 2026-01-31T18:53:00.281257