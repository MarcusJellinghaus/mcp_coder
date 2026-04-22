# Task Status Tracker

## Instructions for LLM

This tracks **Feature Implementation** consisting of multiple **Tasks**.

**Summary:** See [summary.md](./steps/summary.md) for implementation overview.

**How to update tasks:**
1. Change [ ] to [x] when implementation step is fully complete (code + checks pass)
2. Change [x] to [ ] if task needs to be reopened
3. Add brief notes in the linked detail files if needed
4. Keep it simple - just GitHub-style checkboxes

**Task format:**
- [x] = Task complete (code + all checks pass)
- [ ] = Task not complete
- Each task links to a detail file in steps/ folder

---

## Tasks

### Step 1: Refactor `failure_handling.py` — replace GitPython with subprocess
- [x] Implementation: replace `_safe_repo_context` with `execute_command` in `get_diff_stat()`, update tests
- [x] Quality checks pass: pylint, pytest, mypy — fix all issues
- [x] Commit: `refactor: replace GitPython with subprocess in get_diff_stat (#886)`

### Step 2: Flip shim imports to `mcp_workspace.git_operations`
- [x] Implementation: change all imports in `mcp_workspace_git.py` from local to external package, drop `_safe_repo_context`, update smoke test (29→28)
- [x] Quality checks pass: pylint, pytest, mypy — fix all issues
- [x] Commit: `refactor: flip git shim to mcp_workspace.git_operations (#886)`

### Step 3: Fix 5 bypass files to import through shim
- [x] Implementation: reroute imports in `git_utils.py`, `base_manager.py`, `ci_results_manager.py`, `pr_manager.py`, `issues/manager.py`
- [x] Quality checks pass: pylint, pytest, mypy — fix all issues
- [x] Commit: `refactor: route git imports through shim in 5 bypass files (#886)`

### Step 4: Delete local `git_operations` + cleanup configs
- [x] Implementation: edit `.importlinter` and `vulture_whitelist.py`, delete `src/mcp_coder/utils/git_operations/` and `tests/utils/git_operations/`
- [x] Quality checks pass: pylint, pytest, mypy, lint-imports — fix all issues
- [x] Commit: `refactor: delete local git_operations and clean up configs (#886)`

## Pull Request
- [ ] PR review: verify all steps merged cleanly, no regressions
- [ ] PR summary prepared
