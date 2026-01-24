# Implementation Task: Step 1.2: Implement `needs_rebase()` function in `src/mcp_coder/utils/git_operations/branches.py`

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

Current task from TASK_TRACKER.md: Step 1.2: Implement `needs_rebase()` function in `src/mcp_coder/utils/git_operations/branches.py`

Please implement this task step by step.

## LLM Response:
## Summary

I have successfully implemented **Step 1.2: Implement `needs_rebase()` function** in `src/mcp_coder/utils/git_operations/branches.py`. 

### What was implemented:

1. **Function Signature**: `needs_rebase(project_dir: Path, target_branch: Optional[str] = None) -> Tuple[bool, str]`

2. **Key Features**:
   - Detects if current branch needs rebasing onto target branch using `git merge-base`
   - Auto-detects target branch using `get_default_branch_name()` if not provided
   - Returns tuple with (needs_rebase: bool, reason: str)
   - Comprehensive error handling with descriptive messages

3. **Integration**:
   - Follows existing code patterns in the file
   - Uses existing utilities: `is_git_repository`, `get_current_branch_name`, `get_default_branch_name`, `fetch_remote`
   - Proper logging and error handling consistent with other functions
   - Uses `_safe_repo_context` for GitPython operations

4. **Algorithm**:
   - Validates git repository and fetches from remote
   - Gets current branch and determines target branch
   - Uses `git merge-base --is-ancestor` to check if up-to-date
   - Counts commits behind using `git rev-list --count` if rebase needed

5. **Quality Checks**:
   - ✅ mypy type checking passed
   - ✅ pylint code quality passed
   - ✅ Tests already exist in test file

The implementation matches the specification in `pr_info/steps/step_1.md` and is ready for the next step (Step 1.3: quality checks).

---
Generated on: 2026-01-24T20:44:53.112918