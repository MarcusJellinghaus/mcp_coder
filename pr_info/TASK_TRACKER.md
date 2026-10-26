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

### Step 1: Baseline + move blocked-marker tests to `test_task_processing_blocked.py`
See [step_1.md](./steps/step_1.md)

- [ ] Implementation: record baseline (55/193/55 passed, write `pr_info/.suite_baseline.txt`), move `TestReadAndClearBlocked`, `TestBlockedExitInPrompts`, `TestProcessSingleTaskBlocked`, fix imports
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 2: Move mypy fix-up tests to `test_task_processing_mypy.py`
See [step_2.md](./steps/step_2.md)

- [ ] Implementation: move `TestCheckAndFixMypy`, fix imports, verify collect counts (base 28)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 3: Move retry-wrapper tests to `test_task_processing_retry.py`
See [step_3.md](./steps/step_3.md)

- [ ] Implementation: move `TestProcessTaskWithRetry`, fix imports, verify collect counts (base 20)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 4: Move branch-name tests, drop allowlist entry, final verification
See [step_4.md](./steps/step_4.md)

- [ ] Implementation: move `TestBranchNameSource`, fix imports, remove `.large-files-allowlist` line, run final verification (lint-imports, tach, vulture, check_file_size, counts, searches, compact diff)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

## Pull Request

- [ ] PR review: review full branch diff against base branch
- [ ] PR summary prepared
