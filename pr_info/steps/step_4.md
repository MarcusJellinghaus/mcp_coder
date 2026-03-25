# Step 4: Remove MLflow from Claude Provider (`logging_utils.py`)

## Context

See `pr_info/steps/summary.md` for full context. This is step 4 of 6 for issue #551.

After Step 3, `prompt_llm()` handles all MLflow logging centrally. The Claude provider's MLflow calls in `logging_utils.py` are now redundant and create duplicate logging. Remove them, keeping only the `logging.debug()` output.

## LLM Prompt

```
You are implementing step 4 of issue #551 (see pr_info/steps/summary.md for full context).
Steps 2-3 centralized MLflow logging in prompt_llm(). Now remove the redundant
MLflow logging from the Claude provider.

Task: Remove MLflow calls from src/mcp_coder/llm/providers/claude/logging_utils.py,
keeping debug logging intact.

1. Update tests FIRST:
   - In tests for logging_utils (find them): remove assertions about MLflow calls
     (start_run, log_metrics, end_run) from log_llm_request, log_llm_response, log_llm_error
   - Keep assertions about logging.debug calls
   - Run tests to see them fail (code still has MLflow calls)

2. Modify logging_utils.py:
   - Remove the MLflow import block at top (try/except importing get_mlflow_logger)
   - Remove the _mlflow_available flag
   - In log_llm_request(): remove the MLflow start_run block at the end
   - In log_llm_response(): remove the MLflow log_metrics and end_run block at the end
   - In log_llm_error(): remove the MLflow log_error_metrics and end_run block at the end
   - Keep ALL logging.debug() calls unchanged

3. Run all quality checks (pylint, mypy, pytest) and fix any issues.
```

## WHERE: Files to Modify

- `src/mcp_coder/llm/providers/claude/logging_utils.py` — remove MLflow code
- `tests/llm/providers/claude/test_logging_utils.py` (or similar) — update tests

## WHAT: Deletions in `logging_utils.py`

### Remove from top of file:
```python
# DELETE THIS BLOCK:
try:
    from ...mlflow_logger import get_mlflow_logger
    _mlflow_available = True
except ImportError:
    _mlflow_available = False
    get_mlflow_logger = None
```

### Remove from `log_llm_request()`:
```python
# DELETE THIS BLOCK (at end of function):
if _mlflow_available and get_mlflow_logger is not None:
    try:
        mlflow_logger = get_mlflow_logger()
        run_name = f"{provider}_{session_status.strip('[]')}"
        tags = {...}
        mlflow_logger.start_run(run_name=run_name, tags=tags)
    except Exception as e:
        logger.debug(f"Failed to start MLflow run: {e}")
```

### Remove from `log_llm_response()`:
```python
# DELETE THIS BLOCK (at end of function):
if _mlflow_available and get_mlflow_logger is not None:
    try:
        mlflow_logger = get_mlflow_logger()
        metrics = {"duration_ms": float(duration_ms)}
        ...
        mlflow_logger.log_metrics(metrics)
        if session_id is not None:
            mlflow_logger.end_run("FINISHED", session_id=session_id)
    except Exception as e:
        logger.debug(f"Failed to log MLflow response metrics: {e}")
```

### Remove from `log_llm_error()`:
```python
# DELETE THIS BLOCK (at end of function):
if _mlflow_available and get_mlflow_logger is not None:
    try:
        mlflow_logger = get_mlflow_logger()
        mlflow_logger.log_error_metrics(error, duration_ms)
        mlflow_logger.end_run("FAILED")
    except Exception as e:
        logger.debug(f"Failed to log MLflow error: {e}")
```

## ALGORITHM: N/A

Pure deletion. No new logic.

## DATA: No Changes

Function signatures and debug logging output remain identical. Only MLflow side effects are removed.
