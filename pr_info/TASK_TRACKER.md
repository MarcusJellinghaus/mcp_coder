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

### Step 1: Add `stale_timeout_minutes` to labels.json Schema
- [ ] Implement Step 1 - Add `stale_timeout_minutes` field to bot_busy labels ([step_1.md](./steps/step_1.md))
- [ ] Run quality checks (pylint, pytest, mypy) and fix all issues
- [ ] Prepare git commit message for Step 1

### Step 2: Issue Initialization in define-labels
- [ ] Implement Step 2 - Add `check_status_labels` and `initialize_issues` functions ([step_2.md](./steps/step_2.md))
- [ ] Run quality checks (pylint, pytest, mypy) and fix all issues
- [ ] Prepare git commit message for Step 2

### Step 3: Validation and Staleness Detection in define-labels
- [ ] Implement Step 3 - Add `calculate_elapsed_minutes`, `check_stale_bot_process`, and `validate_issues` functions ([step_3.md](./steps/step_3.md))
- [ ] Run quality checks (pylint, pytest, mypy) and fix all issues
- [ ] Prepare git commit message for Step 3

### Step 4: Exit Codes and Output Formatting in define-labels
- [ ] Implement Step 4 - Update `execute_define_labels()` with initialization, validation, and exit codes ([step_4.md](./steps/step_4.md))
- [ ] Run quality checks (pylint, pytest, mypy) and fix all issues
- [ ] Prepare git commit message for Step 4

### Step 5: coordinator issue-stats Core Functions
- [ ] Implement Step 5 - Move core functions from `workflows/issue_stats.py` to `coordinator/issue_stats.py` ([step_5.md](./steps/step_5.md))
- [ ] Run quality checks (pylint, pytest, mypy) and fix all issues
- [ ] Prepare git commit message for Step 5

### Step 6: coordinator issue-stats CLI Wiring
- [ ] Implement Step 6 - Add `execute_coordinator_issue_stats()` and register subcommand in main.py ([step_6.md](./steps/step_6.md))
- [ ] Run quality checks (pylint, pytest, mypy) and fix all issues
- [ ] Prepare git commit message for Step 6

### Step 7: Cleanup - Delete workflows/ Folder
- [ ] Implement Step 7 - Delete legacy `workflows/` folder and migrate test files ([step_7.md](./steps/step_7.md))
- [ ] Run quality checks (pylint, pytest, mypy) and fix all issues
- [ ] Prepare git commit message for Step 7

### Step 8: Documentation Updates
- [ ] Implement Step 8 - Update `repository-setup.md` and `cli-reference.md` ([step_8.md](./steps/step_8.md))
- [ ] Run quality checks (pylint, pytest, mypy) and fix all issues
- [ ] Prepare git commit message for Step 8

---

## Pull Request

- [ ] Final review of all changes across all steps
- [ ] Verify all tests pass (full test suite)
- [ ] Verify all quality checks pass (pylint, mypy)
- [ ] Create PR summary with overview of changes
- [ ] Submit pull request for review
