# MCP Coder Task Tracker

## Overview

This tracks **Feature Implementation** consisting of multiple **Implementation Steps**.

- **Feature**: A complete user-facing capability
- **Implementation Step**: A self-contained unit of work (tests + implementation)

## Status Legend

- [x] = Implementation step complete
- [ ] = Implementation step not complete
- Each task links to a detail file in pr_info/steps/ folder

---

## Tasks

### Step 1: Update base_manager.py to Use git_operations Abstraction
See: [pr_info/steps/step_1.md](steps/step_1.md)

- [x] Remove `import git` and add `from mcp_coder.utils import git_operations`
- [x] Remove `self._repo` attribute and all related assignments
- [x] Update `_init_with_project_dir()` to use `git_operations.is_git_repository()`
- [x] Update `_get_repository()` to use `git_operations.get_github_repository_url()`
- [x] Run quality checks: pylint, pytest, mypy - fix all issues
- [x] Prepare git commit message for Step 1

### Step 2: Update Tests to Mock git_operations Instead of git.Repo
See: [pr_info/steps/step_2.md](steps/step_2.md)

- [ ] Remove `import git` from test file
- [ ] Update `test_successful_initialization_with_project_dir` - mock `is_git_repository`
- [ ] Update `test_initialization_fails_not_git_repository` - mock `is_git_repository` returns False
- [ ] Update `test_initialization_fails_no_github_token` - mock `is_git_repository`
- [ ] Update `test_get_repository_with_project_dir_mode` - mock both functions
- [ ] Update `test_get_repository_caching` - mock both functions
- [ ] Update `test_get_repository_no_origin_remote` - mock `get_github_repository_url` returns None
- [ ] Update `test_get_repository_invalid_github_url` - mock `get_github_repository_url` returns GitLab URL
- [ ] Update `test_get_repository_github_api_error` - mock both functions
- [ ] Update `test_get_repository_generic_exception` - mock both functions
- [ ] Update `test_ssh_url_format_parsing` - mock both functions
- [ ] Update `test_https_url_without_git_extension` - mock both functions
- [ ] Run quality checks: pylint, pytest, mypy - fix all issues
- [ ] Prepare git commit message for Step 2

### Step 3: Update .importlinter and Verify
See: [pr_info/steps/step_3.md](steps/step_3.md)

- [ ] Remove exception rule for `base_manager -> git` from `.importlinter`
- [ ] Remove associated TODO and comment lines
- [ ] Run `lint-imports` to verify GitPython Library Isolation contract passes
- [ ] Run quality checks: pylint, pytest, mypy - fix all issues
- [ ] Prepare git commit message for Step 3

---

## Acceptance Criteria Verification

- [ ] `base_manager.py` has no `import git` statement
- [ ] `base_manager.py` uses `from mcp_coder.utils import git_operations`
- [ ] `base_manager.py` has no `self._repo` attribute
- [ ] `test_base_manager.py` has no `import git` statement
- [ ] `test_base_manager.py` mocks `git_operations` functions
- [ ] `.importlinter` has no exception for `base_manager -> git`
- [ ] `lint-imports` passes
- [ ] All tests pass
- [ ] Error message `"Directory is not a git repository: {project_dir}"` preserved

---

## Pull Request

- [ ] Review all implementation steps are complete
- [ ] Verify all quality checks pass (pylint, pytest, mypy)
- [ ] Verify lint-imports passes
- [ ] Create PR summary with changes overview
- [ ] Prepare final PR description
