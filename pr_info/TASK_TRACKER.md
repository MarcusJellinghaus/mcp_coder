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

<!-- Tasks populated from pr_info/steps/ by prepare_task_tracker -->

### Step 1: Move source file and update test ([step_1.md](./steps/step_1.md))

- [x] Copy `src/mcp_coder/workflow_utils/branch_status.py` to `src/mcp_coder/checks/branch_status.py` (no code changes)
- [x] Copy `tests/workflow_utils/test_branch_status.py` to `tests/checks/test_branch_status.py` and update all imports (`workflow_utils.branch_status` → `checks.branch_status`)
- [x] Delete `src/mcp_coder/workflow_utils/branch_status.py`
- [x] Delete `tests/workflow_utils/test_branch_status.py`
- [x] Run pylint on changed files and fix all issues found
- [x] Run pytest `tests/checks/test_branch_status.py` and confirm all tests pass
- [x] Run mypy on changed files and fix all issues found
- [x] Prepare git commit message for Step 1

### Step 2: Update all callers and remove old exports ([step_2.md](./steps/step_2.md))

- [x] Remove `from .branch_status import (...)` block from `src/mcp_coder/workflow_utils/__init__.py` and remove all branch_status symbols from `__all__`
- [x] Update import in `src/mcp_coder/cli/commands/check_branch_status.py` (`workflow_utils.branch_status` → `checks.branch_status`)
- [x] Update import in `src/mcp_coder/workflows/implement/core.py` (`workflow_utils.branch_status` → `checks.branch_status`)
- [x] Update import in `tests/cli/commands/test_check_branch_status.py` (`workflow_utils.branch_status` → `checks.branch_status`)
- [x] Run pylint on changed files and fix all issues found
- [x] Run full pytest suite (excluding integration markers) and confirm all tests pass
- [x] Run mypy on changed files and fix all issues found
- [x] Prepare git commit message for Step 2

### Step 3: Verify architectural boundary tools ([step_3.md](./steps/step_3.md))

- [x] Update `tach.toml`: add `"tools"` to layers list, add `[[modules]]` entry for `mcp_coder.checks` at `tools` layer, add `mcp_coder.checks` to `depends_on` for `cli`, `workflows`, and `tests`
- [x] Update `.importlinter`: insert `mcp_coder.checks` as new layer between `mcp_coder.workflows` and `mcp_coder.workflow_utils`, and add `tests.checks` to the `test_module_independence` contract
- [x] Run `tach check` and confirm no violations
- [x] Run `lint-imports` and confirm no violations
- [x] Run pylint on changed files and fix all issues found
- [x] Run full pytest suite (excluding integration markers) and confirm all tests pass
- [x] Run mypy on changed files and fix all issues found
- [x] Prepare git commit message for Step 3

## Pull Request

- [ ] Review all changes across steps 1–3 for correctness and completeness
- [ ] Confirm no logic changes were introduced (pure file move only)
- [ ] Confirm no backward-compatible re-exports were added
- [ ] Verify PR description accurately summarizes the change (issue #351, files created/modified/deleted)
- [ ] Prepare PR summary for review
