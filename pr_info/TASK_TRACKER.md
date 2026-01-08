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

### Step 1: Add Tests for `ignore_files` Parameter
**Reference**: [pr_info/steps/step_1.md](steps/step_1.md)

- [x] Add 4 test scenarios to `tests/utils/git_operations/test_repository.py`
- [x] Run pylint and fix any issues
- [x] Run pytest and verify tests fail (TDD - tests written before implementation)
- [x] Run mypy and fix any type issues
- [x] Prepare git commit message for Step 1

---

### Step 2: Implement `ignore_files` Parameter and Update Callers
**Reference**: [pr_info/steps/step_2.md](steps/step_2.md)

- [x] Implement `ignore_files` parameter in `is_working_directory_clean()` function
- [x] Update caller: `src/mcp_coder/workflows/create_plan.py`
- [x] Update caller: `src/mcp_coder/workflows/implement/prerequisites.py`
- [x] Update caller: `src/mcp_coder/workflows/create_pr/core.py` (2 locations)
- [x] Remove `uv.lock` from `.gitignore`
- [x] Run pylint and fix any issues
- [x] Run pytest and verify all tests pass
- [x] Run mypy and fix any type issues
- [x] Prepare git commit message for Step 2

---

## Pull Request

- [ ] Review all changes for Issue #254
- [ ] Verify backward compatibility
- [ ] Prepare PR summary with test results
