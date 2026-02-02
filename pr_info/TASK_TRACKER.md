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

### Step 1: Add Git Merge-Base Detection to `base_branch.py`
See [step_1.md](./steps/step_1.md) for details.

- [x] Add `MERGE_BASE_DISTANCE_THRESHOLD = 20` constant with comment
- [x] Implement `_detect_from_git_merge_base()` function
- [x] Update `detect_base_branch()` to call merge-base as priority 1
- [x] Change `detect_base_branch()` return type to `Optional[str]`
- [x] Return `None` instead of `"unknown"` on failure
- [x] Add DEBUG logging for detection steps
- [x] Add new tests for merge-base detection
- [x] Update existing tests for `None` return value
- [x] Run quality checks (pylint, pytest, mypy) and fix all issues
- [x] Prepare git commit message for Step 1

### Step 2: Remove `get_parent_branch_name()` and Update Exports
See [step_2.md](./steps/step_2.md) for details.

- [x] Remove `get_parent_branch_name()` function from `readers.py`
- [x] Remove re-export from `git_operations/__init__.py`
- [x] Remove re-export from `utils/__init__.py`
- [x] Remove test from `test_readers.py`
- [x] Verify `grep -r "get_parent_branch_name" src/` returns no results
  - Note: Function removed from readers.py and exports. Consumers in diffs.py/core.py remain (fixed in Steps 3-4)
- [ ] Run quality checks (pylint, pytest, mypy) and fix all issues *(blocked - see note)*
- [ ] Prepare git commit message for Step 2 *(blocked - see note)*

**Note:** Quality checks blocked until Steps 3-4 complete. Current failures:
- `diffs.py:12` - broken import (Step 3)
- `core.py:17` - broken import (Step 4)
- `test_create_pr_integration.py:65` - broken import (Step 4)

### Step 3: Update `diffs.py` - Remove Auto-Detection
See [step_3.md](./steps/step_3.md) for details.

- [ ] Remove `get_parent_branch_name` import from `diffs.py`
- [ ] Remove auto-detection logic from `get_branch_diff()`
- [ ] Return empty string with error log when `base_branch` is `None`
- [ ] Update docstring to document new behavior
- [ ] Update tests to reflect explicit `base_branch` requirement
- [ ] Run quality checks (pylint, pytest, mypy) and fix all issues
- [ ] Prepare git commit message for Step 3

### Step 4: Update `create_pr/core.py` to Use `detect_base_branch()`
See [step_4.md](./steps/step_4.md) for details.

- [ ] Remove `get_parent_branch_name` import from `core.py`
- [ ] Add `detect_base_branch` import from `workflow_utils.base_branch`
- [ ] Update `check_prerequisites()` to use `detect_base_branch()` with `None` handling
- [ ] Update `create_pull_request()` to use `detect_base_branch()` with `None` handling
- [ ] Update `generate_pr_summary()` to pass explicit `base_branch` to `get_branch_diff()`
- [ ] Add helpful tip in error messages about `### Base Branch` section
- [ ] Change variable names from `parent_branch` to `base_branch`
- [ ] Update all test mocks in `test_prerequisites.py` and `test_workflow.py`
- [ ] Run quality checks (pylint, pytest, mypy) and fix all issues
- [ ] Prepare git commit message for Step 4

### Step 5: Update `implement/core.py` for `None` Handling
See [step_5.md](./steps/step_5.md) for details.

- [ ] Update `_get_rebase_target_branch()` to remove `"unknown"` check
- [ ] Simplify function to return `detect_base_branch()` result directly
- [ ] Update any tests mocking `"unknown"` return to mock `None`
- [ ] Verify rebase workflow works correctly with `None` handling
- [ ] Run quality checks (pylint, pytest, mypy) and fix all issues
- [ ] Prepare git commit message for Step 5

---

## Pull Request

- [ ] Review all implementation steps are complete
- [ ] Run full test suite to verify all tests pass
- [ ] Run full quality checks (pylint, pytest, mypy) on entire codebase
- [ ] Verify no regressions in existing functionality
- [ ] Prepare PR title and description summarizing all changes
- [ ] Create Pull Request
