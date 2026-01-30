# Task Status Tracker

## Instructions for LLM

This tracks **Feature Implementation** for Issue #75: Base Branch Support for Issues.

---

## Tasks

### Step 1: Core Parsing Function `_parse_base_branch()`

- [x] Write unit tests for `_parse_base_branch()` in `tests/utils/github_operations/test_issue_manager.py`
- [x] Implement `_parse_base_branch()` function in `src/mcp_coder/utils/github_operations/issue_manager.py`
- [x] Run pylint and fix any issues found
- [x] Run pytest and fix any failing tests
- [x] Run mypy and fix any type errors
- [x] Prepare git commit message for Step 1

### Step 2: Extend `IssueData` and Populate in `get_issue()` / `list_issues()`

- [x] Add `NotRequired` import and extend `IssueData` TypedDict with `base_branch` field
- [x] Write unit tests for `base_branch` field in `get_issue()` and `list_issues()`
- [x] Modify `get_issue()` to populate `base_branch` from issue body
- [x] Modify `list_issues()` to populate `base_branch` for each issue
- [x] Run pylint and fix any issues found
- [x] Run pytest and fix any failing tests
- [x] Run mypy and fix any type errors
- [x] Prepare git commit message for Step 2

### Step 3: Pass `base_branch` Through `create_plan.py` Workflow

- [x] Write unit tests for `base_branch` parameter in `manage_branch()`
- [x] Update `manage_branch()` signature to accept `base_branch` parameter
- [x] Pass `base_branch` to `create_remote_branch_for_issue()` call
- [x] Update `run_create_plan_workflow()` to extract and pass `base_branch`
- [x] Run pylint and fix any issues found
- [x] Run pytest and fix any failing tests
- [x] Run mypy and fix any type errors
- [x] Prepare git commit message for Step 3

### Step 4: Fix Hardcoded "main" in `pr_manager.py`

- [x] Write unit tests for dynamic default branch resolution in `create_pull_request()`
- [x] Change `base_branch` parameter from `str = "main"` to `Optional[str] = None`
- [x] Add logic to resolve default branch using `get_default_branch_name()` when `base_branch` is None
- [x] Run pylint and fix any issues found
- [x] Run pytest and fix any failing tests
- [x] Run mypy and fix any type errors
- [x] Prepare git commit message for Step 4

### Step 5: Update Slash Commands and Documentation

- [x] Update `.claude/commands/issue_analyse.md` with base branch display guidance
- [x] Update `.claude/commands/issue_create.md` with base branch field documentation
- [x] Update `.claude/commands/issue_update.md` with base branch editing guidance
- [x] Update `docs/repository-setup.md` with base branch feature documentation
- [x] Verify markdown syntax is valid in all modified files
- [x] Run pylint and fix any issues found
- [x] Run pytest and fix any failing tests
- [x] Run mypy and fix any type errors
- [x] Prepare git commit message for Step 5

---

## Pull Request

- [ ] Review all implementation steps are complete
- [ ] Ensure all tests pass (full test suite)
- [ ] Verify no pylint errors remain
- [ ] Verify no mypy type errors remain
- [ ] Prepare PR title and description summarizing the feature
- [ ] Create pull request
