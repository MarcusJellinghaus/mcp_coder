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

### Step 1: Add PROMPT_3_TIMEOUT Constant
- [x] Add PROMPT_3_TIMEOUT = 900 constant to src/mcp_coder/workflows/create_plan.py (after logger setup, before first function)
- [x] Add clear multi-line comment explaining the rationale (15 minutes for detailed multi-file plans vs 600s standard timeout)
- [x] Follow PEP 8 naming conventions and code style
- [x] Run pylint code quality check using mcp__code-checker__run_pylint_check
- [x] Run pytest tests using mcp__code-checker__run_pytest_check with extra_args=["-n", "auto", "-m", "not git_integration and not claude_integration and not formatter_integration and not github_integration"]
- [x] Run mypy type checking using mcp__code-checker__run_mypy_check
- [x] Fix any issues found by code quality checks
- [x] Verify constant is defined correctly and module imports successfully
- [x] Prepare git commit message for Step 1 changes

### Step 2: Update Prompt 3 Timeout References
- [ ] Update Prompt 3 debug log message (~line 359) to use f-string with {PROMPT_3_TIMEOUT}s
- [ ] Update Prompt 3 timeout parameter (~line 363) to use PROMPT_3_TIMEOUT constant
- [ ] Verify Prompts 1 & 2 remain unchanged with hardcoded 600
- [ ] Preserve exact formatting and indentation
- [ ] Run pylint code quality check using mcp__code-checker__run_pylint_check
- [ ] Run pytest tests using mcp__code-checker__run_pytest_check with extra_args=["-n", "auto", "-m", "not git_integration and not claude_integration and not formatter_integration and not github_integration"]
- [ ] Run mypy type checking using mcp__code-checker__run_mypy_check
- [ ] Fix any issues found by code quality checks
- [ ] Verify both timeout locations updated correctly
- [ ] Prepare git commit message for Step 2 changes

## Pull Request

- [ ] Review all changes and verify they match the implementation plan
- [ ] Run final code quality checks on all modified files
- [ ] Format all code using ./tools/format_all.sh before committing
- [ ] Create comprehensive PR description summarizing the timeout increase from 10 to 15 minutes
- [ ] Verify PR title clearly describes the change (e.g., "Increase timeout for implementation plan creation prompt from 10 to 15 minutes")
