# Step 5: Remove MLflow from LangChain Provider, Pass Tool Trace via `raw_response`

## Context

See `pr_info/steps/summary.md` for full context. This is step 5 of 6 for issue #551.

After Step 3, `prompt_llm()` handles all MLflow logging centrally. The LangChain provider's `_log_text_mlflow()` and `_log_agent_mlflow()` are now redundant. However, `_log_agent_mlflow()` currently logs a `tool_trace.json` artifact — we need to ensure this data reaches the central logger via `raw_response`.

## LLM Prompt

```
You are implementing step 5 of issue #551 (see pr_info/steps/summary.md for full context).
Steps 2-3 centralized MLflow logging in prompt_llm(). Now remove the redundant
MLflow logging from the LangChain provider.

Task: Remove _log_text_mlflow() and _log_agent_mlflow() from 
src/mcp_coder/llm/providers/langchain/__init__.py. Ensure tool_trace data
is available in raw_response for the central logger.

1. Update tests FIRST:
   - Find LangChain provider tests and remove assertions about _log_text_mlflow 
     and _log_agent_mlflow being called
   - Add assertion that raw_response contains "tool_trace" key when agent mode is used
   - Run tests to see expected failures

2. Modify langchain/__init__.py:
   - Delete the _log_text_mlflow() function entirely
   - Delete the _log_agent_mlflow() function entirely
   - Remove the call to _log_text_mlflow() from _ask_text()
   - Remove the call to _log_agent_mlflow() from _ask_agent()
   - Remove the import of get_mlflow_logger (if no longer used elsewhere)
   - Verify that _ask_agent() already includes tool_trace in raw_response via **stats 
     (stats dict contains "tool_trace" key from the agent runner)
     If not, explicitly add: raw_response["tool_trace"] = stats.get("tool_trace", [])

3. In the central logger (mlflow_conversation_logger.py from Step 2):
   - In Phase 2, check if response_data["raw_response"] contains "tool_trace"
   - If so, log it as an artifact: logger.log_artifact(json.dumps(tool_trace), "tool_trace.json")
   - Add a test for this in test_mlflow_conversation_logger.py

4. Run all quality checks (pylint, mypy, pytest) and fix any issues.
```

## WHERE: Files to Modify

- `src/mcp_coder/llm/providers/langchain/__init__.py` — delete MLflow functions and calls
- `src/mcp_coder/llm/mlflow_conversation_logger.py` — add tool_trace artifact logging in Phase 2
- `tests/llm/test_mlflow_conversation_logger.py` — add tool_trace test
- `tests/llm/providers/langchain/test_*.py` — update tests

## WHAT: Deletions in `langchain/__init__.py`

### Delete entirely:
- `_log_text_mlflow()` function (~15 lines)
- `_log_agent_mlflow()` function (~25 lines)

### Remove calls:
- In `_ask_text()`: delete `_log_text_mlflow(config, session_id)` line
- In `_ask_agent()`: delete `_log_agent_mlflow(config, stats, session_id)` line

### Remove import (if unused):
- `from mcp_coder.llm.mlflow_logger import get_mlflow_logger`

### Verify tool_trace in raw_response:
The `_ask_agent()` function already does `raw_response = {..., **stats}` where `stats` contains `tool_trace`. Verify this is the case — if so, no change needed here.

## WHAT: Addition in `mlflow_conversation_logger.py`

In Phase 2 (finally block), after logging conversation:
```python
# Log tool trace artifact if present (LangChain agent mode)
tool_trace = response_data.get("raw_response", {}).get("tool_trace")
if tool_trace:
    logger.log_artifact(json.dumps(tool_trace, indent=2, default=str), "tool_trace.json")
```

## ALGORITHM: N/A

Mostly deletion. The only new logic is 3 lines to check for and log tool_trace artifact.

## DATA: raw_response Structure (Agent Mode)

```python
raw_response = {
    "messages": [...],
    "backend": "openai",
    "model": "gpt-4",
    "agent_steps": 3,
    "total_tool_calls": 5,
    "tool_trace": [{"tool": "read_file", "args": {...}, "result": "..."}],  # already present via **stats
}
```

The central logger reads `raw_response["tool_trace"]` and logs it as `tool_trace.json` artifact.
