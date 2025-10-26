# Task Status Tracker

## Instructions for LLM

This tracks **Feature Implementation** consisting of multiple **Implementation Steps** (tasks).

**Development Process:** See [DEVELOPMENT_PROCESS.md](./DEVELOPMENT_PROCESS.md) for detailed workflow, prompts, and tools.

**How to update tasks:**

1. Change [ ] to [x] when implementation step is fully complete (code + checks pass)
2. Change [x] to [ ] if task needs to be reopened
3. Add brief notes in the linked detail files if needed
4. Keep it simple - just GitHub-style checkboxes

**Task format:**

- [x] = Implementation step complete (code + all checks pass)
- [ ] = Implementation step not complete
- Each task links to a detail file in pr_info/steps/ folder

---

## Tasks

### Step 1: Update Tests for Runner Environment Detection (TDD Red Phase)
See [step_1.md](./steps/step_1.md) for detailed instructions.

- [x] Add new test: `test_prepare_llm_environment_uses_virtual_env_variable`
- [x] Add new test: `test_prepare_llm_environment_uses_conda_prefix`
- [x] Add new test: `test_prepare_llm_environment_uses_sys_prefix_fallback`
- [ ] Add new test: `test_prepare_llm_environment_separate_runner_project`
- [ ] Update existing test: `test_prepare_llm_environment_success` (remove detect_python_environment mock)
- [ ] Remove/replace test: `test_prepare_llm_environment_no_venv`
- [ ] Run pylint - fix all issues found
- [ ] Run pytest - verify tests FAIL (expected RED phase)
- [ ] Run mypy - fix all issues found
- [ ] Prepare git commit message for Step 1

### Step 2: Simplify Runner Environment Detection (TDD Green Phase)
See [step_2.md](./steps/step_2.md) for detailed instructions.

- [ ] Modify `prepare_llm_environment()` to use environment variables (VIRTUAL_ENV, CONDA_PREFIX, sys.prefix)
- [ ] Remove import for `detect_python_environment`
- [ ] Update docstring to explain runner environment detection
- [ ] Remove complex detection logic and platform-specific checks
- [ ] Run pylint - fix all issues found
- [ ] Run pytest - verify tests PASS (expected GREEN phase)
- [ ] Run mypy - fix all issues found
- [ ] Prepare git commit message for Step 2

### Step 2.5: Add Validation and Robustness Enhancements
See [step_2.5.md](./steps/step_2.5.md) for detailed instructions.

- [ ] Add private helper function `_get_runner_environment()` with validation logic
- [ ] Implement empty string handling for environment variables
- [ ] Add path existence validation with fallback behavior
- [ ] Add logging to show which environment source was used
- [ ] Update `prepare_llm_environment()` to use new helper function
- [ ] Add test: `test_prepare_llm_environment_empty_virtual_env`
- [ ] Add test: `test_prepare_llm_environment_invalid_path_fallback`
- [ ] Add test: `test_prepare_llm_environment_all_invalid_uses_sys_prefix`
- [ ] Run pylint - fix all issues found
- [ ] Run pytest - verify all tests pass
- [ ] Run mypy - fix all issues found
- [ ] Prepare git commit message for Step 2.5

### Step 3: Run Quality Checks, Cleanup, and Full Verification
See [step_3.md](./steps/step_3.md) for detailed instructions.

- [ ] Delete unused `detect_python_environment()` function from `src/mcp_coder/utils/detection.py`
- [ ] Run pytest with fast unit tests (exclude integration tests)
- [ ] Fix any pytest failures
- [ ] Run pylint on src and tests directories
- [ ] Fix all pylint issues
- [ ] Run mypy on src and tests directories
- [ ] Fix all mypy issues
- [ ] Run full test suite (all tests including integration)
- [ ] Fix any remaining test failures
- [ ] Prepare git commit message for Step 3

### Step 4: Update Documentation
See [step_4.md](./steps/step_4.md) for detailed instructions.

- [ ] Review README.md for accuracy (check venv requirements, setup instructions)
- [ ] Check setup/installation guides (if they exist)
- [ ] Verify .mcp.json configuration examples are correct
- [ ] Update architecture documentation (if it exists)
- [ ] Remove outdated venv requirement statements
- [ ] Remove platform-specific warnings that are no longer relevant
- [ ] Verify code examples in documentation are correct
- [ ] Run pylint - fix all issues found
- [ ] Run pytest - verify all tests pass
- [ ] Run mypy - fix all issues found
- [ ] Prepare git commit message for Step 4

---

## Pull Request

### PR Review and Summary
- [ ] Review all changes made across all steps
- [ ] Verify all acceptance criteria met (see summary.md)
- [ ] Run final full test suite (all tests must pass)
- [ ] Run final pylint check (must pass)
- [ ] Run final mypy check (must pass)
- [ ] Prepare comprehensive PR description with summary of changes
- [ ] Verify backward compatibility maintained
- [ ] Confirm no breaking API changes introduced
