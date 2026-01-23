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

### Step 1: Verify Test Imports and Create `readers.py`
*See: [pr_info/steps/step_1.md](steps/step_1.md)*

- [x] Part A: Verify test imports use package level (not direct submodule imports)
- [x] Part A: Run all git_operations tests to establish baseline
- [x] Part B: Create `src/mcp_coder/utils/git_operations/readers.py` with all read-only operations
- [x] Run pylint on `src/mcp_coder/utils/git_operations/readers.py`
- [x] Run pytest on `tests/utils/git_operations/`
- [x] Run mypy on `src/mcp_coder/utils/git_operations/readers.py`
- [x] Prepare git commit message for Step 1

---

### Step 2: Update Source Modules and Package Exports
*See: [pr_info/steps/step_2.md](steps/step_2.md)*

- [x] Part A: Update `branches.py` - remove moved functions, import from readers
- [x] Part B: Update `remotes.py` - add rebase_onto_branch, import from readers
- [x] Part C: Update `staging.py` - change imports to readers
- [x] Part C: Update `file_tracking.py` - change imports to readers
- [x] Part C: Update `diffs.py` - change imports to readers
- [x] Part C: Update `commits.py` - change imports to readers
- [x] Part D: Update `__init__.py` - re-export from new locations
- [x] Part E: Delete `src/mcp_coder/utils/git_operations/repository.py`
- [x] Run pylint on `src/mcp_coder/utils/git_operations/`
- [x] Run pytest on `tests/utils/git_operations/`
- [x] Run mypy on `src/mcp_coder/utils/git_operations/`
- [x] Prepare git commit message for Step 2

---

### Step 3: Update External Imports and Add Import Linter Contract
*See: [pr_info/steps/step_3.md](steps/step_3.md)*

- [x] Part A: Update `src/mcp_coder/workflows/create_plan.py` - change repository to readers
- [x] Part B: Update `src/mcp_coder/utils/github_operations/ci_results_manager.py` - change branches to readers
- [ ] Part C: Update `src/mcp_coder/utils/github_operations/issue_manager.py` - change branches to readers
- [ ] Part D: Update `src/mcp_coder/workflows/create_pr/core.py` - change branches to readers
- [ ] Part E: Update `src/mcp_coder/cli/commands/set_status.py` - change branches to readers
- [ ] Part F: Add import linter contract to `.importlinter` for git_operations internal layering
- [ ] Run pylint on all modified external files
- [ ] Run pytest on `tests/`
- [ ] Run mypy on modified files
- [ ] Run `lint-imports` to verify layering contract passes
- [ ] Prepare git commit message for Step 3

---

### Step 4: Reorganize Test Files
*See: [pr_info/steps/step_4.md](steps/step_4.md)*

- [ ] Part A: Create `tests/utils/git_operations/test_readers.py` with reader function tests
- [ ] Part B: Update `tests/utils/git_operations/test_branches.py` - keep only mutation tests
- [ ] Part C: Update `tests/utils/git_operations/test_remotes.py` - add rebase_onto_branch tests
- [ ] Part D: Delete `tests/utils/git_operations/test_repository.py`
- [ ] Run pylint on `tests/utils/git_operations/`
- [ ] Run pytest on `tests/utils/git_operations/` - verify test count unchanged
- [ ] Run mypy on `tests/utils/git_operations/`
- [ ] Prepare git commit message for Step 4

---

## Pull Request

- [ ] Run full test suite (`pytest tests/ -v`)
- [ ] Run full pylint check on `src/mcp_coder/`
- [ ] Run full mypy check on `src/mcp_coder/`
- [ ] Run `lint-imports` to verify all contracts pass
- [ ] Verify public API unchanged (all exports from `__init__.py` work)
- [ ] Review PR for completeness and accuracy
- [ ] Prepare PR summary describing the layered architecture refactoring
