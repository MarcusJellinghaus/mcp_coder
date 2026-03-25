# Step 2: Create `mlflow_conversation_logger.py` — Two-Phase Context Manager

## Context

See `pr_info/steps/summary.md` for full context. This is step 2 of 6 for issue #551.

This step creates the new centralized MLflow logging module. It is a thin orchestration layer over the existing `MLflowLogger` singleton — no new MLflow logic, just calling existing methods in the right order (Phase 1 before LLM call, Phase 2 after).

## LLM Prompt

```
You are implementing step 2 of issue #551 (see pr_info/steps/summary.md for full context).

Task: Create src/mcp_coder/llm/mlflow_conversation_logger.py with a context manager for
two-phase MLflow logging, and comprehensive tests.

1. Write tests FIRST in tests/llm/test_mlflow_conversation_logger.py:
   - Test happy path: Phase 1 logs prompt, Phase 2 logs response + ends run FINISHED
   - Test error path: exception during yield → Phase 2 logs error + ends run FAILED
   - Test MLflow disabled: context manager is a no-op, yields normally
   - Test session reuse: passing session_id reuses existing MLflow run
   - Test Phase 2 failure: if Phase 2 logging itself fails, warning is logged but no exception
   - Mock get_mlflow_logger() to avoid needing real MLflow

2. Create src/mcp_coder/llm/mlflow_conversation_logger.py:
   - Import contextmanager from contextlib, get_mlflow_logger from .mlflow_logger
   - Implement mlflow_conversation() context manager
   - Keep it simple: ~40-60 lines total

3. Run all quality checks (pylint, mypy, pytest) and fix any issues.
```

## WHERE: Files to Create

- `src/mcp_coder/llm/mlflow_conversation_logger.py` (~40-60 lines)
- `tests/llm/test_mlflow_conversation_logger.py` (~100-150 lines)

## WHAT: Main Function Signature

```python
@contextmanager
def mlflow_conversation(
    prompt: str,
    provider: str,
    session_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> Generator[dict[str, Any], None, None]:
```

## ALGORITHM: Core Logic (Pseudocode)

```python
@contextmanager
def mlflow_conversation(prompt, provider, session_id=None, metadata=None):
    logger = get_mlflow_logger()
    if not logger.config.enabled:
        yield {"response_data": None}    # no-op when disabled
        return

    # Phase 1: log prompt (survives timeout/kill)
    run_name = f"{provider}_{'resuming' if session_id and logger.has_session(session_id) else 'new'}"
    logger.start_run(session_id=session_id, run_name=run_name, tags={...})
    logger.log_params({"provider": provider, "prompt_length": len(prompt), ...})
    logger.log_artifact(prompt, "prompt.txt")

    result = {"response_data": None, "error": None}
    try:
        yield result              # caller sets result["response_data"]
    except Exception as exc:
        result["error"] = exc
        raise
    finally:
        # Phase 2: log response or error
        try:
            if result["response_data"]:
                logger.log_conversation(prompt, result["response_data"], metadata or {})
                response_sid = result["response_data"].get("session_id")
                logger.end_run("FINISHED", session_id=response_sid)
            elif result["error"]:
                logger.log_error_metrics(result["error"])
                logger.end_run("FAILED", session_id=session_id)
            else:
                logger.end_run("KILLED", session_id=session_id)  # process killed mid-yield
        except Exception:
            logging.warning("Phase 2 MLflow logging failed", exc_info=True)
```

## DATA: Yielded Dict Structure

```python
{"response_data": None | LLMResponseDict, "error": None | Exception}
```

The caller sets `result["response_data"] = response` after the provider call succeeds. The context manager reads it in the `finally` block.

## HOW: Integration Points

- Imports `get_mlflow_logger` from `mcp_coder.llm.mlflow_logger` (existing singleton)
- Uses existing `MLflowLogger` methods: `start_run`, `log_params`, `log_artifact`, `log_conversation`, `log_error_metrics`, `end_run`
- Will be wired into `prompt_llm()` in Step 3

## Key Design Choices

- **Context manager, not class**: Simplest possible API for wrapping a call
- **Yields a mutable dict**: Caller sets response_data; finally-block reads it
- **No new MLflow logic**: Pure orchestration of existing `MLflowLogger` methods
- **Graceful degradation**: If MLflow disabled, yields immediately (no-op)
- **Phase 2 never raises**: Wrapped in try/except with warning log
