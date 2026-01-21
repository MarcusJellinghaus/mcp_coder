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

### Step 1: Delete Duplicate Files and Directory
See [step_1.md](steps/step_1.md) for details.

- [x] Delete `workflows/config/labels.json`
- [x] Delete `workflows/config/__init__.py`
- [x] Verify `workflows/config/` directory is removed
- [ ] Verify `tests/workflows/config/` still exists
- [ ] Run pylint checks and fix issues
- [ ] Run pytest and fix failures
- [ ] Run mypy checks and fix issues
- [ ] Prepare git commit message for Step 1

### Step 2: Simplify Test Fixtures
See [step_2.md](steps/step_2.md) for details.

- [ ] Simplify `labels_config_path` fixture in `tests/conftest.py`
- [ ] Simplify `labels_config_path` fixture in `tests/workflows/conftest.py`
- [ ] Verify both fixtures return consistent results
- [ ] Run pylint checks and fix issues
- [ ] Run pytest and fix failures
- [ ] Run mypy checks and fix issues
- [ ] Prepare git commit message for Step 2

### Step 3: Verify All Tests Pass and CLI Works
See [step_3.md](steps/step_3.md) for details.

- [ ] Run full test suite with `pytest tests/`
- [ ] Run `tests/workflows/test_label_config.py` (override mechanism tests)
- [ ] Run `tests/workflows/test_validate_labels.py` (validation tests)
- [ ] Run `tests/cli/commands/test_define_labels.py` (CLI tests)
- [ ] Verify `mcp-coder define-labels --help` CLI responds
- [ ] Run pylint checks and fix issues
- [ ] Run pytest and fix failures
- [ ] Run mypy checks and fix issues
- [ ] Prepare git commit message for Step 3

---

## Pull Request

- [ ] Review all implementation steps are complete
- [ ] Verify all quality checks pass (pylint, pytest, mypy)
- [ ] Prepare PR summary
- [ ] Create pull request
