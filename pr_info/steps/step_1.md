# Step 1: Extend `MLflowLogger` with LRU Session Map

## Context
See [summary.md](summary.md) for the full design.

This step implements all changes to `MLflowLogger`:
- LRU `session_id → run_id` map (max 100 entries)
- `has_session()` — check if session is in map
- `log_conversation_artifacts()` — log params + artifacts, skip metrics
- Extend `start_run(session_id=None)` — resume run from map when session is known
- Extend `end_run(session_id=None)` — store mapping before clearing `active_run_id`

No other files are changed in this step.

---

## WHERE

| Role | Path |
|------|------|
| Tests (new class) | `tests/llm/test_mlflow_logger.py` — add `TestSessionMapBehavior` |
| Implementation | `src/mcp_coder/llm/mlflow_logger.py` |

---

## WHAT

### New / changed in `MLflowLogger`

```python
from collections import OrderedDict

class MLflowLogger:
    _MAX_SESSION_MAP_SIZE: int = 100          # class constant

    def __init__(self, config=None):
        ...
        self._session_run_map: OrderedDict[str, str] = OrderedDict()   # NEW

    def has_session(self, session_id: str) -> bool: ...                # NEW

    def log_conversation_artifacts(                                     # NEW
        self, prompt: str, response_data: Dict[str, Any],
        metadata: Dict[str, Any]
    ) -> None: ...

    def start_run(                                                      # EXTENDED
        self, session_id: Optional[str] = None,
        run_name: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None,
    ) -> Optional[str]: ...

    def end_run(                                                        # EXTENDED
        self, status: str = "FINISHED",
        session_id: Optional[str] = None,
    ) -> None: ...
```

---

## HOW

### Integration points
- `OrderedDict` import added at top of `mlflow_logger.py`
- `_session_run_map` initialised in `__init__` alongside `active_run_id`
- Existing callers of `start_run(run_name=..., tags=...)` are unaffected (keyword args)
- Existing callers of `end_run("FINISHED")` are unaffected (`session_id` defaults to `None`)
- `__all__` does not need updating (these are instance methods)

---

## ALGORITHM

### `end_run(status, session_id=None)` — LRU store before clearing run_id

```
if not enabled or not active_run_id: return early
if session_id is not None:
    remove session_id from map (if present) to reset LRU order
    map[session_id] = active_run_id          # insert at end (most recent)
    if len(map) > MAX_SIZE: map.popitem(last=False)   # evict LRU (first item)
call mlflow.end_run(status=status)
set active_run_id = None
```

### `start_run(session_id, run_name, tags)` — resume or create

```
if not enabled: return None
if session_id in map:
    map.move_to_end(session_id)              # LRU access update
    run = mlflow.start_run(run_id=map[session_id])
    active_run_id = run.info.run_id; return it
generate run_name if not provided
run = mlflow.start_run(run_name=run_name)
set tags, active_run_id = run.info.run_id; return it
```

### `log_conversation_artifacts(prompt, response_data, metadata)`

```
if not enabled or not active_run_id: return early
log_params({model, working_directory, branch_name, step_name, prompt_length})
log_artifact(prompt, "prompt.txt")
log_artifact(json.dumps({prompt, response_data, metadata}), "conversation.json")
```

---

## DATA

### `_session_run_map`
- Type: `OrderedDict[str, str]`
- Key: Claude `session_id` string
- Value: MLflow `run_id` string
- Capacity: 100 entries; LRU eviction on overflow
- OrderedDict ordering: most-recently-used at the **end**; LRU (oldest) at the **front**

### `log_conversation_artifacts` params logged
```python
{
    "model": metadata.get("model", "unknown"),
    "working_directory": metadata.get("working_directory"),
    "branch_name": metadata.get("branch_name"),
    "step_name": metadata.get("step_name"),
    "prompt_length": len(prompt),
}
```
Metrics (`duration_ms`, `cost_usd`, `usage_*`) are intentionally **not** logged here —
they are already in the run from `log_llm_response()`.

---

## TESTS — `TestSessionMapBehavior` (new class, existing tests untouched)

Write these tests **first**, then implement to make them pass.

### Test 1 — `has_session` returns `False` for unknown session
```
logger = MLflowLogger(enabled_config)
assert logger.has_session("nonexistent") is False
```

### Test 2 — `end_run(session_id=...)` stores mapping; `has_session` returns `True`
```
mock mlflow; logger.active_run_id = "run-abc"
logger.end_run("FINISHED", session_id="sid-1")
assert logger.has_session("sid-1") is True
assert "sid-1" in logger._session_run_map
assert logger._session_run_map["sid-1"] == "run-abc"
assert logger.active_run_id is None        # run was ended
```

### Test 3 — `start_run(session_id=...)` calls `mlflow.start_run(run_id=...)` when session is known
```
mock mlflow; mock_run.info.run_id = "run-abc"
logger._session_run_map["sid-1"] = "run-abc"

result = logger.start_run(session_id="sid-1")

assert result == "run-abc"
mock_mlflow.start_run.assert_called_once_with(run_id="run-abc")
# No run_name kwarg — it's a resume, not a new run
```

### Test 4 — `log_conversation_artifacts` logs params + artifacts, skips metrics
```
mock mlflow; logger.active_run_id = "run-x"
patch log_params, log_metrics, log_artifact as spies

logger.log_conversation_artifacts("prompt text", response_data, metadata)

log_params.assert_called_once()
params = log_params.call_args[0][0]
assert "model" in params and "prompt_length" in params
assert log_artifact.call_count == 2       # prompt.txt + conversation.json
log_metrics.assert_not_called()           # metrics excluded
```

### Test 5 — LRU eviction: 101st entry evicts the least recently used
```
mock mlflow; logger with enabled=True
for i in range(100):
    logger._session_run_map[f"sid-{i}"] = f"run-{i}"
logger.active_run_id = "run-100"
logger.end_run("FINISHED", session_id="sid-100")  # triggers real LRU eviction in end_run()

assert "sid-0" not in logger._session_run_map     # LRU evicted
assert logger.has_session("sid-100") is True      # newest kept
assert len(logger._session_run_map) == 100
```

Use `end_run()` to trigger eviction (not direct map manipulation) — this tests the
real eviction code path and catches bugs in `end_run()` itself.

### Test 6 — `end_run(session_id=None)` skips mapping (nothing stored)
```
mock mlflow; logger.active_run_id = "run-xyz"
logger.end_run("FINISHED", session_id=None)

assert len(logger._session_run_map) == 0   # map is still empty
assert logger.active_run_id is None        # run was still ended
```

---

## LLM Prompt

```
You are implementing Step 1 of GitHub issue #491 "Fix MLflow 'already active run' warning".

Read pr_info/steps/summary.md for full context and design.

Your task: extend `src/mcp_coder/llm/mlflow_logger.py` and add a new test class
`TestSessionMapBehavior` to `tests/llm/test_mlflow_logger.py`.

Follow TDD: write the 6 tests listed in step_1.md FIRST, then implement to make them pass.
Do not modify any existing tests in test_mlflow_logger.py.

Changes to mlflow_logger.py:
1. Import `OrderedDict` from `collections` at the top.
2. Add class constant `_MAX_SESSION_MAP_SIZE = 100`.
3. Add `self._session_run_map: OrderedDict[str, str] = OrderedDict()` in `__init__`.
4. Add `has_session(self, session_id: str) -> bool` — returns `session_id in self._session_run_map`.
5. Extend `start_run()` with `session_id: Optional[str] = None` as first param.
   - If `session_id` is in map: call `mlflow.start_run(run_id=stored_id)`, update LRU order, set `active_run_id`, return it.
   - Otherwise: existing behaviour unchanged.
6. Extend `end_run()` with `session_id: Optional[str] = None` as second param.
   - If `session_id` is not None and `active_run_id` is set: store in `_session_run_map` with LRU eviction (OrderedDict pattern: pop+re-insert, evict first if over 100).
   - Then call existing mlflow.end_run and clear active_run_id (unchanged).
7. Add `log_conversation_artifacts(self, prompt, response_data, metadata)` — calls `log_params` (model, working_directory, branch_name, step_name, prompt_length) and `log_artifact` twice (prompt.txt, conversation.json). Does NOT call `log_metrics`.

All changes must be backward-compatible: existing call sites `start_run(run_name=..., tags=...)` and `end_run("FINISHED")` continue to work unchanged.

Run the tests after implementation: pytest tests/llm/test_mlflow_logger.py -v
```
