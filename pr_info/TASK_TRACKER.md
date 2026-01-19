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

### Step 1: Create Slash Command

- [ ] Implement slash command `.claude/commands/implementation_finalise.md`
- [ ] Run pylint and fix all issues found
- [ ] Run pytest and fix all issues found
- [ ] Run mypy and fix all issues found
- [ ] Prepare git commit message for Step 1

### Step 2: Workflow Integration and Tests

- [ ] Add `run_finalisation()` function to `src/mcp_coder/workflows/implement/core.py`
- [ ] Integrate finalisation call into `run_implement_workflow()` after final mypy check
- [ ] Add unit tests to `tests/workflows/implement/test_core.py`
- [ ] Run pylint and fix all issues found
- [ ] Run pytest and fix all issues found
- [ ] Run mypy and fix all issues found
- [ ] Prepare git commit message for Step 2

---

## Pull Request

- [ ] Review all implementation steps for completeness
- [ ] Verify all quality checks pass (pylint, pytest, mypy)
- [ ] Create PR summary with changes overview
