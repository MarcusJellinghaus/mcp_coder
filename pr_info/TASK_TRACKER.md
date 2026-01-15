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

### Step 1: Add `rebase_onto_branch()` Function and `force_with_lease` Parameter with Tests

See: [pr_info/steps/step_1.md](steps/step_1.md)

- [x] Add test class `TestGitPushForceWithLease` to `tests/utils/git_operations/test_remotes.py`
- [x] Modify `git_push()` in `src/mcp_coder/utils/git_operations/remotes.py` to add `force_with_lease` parameter
- [x] Add test class `TestRebaseOntoBranch` to `tests/utils/git_operations/test_branches.py`
- [x] Add function `rebase_onto_branch()` to `src/mcp_coder/utils/git_operations/branches.py`
- [x] Add export `rebase_onto_branch` to `src/mcp_coder/utils/git_operations/__init__.py`
- [x] Run quality checks (pylint, pytest, mypy) and fix all issues
- [x] Prepare git commit message for Step 1

### Step 2: Add Parent Branch Detection and Workflow Integration with Tests

See: [pr_info/steps/step_2.md](steps/step_2.md)

- [x] Add test class `TestGetRebaseTargetBranch` to `tests/workflows/implement/test_core.py`
- [x] Add test class `TestRebaseIntegration` to `tests/workflows/implement/test_core.py`
- [x] Add private function `_get_rebase_target_branch()` to `src/mcp_coder/workflows/implement/core.py`
- [ ] Add helper function `_attempt_rebase()` to `src/mcp_coder/workflows/implement/core.py`
- [ ] Integrate rebase step into `run_implement_workflow()` in `src/mcp_coder/workflows/implement/core.py`
- [ ] Modify `push_changes()` in `src/mcp_coder/workflows/implement/task_processing.py` to accept `force_with_lease` parameter
- [ ] Run quality checks (pylint, pytest, mypy) and fix all issues
- [ ] Prepare git commit message for Step 2

---

## Pull Request

- [ ] Review all implementation steps for completeness
- [ ] Run final quality checks (pylint, pytest, mypy) on entire codebase
- [ ] Prepare PR summary and description
