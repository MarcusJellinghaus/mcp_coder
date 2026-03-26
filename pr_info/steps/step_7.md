# Step 7: MLflow Logging in Streaming Path + Dead Code Cleanup

## LLM Prompt

> Read `pr_info/steps/summary.md` for full context. Implement Step 7: add MLflow logging to the streaming path in `execute_prompt()` and remove dead verbosity formatter functions. Run all three code quality checks (pylint, pytest, mypy) after changes. Commit as `fix(cli): add mlflow logging to streaming path, remove dead verbosity formatters`.

## WHERE

- **Modify**: `src/mcp_coder/cli/commands/prompt.py`
- **Modify**: `src/mcp_coder/llm/formatting/formatters.py`
- **Modify**: `src/mcp_coder/llm/formatting/__init__.py`
- **Modify**: `tests/cli/commands/test_prompt_streaming.py`

## WHAT

### In `prompt.py` (streaming path):
After the stream loop completes and `assembler.result()` produces the final `LLMResponseDict`, wrap the post-stream logging in `mlflow_conversation()` context manager — same pattern as the blocking `json` path.

### In `formatters.py`:
Remove dead functions: `format_text_response`, `format_verbose_response`, `format_raw_response`. Update module docstring to remove "verbosity levels" reference.

### In `formatting/__init__.py`:
Remove re-exports of the deleted functions.

### In `prompt.py` docstring:
Remove "optional verbosity" reference from module docstring.

## HOW

- Import `mlflow_conversation` in the streaming branch (same import as blocking path)
- After `response = assembler.result()`, wrap store/log operations:
  ```python
  with mlflow_conversation(args.prompt, provider):
      if getattr(args, "store_response", False):
          store_session(response, args.prompt, branch_name=branch_name)
  ```
- Grep for any remaining references to the deleted functions and remove them

## TEST CASES

1. `test_streaming_mlflow_logging` — mock `mlflow_conversation`, verify it is called after streaming completes
2. `test_dead_formatters_removed` — verify `format_text_response`, `format_verbose_response`, `format_raw_response` are not importable from `formatters`
