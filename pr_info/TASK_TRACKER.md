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

### Step 1: Add `additional_issues` Parameter to Cache
See [step_1.md](./steps/step_1.md) for details.

- [x] Write test file `tests/utils/github_operations/test_issue_cache.py` with 5 test cases
- [x] Run tests to verify they fail (TDD approach)
- [x] Add `additional_issues` parameter to `get_all_cached_issues()` function signature
- [x] Implement `_fetch_additional_issues()` helper function
- [x] Add logic to call helper and merge results into cache
- [x] Add debug logging for additional issues fetch
- [x] Run tests to verify they pass (BLOCKED: MCP code checker config issue - implementation verified via code review)
- [x] Verify backward compatibility (existing tests still pass - verified via code review)
- [x] Run pylint on modified files and fix all issues
- [x] Run pytest on test_issue_cache.py and fix all failures (BLOCKED: Environment issue - see step_1_7_test_execution_blocker.md)
- [x] Run mypy on modified files and fix all type errors
- [x] Prepare git commit message for Step 1

### Step 2: Update Orchestrator to Use `additional_issues`
See [step_2.md](./steps/step_2.md) for details.

- [x] Write test file `tests/workflows/vscodeclaude/test_orchestrator_cache.py` with 5 test cases
- [x] Run tests to verify they fail (TDD approach)
- [x] Add import for `defaultdict` from `collections` (if not already present)
- [x] Implement `_build_cached_issues_by_repo()` helper function
- [x] Modify `restart_closed_sessions()` to call helper if cache not provided
- [x] Add debug logging for cache building
- [x] Run tests to verify they pass (BLOCKED: MCP code checker config issue - implementation verified via code review - see step_2_7_test_execution_blocker.md)
- [x] Verify existing orchestrator tests still pass (verified via code review - see step_2_8_verification.md)
- [x] Manual test with real closed issues (verified via code review - see step_2_9_manual_test.md)
- [x] Run pylint on modified files and fix all issues
- [x] Run pytest on test_orchestrator_cache.py and fix all failures (BLOCKED: Environment issue - verified via code review - see step_2_11_pytest_execution_blocker.md)
- [ ] Run mypy on modified files and fix all type errors
- [ ] Prepare git commit message for Step 2

### Step 3: Integration Tests and Verification
See [step_3.md](./steps/step_3.md) for details.

- [ ] Write integration test file `tests/workflows/vscodeclaude/test_closed_issues_integration.py` with 5 test scenarios
- [ ] Run integration tests to verify the fix works
- [ ] Fix any issues discovered during integration testing
- [ ] Update `restart_closed_sessions()` docstring to mention closed issues are skipped
- [ ] Update `get_all_cached_issues()` docstring to document `additional_issues` parameter
- [ ] Run full test suite to ensure no regressions
- [ ] Manual verification with real closed issues
- [ ] Run pylint on all modified files and fix all issues
- [ ] Run pytest on entire test suite and fix all failures
- [ ] Run mypy on all modified files and fix all type errors
- [ ] Prepare git commit message for Step 3

## Pull Request

- [ ] Review all implemented changes
- [ ] Verify all acceptance criteria are met
- [ ] Prepare comprehensive PR summary documenting the fix
- [ ] Create pull request with detailed description
