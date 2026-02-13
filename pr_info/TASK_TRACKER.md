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

### Step 1: Create `llm_response_utils.py` and Enhance `strip_claude_footers()` (TDD)
[Details](./steps/step_1.md)

- [ ] Create new module `src/mcp_coder/workflow_utils/llm_response_utils.py` with module docstring and imports
- [ ] Create new test file `tests/workflow_utils/test_llm_response_utils.py`
- [ ] Move `TestStripClaudeFooters` class from `test_commit_operations.py` to new test file
- [ ] Add ~3 new parameterized tests for case-insensitive matching, model variations, and AutoRunner Bot preservation
- [ ] Verify new tests fail (red phase)
- [ ] Move `strip_claude_footers()` function from `commit_operations.py` to `llm_response_utils.py`
- [ ] Enhance function with regex pattern matching: `r'^Co-Authored-By:\s*Claude.*<noreply@anthropic\.com>$'` with `re.IGNORECASE`
- [ ] Update function docstring to reflect case-insensitive matching, model variations, and PR body usage
- [ ] Add import to `commit_operations.py`: `from .llm_response_utils import strip_claude_footers`
- [ ] Remove original `strip_claude_footers()` function from `commit_operations.py`
- [ ] Remove `TestStripClaudeFooters` class from `test_commit_operations.py`
- [ ] Verify all tests pass (green phase)
- [ ] Run pylint on modified files and fix any errors
- [ ] Run pytest on `test_llm_response_utils.py` and `test_commit_operations.py` and fix any failures
- [ ] Run mypy on modified files and fix any type errors
- [ ] Prepare git commit message for Step 1

### Step 2: Apply Footer Stripping to PR Body in `parse_pr_summary()` (TDD)
[Details](./steps/step_2.md)

- [ ] Add ~2 new parameterized tests to `tests/workflows/create_pr/test_parsing.py` for PR body footer stripping
- [ ] Add test for preserving legitimate content that mentions footers
- [ ] Verify new tests fail (red phase)
- [ ] Add import to `src/mcp_coder/workflows/create_pr/core.py`: `from mcp_coder.workflow_utils.llm_response_utils import strip_claude_footers`
- [ ] Apply footer stripping to body in `parse_pr_summary()` before return: `body = strip_claude_footers(body)`
- [ ] Verify title remains unchanged (not stripped)
- [ ] Verify all tests pass (green phase)
- [ ] Run pylint on modified files and fix any errors
- [ ] Run pytest on `test_parsing.py` and fix any failures
- [ ] Run mypy on modified files and fix any type errors
- [ ] Prepare git commit message for Step 2

### Step 3: Integration Testing and Quality Gates
[Details](./steps/step_3.md)

- [ ] Run pytest on `tests/workflow_utils/test_llm_response_utils.py` with `show_details=True` and fix any failures
- [ ] Run pytest on `tests/workflows/create_pr/test_parsing.py` with `show_details=True` and fix any failures
- [ ] Run pytest on `tests/workflow_utils/test_commit_operations.py` with `show_details=True` to verify imports and fix any failures
- [ ] Run full test suite (fast unit tests only, excluding integration tests) and fix any failures
- [ ] Run pylint on `src` directory with categories `['error', 'fatal']` and fix all issues
- [ ] Run mypy on `src` directory with strict mode and fix all type errors
- [ ] Verify all acceptance criteria from summary.md are met
- [ ] Prepare git commit message for Step 3 (if any fixes were needed)

## Pull Request

- [ ] Review all implementation steps and verify completeness
- [ ] Verify all quality gates pass (pylint, pytest, mypy)
- [ ] Review PR description and ensure footers are stripped
- [ ] Prepare comprehensive PR summary with testing results
