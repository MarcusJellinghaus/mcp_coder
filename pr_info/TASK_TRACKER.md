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

### Step 0: Pre-flight check — verify mcp_workspace.git_operations exists
- [x] Implementation: verify `mcp_workspace.git_operations` package in `p_workspace` reference project; create `pr_info/error.md` if missing
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 1: Create shim module + smoke test
- [x] Implementation: create `src/mcp_coder/mcp_workspace_git.py` (28 symbols + 1 constant) and `tests/test_mcp_workspace_git_smoke.py`
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 2: Update all source consumers to use shim
- [ ] Implementation: switch all `src/` imports from `mcp_coder.utils.git_operations` to `mcp_coder.mcp_workspace_git`; update `utils/__init__.py` (remove dead symbols, source from shim); update root `__init__.py`
- [ ] Implementation: update test `@patch` targets that break from source changes (`test_module_integration.py`, `test_base_manager.py`, `test_ci_results_manager_foundation.py`, `test_issue_branch_manager.py`, `issues/conftest.py`, `test_issue_manager_label_update.py`)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 3: Update remaining test consumers + delete old git_operations tests
- [ ] Implementation: update remaining test imports (`test_git_encoding_stress.py`, `test_check_branch_status_pr_waiting.py`, `test_create_pr_integration.py`, `test_github_integration_smoke.py`, `test_github_utils.py`, `cli/test_utils.py`, `test_git_tool.py`)
- [ ] Implementation: delete `tests/utils/git_operations/` directory (14 files)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 4: Delete local git_operations package
- [ ] Implementation: delete `src/mcp_coder/utils/git_operations/` directory (13 files); grep-verify no remaining references
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 5: Update architecture configs
- [ ] Implementation: update `.importlinter` — remove `git_local` and `git_operations_internal_layering` contracts, add `mcp_workspace_git_isolation`, update `git_library_isolation` and `jenkins_independence`, update layered architecture
- [ ] Implementation: update `tach.toml` — add `shim_workspace` layer, move `mcp_tools_py`, add `mcp_workspace_git`, update dependants
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

## Pull Request
- [ ] PR review: verify all steps complete, all checks green
- [ ] PR summary prepared
