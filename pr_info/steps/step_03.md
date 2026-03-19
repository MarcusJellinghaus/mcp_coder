# Step 3: Add regression tests

## File
`tests/workflows/vscodeclaude/test_templates.py`

## Tests to add

### 3a. Test `--llm-method claude_code_cli` in `AUTOMATED_SECTION_WINDOWS`
Assert that the template string contains `--llm-method claude_code_cli`.

### 3b. Test `--llm-method claude_code_cli` in `DISCUSSION_SECTION_WINDOWS`
Assert that the template string contains `--llm-method claude_code_cli`.

### 3c. Test `langchain_code_api` reconstruction fix
In a test for `run_create_plan_workflow` (or a unit test for the llm_method reconstruction logic), verify that passing `provider="langchain", method="api"` produces `llm_method="langchain"`, not `"langchain_code_api"`.

This test should live in `tests/workflows/create_plan/` alongside the existing tests for that workflow.
