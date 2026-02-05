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

### Step 1: Add Test for Dev Dependencies in Template
See [step_1.md](./steps/step_1.md) for details.

- [x] Create test file `tests/workflows/vscodeclaude/test_templates.py`
- [x] Implement `test_venv_section_installs_dev_dependencies()` test function
- [x] Verify test fails as expected (TDD red phase)
- [x] Run pylint on new test file and fix any issues
- [x] Run mypy on new test file and fix any issues
- [x] Prepare git commit message for Step 1

### Step 2: Update Template to Use --extra dev
See [step_2.md](./steps/step_2.md) for details.

- [x] Update `src/mcp_coder/workflows/vscodeclaude/templates.py`
- [x] Change `uv sync --extra types` to `uv sync --extra dev` in VENV_SECTION_WINDOWS
- [x] Verify test from Step 1 now passes (TDD green phase)
- [x] Run pylint on modified file and fix any issues
- [x] Run mypy on modified file and fix any issues
- [x] Prepare git commit message for Step 2

### Step 3: Verify Change and Run Full Test Suite
See [step_3.md](./steps/step_3.md) for details.

- [x] Read templates.py and confirm "uv sync --extra dev" is present
- [x] Confirm "uv sync --extra types" is absent from templates.py
- [x] Run new test: test_venv_section_installs_dev_dependencies with pytest
- [ ] Run all vscodeclaude tests for regression check with pytest
- [ ] Run full unit test suite (fast tests only) with pytest
- [ ] Update documentation in `docs/coordinator-vscodeclaude.md`
- [ ] Run pylint on all modified files and fix any issues
- [ ] Run mypy on all modified files and fix any issues
- [ ] Prepare git commit message for Step 3 (documentation update)

## Pull Request

- [ ] Review all changes and ensure they align with implementation plan
- [ ] Prepare comprehensive PR description with summary and test plan
- [ ] Verify all tasks above are completed
