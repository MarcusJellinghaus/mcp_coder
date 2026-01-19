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

### Step 1: Update Implementation Prompt
See [step_1.md](steps/step_1.md)

- [x] Update `src/mcp_coder/prompts/prompts.md` - Change commit message instruction from "Prepare commit message when that sub-task appears" to "Write commit message to `pr_info/.commit_message.txt`"
- [x] Run quality checks (pylint, pytest, mypy) and fix any issues
- [x] Prepare git commit message

### Step 2: Update task_processing.py - Commit Message File Handling
See [step_2.md](steps/step_2.md)

- [x] Add `COMMIT_MESSAGE_FILE` constant to `src/mcp_coder/workflows/implement/task_processing.py`
- [x] Add `parse_llm_commit_response` import from `commit_operations`
- [x] Implement `_cleanup_commit_message_file()` helper function
- [x] Call cleanup function at start of `process_single_task()`
- [x] Modify `commit_changes()` to read commit message file if present (with fallback to LLM)
- [x] Add `TestCommitMessageFile` test class with `test_cleanup_removes_existing_file` and `test_cleanup_handles_missing_file` tests
- [ ] Add `test_commit_changes_uses_file_when_present` test to `TestCommitChanges`
- [ ] Add `test_commit_changes_falls_back_to_llm_when_no_file` test to `TestCommitChanges`
- [ ] Add `test_commit_changes_logs_message_on_failure` test to `TestCommitChanges`
- [ ] Run quality checks (pylint, pytest, mypy) and fix any issues
- [ ] Prepare git commit message

### Step 3: Update CI Pipeline - Forbidden File Check
See [step_3.md](steps/step_3.md)

- [ ] Add file existence check for `pr_info/.commit_message.txt` to `.github/workflows/ci.yml` in `check-forbidden-folders` job
- [ ] Verify YAML syntax is valid
- [ ] Prepare git commit message

---

## Pull Request

- [ ] Review all implementation steps are complete
- [ ] Run final quality checks across entire codebase
- [ ] Prepare PR summary with all changes
