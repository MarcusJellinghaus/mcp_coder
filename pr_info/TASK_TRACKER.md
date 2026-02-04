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

### Step 1: Update Templates ([step_1.md](./steps/step_1.md))

- [x] Replace `STATUS_FILE_TEMPLATE` with plain text banner format
- [x] Update `GITIGNORE_ENTRY` to use `.txt` instead of `.md`
- [x] Add second task to `TASKS_JSON_TEMPLATE` for auto-opening status file
- [x] Remove `INTERVENTION_ROW` (no longer needed)
- [x] Run pylint and fix any issues
- [x] Run pytest and fix any issues
- [x] Run mypy and fix any issues
- [x] Prepare git commit message for Step 1

### Step 2: Update Workspace Functions and Gitignore ([step_2.md](./steps/step_2.md))

- [x] Update `create_status_file()` to write `.txt` file with new template format
- [x] Update `update_gitignore()` idempotency check from `.md` to `.txt`
- [x] Add `.vscodeclaude_status.txt` to project root `.gitignore`
- [x] Run pylint and fix any issues
- [x] Run pytest and fix any issues (tests expected to fail until Step 3)
- [x] Run mypy and fix any issues
- [x] Prepare git commit message for Step 2

### Step 3: Update Tests ([step_3.md](./steps/step_3.md))

- [ ] Update `test_update_gitignore_*` tests to check for `.txt`
- [ ] Update `test_create_status_file*` tests for new filename and format
- [ ] Update `test_create_vscode_task` to verify two tasks exist
- [ ] Run pylint and fix any issues
- [ ] Run pytest and fix any issues
- [ ] Run mypy and fix any issues
- [ ] Prepare git commit message for Step 3

---

## Pull Request

- [ ] Review all changes across modified files
- [ ] Verify all tests pass
- [ ] Verify all quality checks pass (pylint, pytest, mypy)
- [ ] Prepare PR title and description
- [ ] Create Pull Request
