# Step 4: Update `_log_to_mlflow()` in `prompt.py`

## Context
See [summary.md](summary.md) for the full design.
Steps 1, 2, and 3 must be complete before this step.

This step updates `_log_to_mlflow()` in `prompt.py` to use the session map.
After Steps 1–3, the MLflow run has already been closed (with metrics) by the time
`_log_to_mlflow()` is called. This step resumes that run to add params and artifacts.

---

## WHERE

| Role | Path |
|------|------|
| Tests | `tests/cli/commands/test_prompt.py` — add new test class `TestLogToMlflow` |
| Implementation | `src/mcp_coder/cli/commands/prompt.py` — `_log_to_mlflow()` only |

---

## WHAT

### Revised `_log_to_mlflow()` logic

```python
def _log_to_mlflow(response_data, prompt, project_dir, branch_name=None, step_name=None):
    try:
        mlflow_logger = get_mlflow_logger()
        if not mlflow_logger.config.enabled:
            return

        # [existing metadata / model extraction — unchanged]

        response_dict: Dict[str, Any] = dict(response_data)
        response_sid = response_data.get("session_id")        # NEW

        if response_sid and mlflow_logger.has_session(response_sid):  # NEW — normal path
            # Resume closed run; metrics are already logged
            mlflow_logger.start_run(session_id=response_sid)
            mlflow_logger.log_conversation_artifacts(prompt, response_dict, metadata)
            mlflow_logger.end_run("FINISHED")
        else:                                                          # NEW — edge/fallback path
            # No mapping found: start a fresh run with full logging.
            # Note: log_llm_response() (Step 2) already closed the previous run,
            # so the metrics from that run exist separately. This new run will
            # duplicate those metrics — acceptable for this rare edge case.
            if response_sid:
                logger.debug(
                    f"Session {response_sid} not in MLflow map — "
                    "starting fresh run (metrics may appear in a separate run)"
                )
            mlflow_logger.start_run()
            mlflow_logger.log_conversation(prompt, response_dict, metadata)
            mlflow_logger.end_run("FINISHED")

        logger.debug("Logged conversation to MLflow")

    except Exception as e:
        logger.debug(f"Failed to log conversation to MLflow: {e}")
        try:
            mlflow_logger.end_run("FAILED")
        except Exception:
            pass
```

### What is removed
- The single `mlflow_logger.end_run("FINISHED")` call that previously sat alone at
  the end of the `try` block (it's now inside each conditional branch)
- The single `mlflow_logger.log_conversation(...)` call (it's now inside the `else` branch)

### What is unchanged
- All metadata/model extraction logic
- The outer `try/except` structure
- The `if not mlflow_logger.config.enabled: return` guard
- All call sites in `execute_prompt()` that call `_log_to_mlflow()` — their signatures
  are unchanged

---

## HOW

### Integration points
- `get_mlflow_logger` is already imported in `prompt.py` (no new imports needed)
- `mlflow_logger.has_session()` and `mlflow_logger.log_conversation_artifacts()` are
  added in Step 1
- `mlflow_logger.start_run(session_id=...)` resume behaviour added in Step 1
- `response_data.get("session_id")` always exists in `LLMResponseDict` (may be `None`)

### Normal-path vs edge-path

| Condition | Path | Why |
|-----------|------|-----|
| `response_sid` is set AND in LRU map | Resume run → `log_conversation_artifacts()` | Typical prompt command flow |
| `response_sid` is `None` | Fresh run → `log_conversation()` | Claude omitted session_id (rare) |
| `response_sid` set but NOT in map | Fresh run → `log_conversation()` | LRU eviction (>100 concurrent sessions) |

---

## ALGORITHM

```
get mlflow_logger; if disabled return early
extract model, build metadata dict   [unchanged]
response_sid = response_data.get("session_id")
if response_sid and has_session(response_sid):
    start_run(session_id=response_sid)          # resume via run_id
    log_conversation_artifacts(prompt, ...)     # params + artifacts only
else:
    start_run()                                 # new run
    log_conversation(prompt, ...)               # full: params + metrics + artifacts
end_run("FINISHED")
```

---

## DATA

- `response_sid: str | None` — extracted from `response_data.get("session_id")`
- When resuming: `log_conversation_artifacts()` receives the same `prompt`,
  `response_dict`, `metadata` as `log_conversation()` would have
- `start_run(session_id=response_sid)` returns the resumed run_id (stored in
  `mlflow_logger.active_run_id`), allowing `log_conversation_artifacts()` to write
  to the correct run

---

## TESTS — new `TestLogToMlflow` class in `test_prompt.py`

Write these tests **first**, then implement.

Each test patches `get_mlflow_logger` directly on `prompt.py`'s import namespace
(`mcp_coder.cli.commands.prompt.get_mlflow_logger`) and patches `prompt_llm` to
return a controlled `LLMResponseDict`.

### Test 1 — known session: `start_run(session_id=...)` + `log_conversation_artifacts` + `end_run`
```
mock_mlflow_logger.config.enabled = True
mock_mlflow_logger.has_session("sid-1") returns True

Call execute_prompt with output_format="just-text" (or via _log_to_mlflow directly)
→ response_data["session_id"] = "sid-1"

Assert:
  mock_mlflow_logger.start_run.called_with(session_id="sid-1")
  mock_mlflow_logger.log_conversation_artifacts.called_once()
  mock_mlflow_logger.log_conversation.not_called()
  mock_mlflow_logger.end_run.called_with("FINISHED")
```

### Test 2 — unknown session (not in map): `start_run()` + `log_conversation` + `end_run`
```
mock_mlflow_logger.config.enabled = True
mock_mlflow_logger.has_session("sid-2") returns False

response_data["session_id"] = "sid-2"

Assert:
  mock_mlflow_logger.start_run.called_with()   # no session_id arg
  mock_mlflow_logger.log_conversation.called_once()
  mock_mlflow_logger.log_conversation_artifacts.not_called()
  mock_mlflow_logger.end_run.called_with("FINISHED")
```

### Test 3 — session_id is None: fresh run path
```
mock_mlflow_logger.config.enabled = True
response_data["session_id"] = None

Assert:
  has_session not called (guarded by `if response_sid`)
  mock_mlflow_logger.start_run called without session_id
  mock_mlflow_logger.log_conversation.called_once()
  mock_mlflow_logger.log_conversation_artifacts.not_called()
```

### Test 4 — MLflow disabled: nothing is called
```
mock_mlflow_logger.config.enabled = False

Call _log_to_mlflow()

Assert: start_run, log_conversation, log_conversation_artifacts, end_run — none called
```

### Test 5 — Exception during logging: end_run("FAILED") is attempted
```
mock_mlflow_logger.config.enabled = True
mock_mlflow_logger.has_session("sid-1") returns True
mock_mlflow_logger.start_run raises Exception("resume failed")

Call _log_to_mlflow()

Assert: end_run.called_with("FAILED")
        execute_prompt still returns 0 (mlflow failure is silent)
```

---

## LLM Prompt

```
You are implementing Step 4 of GitHub issue #491 "Fix MLflow 'already active run' warning".

Read pr_info/steps/summary.md for full context and design.
Steps 1, 2, and 3 must already be complete.

Your task: rewrite `_log_to_mlflow()` in `src/mcp_coder/cli/commands/prompt.py`
and add a new `TestLogToMlflow` class to `tests/cli/commands/test_prompt.py`.

Follow TDD: write the 5 tests FIRST, then implement.

--- Implementation change ---
In `_log_to_mlflow()`, after building `metadata` and `response_dict` (unchanged),
add:
    response_sid = response_data.get("session_id")

Then replace the single `mlflow_logger.log_conversation(...)` + `mlflow_logger.end_run(...)`
calls with a conditional:

    if response_sid and mlflow_logger.has_session(response_sid):
        mlflow_logger.start_run(session_id=response_sid)
        mlflow_logger.log_conversation_artifacts(prompt, response_dict, metadata)
        mlflow_logger.end_run("FINISHED")
    else:
        # `start_run()` is required in BOTH branches because log_llm_response()
        # (Step 2) always closes the run before _log_to_mlflow() is called.
        # In the else-path, the previous run (metrics only) is already closed;
        # this new run logs everything, which duplicates metrics for rare edge cases.
        if response_sid:
            logger.debug(
                f"Session {response_sid} not in MLflow map — "
                "starting fresh run (metrics may appear in a separate run)"
            )
        mlflow_logger.start_run()
        mlflow_logger.log_conversation(prompt, response_dict, metadata)
        mlflow_logger.end_run("FINISHED")

Keep the outer try/except and the `logger.debug("Logged conversation to MLflow")`
line intact. Remove the old standalone `mlflow_logger.end_run("FINISHED")` call
(it is now inside each branch). Do not change any other function in prompt.py.

--- Tests ---
Add `TestLogToMlflow` class in test_prompt.py. Each test:
- Patches `mcp_coder.cli.commands.prompt.get_mlflow_logger` to return a Mock
- Patches `mcp_coder.cli.commands.prompt.prompt_llm` to return a dict with the
  desired `session_id`
- Calls `execute_prompt(args)` (or calls `_log_to_mlflow()` directly) and asserts
  the correct MLflowLogger methods were (or were not) called.

See the 5 test descriptions in step_4.md.

Run the tests after implementation:
    pytest tests/cli/commands/test_prompt.py -v
    pytest tests/llm/test_mlflow_logger.py tests/llm/providers/claude/test_logging_utils.py -v
```
