# Step 1a: Update Test Mocks from `ask_llm` to `prompt_llm`

## Context

See `pr_info/steps/summary.md` for full context. This is step 1a of issue #551.

`ask_llm()` is a thin wrapper around `prompt_llm()` that discards structured response data (session_id, metadata, raw_response). Removing it is a prerequisite for centralized MLflow logging. This step updates all tests first (TDD-style) so that Step 1b can remove `ask_llm()` without breaking CI.

## LLM Prompt

```
You are implementing step 1a of issue #551 (see pr_info/steps/summary.md for full context).

Task: Update ALL test files that reference `ask_llm` to mock/use `prompt_llm` instead.
Change mock return values from plain strings to `LLMResponseDict` dicts.
Tests still pass because `ask_llm` still exists — they just no longer exercise it.

1. In each test file listed below:
   - Change mock targets from `ask_llm` to `prompt_llm`
   - Change mock return values from plain strings to LLMResponseDict dicts:
     {"text": "mocked response", "session_id": "test-sid", "provider": "claude",
      "version": "1.0", "timestamp": "2024-01-01T00:00:00", "raw_response": {}}
   - Update any assertions that check the return value to account for dict responses
   - If a test imports `ask_llm` directly, change to `prompt_llm`

2. Run all quality checks (pylint, mypy, pytest) and fix any issues.
```

## WHERE: Files to Modify

- `tests/llm/test_interface.py`
- `tests/test_module_exports.py`
- `tests/test_input_validation.py`
- `tests/llm/test_module_structure.py`
- `tests/llm/providers/test_provider_structure.py`
- `tests/llm/providers/claude/test_llm_sessions.py`
- `tests/llm/providers/claude/test_claude_integration.py`
- `tests/integration/test_execution_dir_integration.py`
- `tests/workflows/test_create_pr_integration.py`
- `tests/cli/commands/test_commit.py`
- `tests/workflow_utils/test_commit_operations.py`
- `tests/workflows/create_pr/test_file_operations.py`
- `tests/workflows/create_pr/test_generation.py`
- `tests/workflows/create_pr/test_parsing.py`
- `tests/workflows/create_pr/test_prerequisites.py`
- `tests/workflows/create_pr/test_repository.py`
- `tests/workflows/create_pr/test_workflow.py`

## WHAT: Changes Per File

### All test files
- **Change mock target**: `ask_llm` → `prompt_llm`
- **Change mock return**: plain `"string"` → `{"text": "string", "session_id": "test-sid", "provider": "claude", "version": "1.0", "timestamp": "2024-01-01T00:00:00", "raw_response": {}}`
- **Update assertions**: where tests check the raw return value, account for dict structure
- **Update imports**: if test imports `ask_llm`, change to `prompt_llm`

## HOW: Integration Points

No production code changes. Tests will still pass because `ask_llm` still exists in production code — the tests simply no longer exercise it.

## DATA: Return Values

Mock `prompt_llm` to return a dict like:
```python
{"text": "mocked response", "session_id": "test-sid", "provider": "claude",
 "version": "1.0", "timestamp": "2024-01-01T00:00:00", "raw_response": {}}
```
instead of mocking `ask_llm` to return `"mocked response"`.

## Test Updates

This step IS the test update. All test modifications happen here so that Step 1b (removing `ask_llm`) can land cleanly.
