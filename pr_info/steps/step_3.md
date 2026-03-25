# Step 3: Wire Context Manager into `prompt_llm()`

## Context

See `pr_info/steps/summary.md` for full context. This is step 3 of 6 for issue #551.

Wire the `mlflow_conversation` context manager (from Step 2) into `prompt_llm()` so every LLM call gets automatic MLflow logging.

## LLM Prompt

```
You are implementing step 3 of issue #551 (see pr_info/steps/summary.md for full context).
Step 2 created mlflow_conversation_logger.py. Now wire it into prompt_llm().

Task: Modify src/mcp_coder/llm/interface.py to wrap provider calls with the
mlflow_conversation context manager.

1. Write/update tests FIRST:
   - In tests/llm/test_interface.py (or create if needed): add test that prompt_llm()
     calls mlflow_conversation context manager
   - Test that response_data is set on the yielded dict after successful call
   - Test that exceptions propagate correctly (context manager sees the error)
   - Mock the context manager and provider to avoid real calls

2. Modify prompt_llm() in interface.py:
   - Import mlflow_conversation from .mlflow_conversation_logger
   - Wrap the Claude and LangChain provider calls with the context manager
   - Set result["response_data"] = response after provider returns
   - Build metadata dict with model, working_directory, branch_name

3. Run all quality checks (pylint, mypy, pytest) and fix any issues.
```

## WHERE: Files to Modify

- `src/mcp_coder/llm/interface.py` — wrap provider calls
- `tests/llm/test_interface.py` — add tests for auto-logging integration

## WHAT: Changes to `prompt_llm()`

```python
from .mlflow_conversation_logger import mlflow_conversation

def prompt_llm(question, provider="claude", session_id=None, timeout=...,
               env_vars=None, execution_dir=None, mcp_config=None, branch_name=None):
    # ... existing validation ...

    metadata = {"branch_name": branch_name, "working_directory": execution_dir}

    with mlflow_conversation(question, provider, session_id, metadata) as mlflow_ctx:
        # ... existing provider dispatch (Claude / LangChain) ...
        response = _call_provider(...)  # existing code, restructured
        mlflow_ctx["response_data"] = response

    return response
```

## ALGORITHM: Integration Pseudocode

```python
def prompt_llm(question, provider, session_id, timeout, ...):
    validate_inputs()
    provider = os.environ.get("MCP_CODER_LLM_PROVIDER") or provider
    metadata = {"branch_name": branch_name, "working_directory": execution_dir}

    with mlflow_conversation(question, provider, session_id, metadata) as mlflow_ctx:
        if provider == "langchain":
            response = ask_langchain(question, session_id, timeout, ...)
        elif provider == "claude":
            response = ask_claude_code_cli(question, session_id, timeout, ...)
        else:
            raise ValueError(...)
        mlflow_ctx["response_data"] = response
    return response
```

The existing timeout error handling (logging + re-raise) stays inside the `with` block so the context manager's `finally` sees the exception.

## HOW: Integration Points

- `mlflow_conversation` imported from `.mlflow_conversation_logger`
- Context manager wraps the entire provider call section
- Timeout exceptions (TimeoutExpired, asyncio.TimeoutError) propagate through the context manager — Phase 2 logs them as FAILED

## DATA: No Changes to Return Type

`prompt_llm()` still returns `LLMResponseDict`. The context manager is transparent to callers.

## Key Considerations

- Error logging (logger.error for timeouts) stays inside the `with` block
- The `with` block replaces the current try/except structure — same behavior, just wrapped
- `ValueError` for unsupported provider should be raised BEFORE entering the context manager (no MLflow run needed for input validation errors)
