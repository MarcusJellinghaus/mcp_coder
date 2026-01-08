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

### Step 1: Add Test for Conversations Directory Cleanup
*Reference: [pr_info/steps/step_1.md](steps/step_1.md)*

- [ ] Implement test `test_cleanup_repository_includes_conversations_cleanup` in `tests/workflows/create_pr/test_repository.py`
- [ ] Update existing tests to mock `clean_profiler_output` for full isolation
- [ ] Run quality checks (pylint, pytest, mypy) and fix any issues
- [ ] Prepare git commit message for Step 1

### Step 2: Implement Conversations Directory Deletion
*Reference: [pr_info/steps/step_2.md](steps/step_2.md)*

- [ ] Update `cleanup_repository()` docstring in `src/mcp_coder/workflows/create_pr/core.py`
- [ ] Add `.conversations` directory deletion logic in `cleanup_repository()`
- [ ] Update commit message from "Clean up pr_info/steps planning files" to "Clean up pr_info temporary folders"
- [ ] Run quality checks (pylint, pytest, mypy) and fix any issues
- [ ] Prepare git commit message for Step 2

---

## Pull Request

- [ ] Verify all acceptance criteria from summary.md are met
- [ ] Review PR for code quality and completeness
- [ ] Prepare PR summary
