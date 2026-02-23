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

<!-- Tasks populated from pr_info/steps/ by prepare_task_tracker -->

### Step 1: Update CLI Parser for New Parameters (TDD)
- [x] Write parser tests first (TestCheckBranchStatusParserEnhancements class with 8 tests)
- [x] Run parser tests to verify they fail (TDD approach)
- [x] Implement CLI parser changes for --ci-timeout and --fix [N] parameters
- [x] Run parser tests to verify they pass
- [x] Run pylint check and fix any issues found
- [x] Run pytest check and fix any test failures
- [x] Run mypy check and fix any type issues
- [x] Prepare git commit message for Step 1 implementation

### Step 2: Add CI Waiting Logic (TDD) 
- [ ] Write waiting logic tests first (TestCIWaitingLogic class with 8 tests)
- [ ] Run waiting logic tests to verify they fail (TDD approach)
- [ ] Implement _wait_for_ci_completion() and _show_progress() helper functions
- [ ] Implement CI waiting logic in execute_check_branch_status()
- [ ] Run waiting logic tests to verify they pass
- [ ] Run pylint check and fix any issues found
- [ ] Run pytest check and fix any test failures
- [ ] Run mypy check and fix any type issues
- [ ] Prepare git commit message for Step 2 implementation

### Step 3: Add Fix Retry Logic (TDD)
- [ ] Write fix retry tests first (TestFixRetryLogic class with 6 tests)
- [ ] Run fix retry tests to verify they fail (TDD approach)
- [ ] Enhance _run_auto_fixes() function with retry logic and new parameters
- [ ] Update execute_check_branch_status() to pass new parameters to _run_auto_fixes()
- [ ] Run fix retry tests to verify they pass
- [ ] Run pylint check and fix any issues found
- [ ] Run pytest check and fix any test failures
- [ ] Run mypy check and fix any type issues
- [ ] Prepare git commit message for Step 3 implementation

### Step 4: Update Documentation
- [ ] Update .claude/commands/check_branch_status.md with new parameters and examples
- [ ] Update docs/cli-reference.md with comprehensive parameter documentation
- [ ] Add exit codes table and usage examples to documentation
- [ ] Add workflow integration examples
- [ ] Run pylint check and fix any issues found
- [ ] Run pytest check and fix any test failures
- [ ] Run mypy check and fix any type issues
- [ ] Prepare git commit message for Step 4 implementation

## Pull Request
- [ ] Review all implementation steps are complete
- [ ] Run final pylint, pytest, and mypy checks across entire codebase
- [ ] Create comprehensive PR summary highlighting new CI waiting and fix retry capabilities
- [ ] Verify backward compatibility is preserved
- [ ] Test all documented usage examples work correctly
- [ ] Ensure exit codes match documentation (0=success, 1=failure, 2=error)
