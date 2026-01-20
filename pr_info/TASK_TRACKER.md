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

### Step 0: Foundational Enhancements
> See: [pr_info/steps/step_0.md](steps/step_0.md)

- [x] Write tests for step-level data in `tests/utils/github_operations/test_ci_results_manager_status.py`
- [x] Add `StepData` and `JobData` TypedDicts to `ci_results_manager.py`
- [x] Update `CIStatusData` to use `List[JobData]`
- [x] Update `get_latest_ci_status()` to include steps in job data
- [x] Add `get_latest_commit_sha()` helper to `commits.py`
- [x] Write tests for `get_latest_commit_sha()` in `test_commits.py`
- [x] Run pylint and fix any issues
- [x] Run pytest and fix any failing tests
- [x] Run mypy and fix any type errors
- [x] Prepare git commit message for Step 0

**Commit Message:**
```
feat(ci): add step-level data to CI status and commit SHA helper

- Add StepData and JobData TypedDicts for improved type safety
- Update CIStatusData.jobs to use List[JobData] instead of List[Dict]
- Enhance get_latest_ci_status() to include step data for each job
- Add get_latest_commit_sha() helper for debug logging support
- Add comprehensive tests for step-level data in CI status
- Add tests for get_latest_commit_sha() function

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
```

---

### Step 1: Add Constants, Prompts, and .gitignore Entry
> See: [pr_info/steps/step_1.md](steps/step_1.md)

- [x] Add CI check constants to `src/mcp_coder/workflows/implement/constants.py`
- [x] Add CI Failure Analysis and CI Fix prompts to `src/mcp_coder/prompts/prompts.md`
- [x] Update `.gitignore` with `pr_info/.ci_problem_description.md`
- [x] Add `get_prompt_with_substitutions()` helper to `prompt_manager.py`
- [x] Write tests for `get_prompt_with_substitutions()` in `tests/test_prompt_manager.py`
- [x] Run pylint and fix any issues
- [x] Run pytest and fix any failing tests
- [x] Run mypy and fix any type errors
- [x] Prepare git commit message for Step 1

---

### Step 2: Add Helper Functions with Tests (TDD)
> See: [pr_info/steps/step_2.md](steps/step_2.md)

- [x] Create test file `tests/workflows/implement/test_ci_check.py`
- [x] Write tests for `_extract_log_excerpt()` function
- [x] Write tests for `_get_failed_jobs_summary()` function
- [x] Implement `_extract_log_excerpt()` in `core.py`
- [x] Implement `_get_failed_jobs_summary()` in `core.py`
- [x] Run pylint and fix any issues
- [x] Run pytest and fix any failing tests
- [x] Run mypy and fix any type errors
- [x] Prepare git commit message for Step 2

**Commit Message:**
```
feat(ci): add helper functions for CI log processing

- Add _extract_log_excerpt() function to truncate long logs (first 30 + last 170 lines)
- Add _get_failed_jobs_summary() function to extract failed job details and log excerpts
- Add comprehensive tests for both helper functions in test_ci_check.py
- Follow TDD approach: tests written first, then implementation

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
```

---

### Step 3: Implement Main CI Check Function with Tests (TDD)
> See: [pr_info/steps/step_3.md](steps/step_3.md)

- [ ] Write tests for `check_and_fix_ci()` in `test_ci_check.py`
- [ ] Add required imports to `core.py`
- [ ] Implement `check_and_fix_ci()` main function
- [ ] Implement CI polling logic (max 50 attempts, 15s interval)
- [ ] Implement fix loop (max 3 attempts)
- [ ] Implement new run detection (6 attempts at 5s intervals)
- [ ] Implement error handling (API errors → exit 0, git errors → exit 1)
- [ ] Run pylint and fix any issues
- [ ] Run pytest and fix any failing tests
- [ ] Run mypy and fix any type errors
- [ ] Prepare git commit message for Step 3

---

### Step 4: Integrate CI Check into Workflow
> See: [pr_info/steps/step_4.md](steps/step_4.md)

- [ ] Add CI check call as Step 5.6 in `run_implement_workflow()`
- [ ] Handle CI check failure (return 1 if `check_and_fix_ci()` returns False)
- [ ] Run pylint and fix any issues
- [ ] Run pytest and fix any failing tests
- [ ] Run mypy and fix any type errors
- [ ] Prepare git commit message for Step 4

---

## Pull Request

- [ ] Review all implementation steps are complete
- [ ] Verify all tests pass: `pytest tests/workflows/implement/ -v`
- [ ] Verify code quality: pylint, mypy checks pass
- [ ] Prepare PR summary with changes overview
- [ ] Create pull request with implementation summary
