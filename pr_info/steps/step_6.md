# Step 6: Remove `log_to_mlflow()` from Commands, Enhance Verify

## Context

See `pr_info/steps/summary.md` for full context. This is step 6 of 6 for issue #551.

After Steps 2-5, all MLflow logging happens automatically in `prompt_llm()`. The explicit `log_to_mlflow()` function in `prompt.py` and its calls in `prompt.py` and `verify.py` are now redundant — they would cause duplicate logging. Remove them and enhance the verify command to explicitly assert logged content.

## LLM Prompt

```
You are implementing step 6 of issue #551 (see pr_info/steps/summary.md for full context).
This is the final step. prompt_llm() now handles all MLflow logging automatically.

Task: Remove log_to_mlflow() from prompt.py, remove its usage from verify.py,
and enhance the verify MLflow check to assert logged content.

1. Update tests FIRST:
   - tests/cli/commands/test_prompt.py: remove all tests for log_to_mlflow() function.
     Tests for prompt execution should verify that prompt_llm is called (MLflow logging
     is now internal to prompt_llm, not the command's responsibility).
   - tests/cli/commands/test_verify.py: remove assertions about log_to_mlflow being called.
     Add test that verify checks MLflow run content (not just existence).

2. Modify src/mcp_coder/cli/commands/prompt.py:
   - Delete the entire log_to_mlflow() function definition (~50 lines)
   - Remove ALL calls to log_to_mlflow() throughout execute_prompt() 
     (there are 4 calls: session-id mode, json mode, just-text mode, verbose/raw mode)
   - Remove the import of get_mlflow_logger (if no longer needed)
   - Remove unused imports that were only used by log_to_mlflow()

3. Modify src/mcp_coder/cli/commands/verify.py:
   - Remove the import: `from .prompt import log_to_mlflow`
   - Remove the call to log_to_mlflow() after the test prompt
   - The test prompt's MLflow logging now happens automatically inside prompt_llm()
   - Enhance the MLflow verification section to check run content:
     After verify_mlflow(since=timestamp), if MLflow is enabled and tracking_data shows
     test prompt logged, optionally query for expected params (provider, prompt_length)
     using the existing mlflow_db_utils pattern.

4. Run all quality checks (pylint, mypy, pytest) and fix any issues.
```

## WHERE: Files to Modify

- `src/mcp_coder/cli/commands/prompt.py` — delete `log_to_mlflow()` and all calls
- `src/mcp_coder/cli/commands/verify.py` — remove import/call, enhance verification
- `tests/cli/commands/test_prompt.py` — remove log_to_mlflow tests
- `tests/cli/commands/test_verify.py` — update verification tests

## WHAT: Deletions in `prompt.py`

### Delete entirely:
- `log_to_mlflow()` function (~50 lines, lines 30-85 approximately)

### Remove all calls (4 occurrences in execute_prompt):
```python
# DELETE each of these lines:
log_to_mlflow(response_dict, args.prompt, project_dir)                     # session-id mode
log_to_mlflow(response_dict, args.prompt, project_dir, branch_name)        # json mode
log_to_mlflow(llm_response, args.prompt, project_dir, branch_name)         # just-text mode
log_to_mlflow(llm_response, args.prompt, project_dir, branch_name)         # verbose/raw mode
```

### Remove unused imports:
- `from ...llm.mlflow_logger import get_mlflow_logger` (if only used by log_to_mlflow)
- `from typing import Dict` (if only used by log_to_mlflow)
- `from datetime import datetime` (if only used by log_to_mlflow)

## WHAT: Changes in `verify.py`

### Remove:
```python
from .prompt import log_to_mlflow   # DELETE this import
```

### Remove call after test prompt:
```python
# DELETE this line:
log_to_mlflow(response, "Reply with OK", project_dir)
```

### Enhance verification (optional, if straightforward):
The existing `verify_mlflow(since=timestamp)` already checks for run existence via SQLite. Enhancement: extend `_format_tracking_data` or add a new check that queries for expected params on the logged run (e.g., confirm `provider` param exists). Keep this simple — if it requires significant new SQLite queries, defer to a follow-up.

## ALGORITHM: N/A

Primarily deletion. The verify enhancement is a minor addition to existing SQLite query logic.

## DATA: No Changes to Public APIs

`execute_prompt()` return type unchanged (int exit code). `execute_verify()` return type unchanged. The only behavioral change: MLflow logging happens inside `prompt_llm()` instead of after it returns.
