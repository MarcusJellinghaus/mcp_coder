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

### Step 1: Move Test Files and Delete Old Directory
See [step_1.md](./steps/step_1.md) for details.

- [x] Move all 13 test files from `tests/utils/vscodeclaude/` to `tests/workflows/vscodeclaude/`
- [x] Verify `tests/utils/vscodeclaude/` is empty
- [x] Delete `tests/utils/vscodeclaude/` directory
- [x] Confirm `tests/workflows/vscodeclaude/` contains all 13 files
- [x] Run pylint check and fix any issues
- [x] Run pytest check and fix any issues
- [x] Run mypy check and fix any issues
- [x] Prepare git commit message for Step 1

### Step 2: Verification Checks
See [step_2.md](./steps/step_2.md) for details.

- [x] Run mcp__code-checker__run_pytest_check() - verify all tests pass
- [x] Run mcp__code-checker__run_pylint_check() - verify no linting errors
- [x] Run mcp__code-checker__run_mypy_check() - verify type checking passes
- [x] Verify acceptance criteria: Directory `tests/workflows/vscodeclaude/` created
- [x] Verify acceptance criteria: All 13 test files moved
- [x] Verify acceptance criteria: `tests/utils/vscodeclaude/` deleted entirely
- [x] Run pylint check and fix any issues
- [x] Run pytest check and fix any issues
- [x] Run mypy check and fix any issues
- [x] Prepare git commit message for Step 2

---

## Pull Request

- [ ] Review all implementation steps are complete
- [ ] Verify all acceptance criteria from issue #363 are met
- [ ] Prepare PR summary with changes made
- [ ] Create Pull Request
