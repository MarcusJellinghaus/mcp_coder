# Step 5: Add MLflow logging to LangChain text mode

## Context
See [summary.md](./summary.md) and [Decisions.md](./Decisions.md).

`_ask_text()` in `langchain/__init__.py` does zero MLflow logging. The agent-mode path has `_log_agent_mlflow()`. Text mode needs an equivalent so that all LangChain calls are visible in MLflow, regardless of whether MCP tools are configured.

---

## LLM Prompt

```
Read pr_info/steps/summary.md, pr_info/steps/Decisions.md, and pr_info/steps/step_5.md.

Implement step 5: add MLflow logging to LangChain text mode.

1. Write tests first in tests/llm/providers/langchain/test_langchain_text_mlflow.py
2. Add _log_text_mlflow() to src/mcp_coder/llm/providers/langchain/__init__.py
3. Call it from _ask_text() after the model responds
4. Run pytest, pylint, mypy, ruff to confirm all checks pass.
```

---

## WHERE

| Item | Path |
|------|------|
| Modified source | `src/mcp_coder/llm/providers/langchain/__init__.py` |
| New tests | `tests/llm/providers/langchain/test_langchain_text_mlflow.py` |

---

## WHAT

### New function: `_log_text_mlflow()`

```python
def _log_text_mlflow(
    config: dict[str, str | None],
    session_id: str,
) -> None:
    """Log text-mode params to MLflow (mirrors _log_agent_mlflow for agent mode)."""
```

### Call site in `_ask_text()`

Insert after `chat_model.invoke()` succeeds, before building the return dict:

```python
_log_text_mlflow(config, sid)
```

---

## HOW

- Import `get_mlflow_logger` is already at top of `__init__.py`
- Follow the same pattern as `_log_agent_mlflow()`: try/except wrapping, debug logging on failure
- The run started here will be enriched by `_log_to_mlflow()` in `prompt.py` (which checks `has_session()` or `active_run_id`)

### Run lifecycle

`_log_text_mlflow()` starts a run and ends it with `session_id`. Later, `_log_to_mlflow()` in `prompt.py` will find the session via `has_session()`, resume the run, add artifacts, and close it again. This is the same lifecycle as agent mode.

---

## ALGORITHM

```
def _log_text_mlflow(config, session_id):
    try:
        mlflow_logger = get_mlflow_logger()
        mlflow_logger.start_run(session_id=session_id)
        mlflow_logger.log_params(backend=, model=, mode="text")
        mlflow_logger.end_run(session_id=session_id)
    except Exception:
        logger.debug("MLflow logging failed for text mode", exc_info=True)
```

---

## DATA

### Params logged

| Param | Value |
|-------|-------|
| `backend` | `config.get("backend", "")` |
| `model` | `config.get("model", "")` |
| `mode` | `"text"` |

No metrics or artifacts at the provider level — `_log_to_mlflow()` in `prompt.py` handles the full conversation logging.

---

## TESTS

### `test_langchain_text_mlflow.py`

```python
class TestLogTextMlflow:
    def test_logs_params_and_ends_run(self):
        """_log_text_mlflow starts run, logs params, ends run."""

    def test_exception_is_swallowed(self):
        """MLflow errors don't propagate to caller."""

    def test_ask_text_calls_log_text_mlflow(self):
        """_ask_text() calls _log_text_mlflow() after successful invoke."""

    def test_ask_text_skips_logging_on_invoke_failure(self):
        """_ask_text() does not call _log_text_mlflow() if chat_model.invoke raises."""
```
