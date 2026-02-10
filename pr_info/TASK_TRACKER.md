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

### Step 1: Update Source Files
See [step_1.md](./steps/step_1.md) for details.

- [ ] Implement Step 1: Replace `.vscodeclaude_status.md` with `.vscodeclaude_status.txt` in source files
- [ ] Run pylint and fix any issues
- [ ] Run pytest and fix any failures
- [ ] Run mypy and fix any type errors
- [ ] Prepare git commit message for Step 1

### Step 2: Update Test Files
See [step_2.md](./steps/step_2.md) for details.

- [ ] Implement Step 2: Replace `.vscodeclaude_status.md` with `.vscodeclaude_status.txt` in test files
- [ ] Run pylint and fix any issues
- [ ] Run pytest and fix any failures
- [ ] Run mypy and fix any type errors
- [ ] Prepare git commit message for Step 2

---

## Pull Request

- [ ] Review all changes for completeness
- [ ] Verify all tests pass
- [ ] Prepare PR summary
