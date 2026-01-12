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

### Step 1: Update pr_manager.py Import Statement
[Details: pr_info/steps/step_1.md]

- [x] Change import in `pr_manager.py` from `mcp_coder.utils` to `mcp_coder.utils.git_operations`
- [x] Run pylint and fix any issues found
- [x] Run pytest and fix any issues found
- [x] Run mypy and fix any issues found
- [x] Prepare git commit message for Step 1

### Step 2: Update .importlinter Configuration
[Details: pr_info/steps/step_2.md]

- [ ] Remove "Known violation (issue #277)" comments from `.importlinter`
- [ ] Remove `ignore_imports` exception from `external_services` contract
- [ ] Run pylint and fix any issues found
- [ ] Run pytest and fix any issues found
- [ ] Run mypy and fix any issues found
- [ ] Prepare git commit message for Step 2

---

## Pull Request

- [ ] Review all implementation steps are complete
- [ ] Verify lint-imports passes without exceptions
- [ ] Run full test suite and verify all tests pass
- [ ] Prepare PR summary with overview of changes
