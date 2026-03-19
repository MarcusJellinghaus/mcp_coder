# Step 3: Update and add tests

## Overview
Update existing tests to reflect the removal of the `method` parameter, and add regression tests for the Windows template fix.

## Test changes

### 3a. Template regression tests
**File:** `tests/workflows/vscodeclaude/test_templates.py`
- Test that `AUTOMATED_SECTION_WINDOWS` contains `--llm-method claude_code_cli`
- Test that `DISCUSSION_SECTION_WINDOWS` contains `--llm-method claude_code_cli`

### 3b. Update `parse_llm_method` tests
**File:** `tests/llm/session/test_resolver.py`
- Update tests to expect `str` return (not tuple)
- Remove `claude_code_api` test case
- Add test that `claude_code_api` raises `ValueError`
- Keep tests for `claude_code_cli` → `"claude"` and `langchain` → `"langchain"`

### 3c. Update CLI utils tests
**File:** `tests/cli/test_utils.py`
- Update `parse_llm_method_from_args` tests to match new return type
- Remove `claude_code_api` test cases

### 3d. Update workflow tests
Update all workflow tests that pass `provider, method` to pass just `provider`:
- `tests/workflows/create_plan/test_main.py`
- `tests/workflows/create_plan/test_prompt_execution.py`
- `tests/integration/test_execution_dir_integration.py`
- Any other test files that reference `method` in LLM context

### 3e. Update interface tests (if any)
- Check for and update tests of `ask_llm()` / `prompt_llm()` signatures

### 3f. Add langchain routing test
**File:** `tests/llm/test_interface.py` (or appropriate existing test file)
- Add a mock-based unit test that calls `prompt_llm(provider="langchain")` and verifies it routes to `ask_langchain()`
- Confirms the langchain path works correctly after method removal

## Test strategy
- Run full test suite excluding integration markers to verify nothing breaks
- Template tests are simple string assertions (fast, no mocking needed)
- Resolver tests are pure unit tests (fast, no mocking needed)
- Workflow tests will need mock signature updates but logic stays the same
