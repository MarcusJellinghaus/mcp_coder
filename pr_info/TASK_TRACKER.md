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

### Step 1: Update Tests for Real GitHub Log Format
See [step_1.md](./steps/step_1.md) for details.

- [x] Update test mocks in `tests/checks/test_branch_status.py` to use GitHub format `{number}_{job_name}.txt`
- [x] Verify tests FAIL after updating mocks (expected behavior)
- [x] Run pylint, pytest, mypy on modified test file
- [x] Fix all issues found by quality checks
- [x] Prepare git commit message for Step 1

### Step 2: Add Test for GitHub URL Display
See [step_2.md](./steps/step_2.md) for details.

- [ ] Add `test_build_ci_error_details_includes_github_urls()` function to test file
- [ ] Verify new test FAILS (expected before implementation)
- [ ] Run pylint, pytest, mypy on modified test file
- [ ] Fix all issues found by quality checks
- [ ] Prepare git commit message for Step 2

### Step 3: Add Tests for Error Handling and Fallback
See [step_3.md](./steps/step_3.md) for details.

- [ ] Add `test_build_ci_error_details_logs_not_available_with_url()` function
- [ ] Add `test_build_ci_error_details_fallback_to_old_format()` function
- [ ] Verify both new tests FAIL (expected before implementation)
- [ ] Run pylint, pytest, mypy on modified test file
- [ ] Fix all issues found by quality checks
- [ ] Prepare git commit message for Step 3

### Step 4: Implement Pattern-Based Log Matching
See [step_4.md](./steps/step_4.md) for details.

- [ ] Implement pattern-based log matching in `_build_ci_error_details()` function
- [ ] Add multi-match warning logic (Decision 1)
- [ ] Add fallback to old format for backward compatibility (Decision 2)
- [ ] Update warning message in `get_failed_jobs_summary()` function (Decision 4)
- [ ] Verify updated tests now PASS
- [ ] Run pylint, pytest, mypy on modified source file
- [ ] Fix all issues found by quality checks
- [ ] Prepare git commit message for Step 4

### Step 5: Add GitHub URL Display
See [step_5.md](./steps/step_5.md) for details.

- [ ] Extract run URL from `run_data` parameter
- [ ] Add run URL display at top of error output
- [ ] Add job URL display for each failed job
- [ ] Verify `test_build_ci_error_details_includes_github_urls()` now PASSES
- [ ] Run pylint, pytest, mypy on modified source file
- [ ] Fix all issues found by quality checks
- [ ] Prepare git commit message for Step 5

### Step 6: Enhance Error Message When Logs Unavailable
See [step_6.md](./steps/step_6.md) for details.

- [ ] Replace simple error message with URL-enhanced version
- [ ] Add GitHub URL to error message when logs not available locally
- [ ] Verify `test_build_ci_error_details_logs_not_available_with_url()` now PASSES
- [ ] Run pylint, pytest, mypy on modified source file
- [ ] Fix all issues found by quality checks
- [ ] Prepare git commit message for Step 6

### Step 7: Run Full Test Suite and Verify
See [step_7.md](./steps/step_7.md) for details.

- [ ] Run complete test suite for `test_branch_status.py`
- [ ] Verify all 6 key tests PASS (3 new + 3 updated)
- [ ] Verify no regressions in existing tests
- [ ] Run pylint, pytest, mypy on entire codebase
- [ ] Fix any remaining issues found by quality checks
- [ ] Prepare git commit message for Step 7 (if needed)

## Pull Request

- [ ] Review all implementation changes against [summary.md](./steps/summary.md)
- [ ] Verify all decisions from [decisions.md](./steps/decisions.md) are implemented
- [ ] Create comprehensive PR description with before/after examples
- [ ] Tag PR for code review
