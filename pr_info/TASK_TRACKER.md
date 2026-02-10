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

### Step 1: Add `is_status_eligible_for_session()` Function
[Details](./steps/step_1.md)

- [x] Write test class `TestIsStatusEligibleForSession` in `tests/workflows/vscodeclaude/test_issues.py`
- [x] Implement `is_status_eligible_for_session()` in `src/mcp_coder/workflows/vscodeclaude/issues.py`
- [x] Run pylint and fix any issues
- [x] Run pytest and ensure all tests pass
- [x] Run mypy and fix any type errors
- [x] Prepare git commit message for Step 1

### Step 2: Update `display_status_table()` with "(Closed)" Prefix and Folder-Exists Filter
[Details](./steps/step_2.md)

- [x] Add test cases for "(Closed)" prefix in status column in `tests/workflows/vscodeclaude/test_status_display.py`
- [ ] Add test case for closed issue with missing folder being skipped
- [ ] Add test cases for bot stage sessions showing simple delete action
- [ ] Add test cases for pr-created sessions showing simple delete action
- [ ] Update imports in `src/mcp_coder/workflows/vscodeclaude/status.py`
- [ ] Remove the early `continue` for closed issues
- [ ] Add folder existence check for closed issues
- [ ] Add "(Closed)" prefix formatting
- [ ] Add `is_status_eligible_for_session` check for stale computation
- [ ] Run pylint and fix any issues
- [ ] Run pytest and ensure all tests pass
- [ ] Run mypy and fix any type errors
- [ ] Prepare git commit message for Step 2

### Step 3: Update `get_stale_sessions()` to Include Ineligible Sessions
[Details](./steps/step_3.md)

- [ ] Add test cases for closed issue sessions being included in `tests/workflows/vscodeclaude/test_cleanup.py`
- [ ] Add test cases for bot stage sessions being included
- [ ] Add test cases for pr-created sessions being included
- [ ] Add test case for eligible sessions NOT being included
- [ ] Update imports in `src/mcp_coder/workflows/vscodeclaude/cleanup.py`
- [ ] Update `get_stale_sessions()` with closed issue check
- [ ] Update `get_stale_sessions()` with ineligibility check
- [ ] Run pylint and fix any issues
- [ ] Run pytest and ensure all tests pass
- [ ] Run mypy and fix any type errors
- [ ] Prepare git commit message for Step 3

### Step 4: Update `restart_closed_sessions()` with Eligibility Checks + Module Docstring
[Details](./steps/step_4.md)

- [ ] Add test cases for closed issues not being restarted in `tests/workflows/vscodeclaude/test_orchestrator_sessions.py`
- [ ] Add test cases for bot stage issues not being restarted
- [ ] Add test cases for pr-created issues not being restarted
- [ ] Add test cases for eligible issues being restarted
- [ ] Add test case for eligible-to-eligible transition (04 → 07) - should restart with updated status
- [ ] Add module docstring to `src/mcp_coder/workflows/vscodeclaude/orchestrator.py`
- [ ] Add import for `is_status_eligible_for_session`
- [ ] Add closed issue check in `restart_closed_sessions()`
- [ ] Add eligibility check in `restart_closed_sessions()`
- [ ] Remove the redundant `is_session_stale()` check
- [ ] Run pylint and fix any issues
- [ ] Run pytest and ensure all tests pass
- [ ] Run mypy and fix any type errors
- [ ] Prepare git commit message for Step 4

---

## Pull Request

- [ ] Review all acceptance criteria from summary.md
- [ ] Verify sessions at bot_pickup statuses (02, 05, 08) are NOT restarted
- [ ] Verify sessions at bot_busy statuses (03, 06, 09) are NOT restarted
- [ ] Verify sessions at status-10:pr-created are NOT restarted
- [ ] Verify sessions for closed issues are NOT restarted
- [ ] Verify sessions at human_action statuses with commands (01, 04, 07) for open issues ARE restarted
- [ ] Verify stale sessions show `→ Delete (--cleanup)`
- [ ] Verify closed issues show "(Closed)" prefix in Status column
- [ ] Verify closed issue sessions are visible in display only if folder exists
- [ ] Verify dirty folders show `!! Manual cleanup`
- [ ] Verify all non-restartable sessions are eligible for `--cleanup` (if clean)
- [ ] Verify session lifecycle rules documented in orchestrator.py module docstring
- [ ] Prepare PR title and summary
