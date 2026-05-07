# Step 3 — `log_file_path` in `store_session()` metadata

## LLM Prompt

> Read `pr_info/steps/summary.md` for context, then implement this step
> (`pr_info/steps/step_3.md`) with strict TDD. Tests first, then code.
> Run pylint, pytest, mypy via the mandatory MCP tools. Single commit.

## WHERE

- Modify: `src/mcp_coder/llm/storage/session_storage.py`
- Modify: `src/mcp_coder/icoder/core/app_core.py` (caller passes the new arg)
- Update tests:
  - `tests/llm/storage/test_session_storage.py` — new test for the field
  - `tests/icoder/test_app_core.py` — assert `stream_llm` passes the
    current event-log path to `store_session`

## WHAT

```python
# session_storage.py
def store_session(
    response_data: LLMResponseDict,
    prompt: str,
    store_path: Optional[str] = None,
    step_name: Optional[str] = None,
    branch_name: Optional[str] = None,
    log_file_path: Optional[str] = None,        # NEW
) -> str:
    """... if log_file_path is given, recorded under metadata.log_file_path."""
```

In `app_core.stream_llm()`:

```python
store_session(
    response_data,
    text,
    log_file_path=str(self._event_log.current_path),    # NEW
)
```

## HOW

- Append `log_file_path` to the existing `metadata: dict[str, Any]`
  block only when not `None` (matches existing pattern for
  `branch_name`/`step_name`).
- The kwarg is keyword-only by convention (last positional param after
  many existing optionals). All existing call sites pass earlier
  arguments; this addition is non-breaking.

## ALGORITHM

```
store_session(...):
    metadata = {timestamp, working_directory, model}
    if branch_name: metadata["branch_name"] = branch_name
    if step_name:   metadata["step_name"] = step_name
    if log_file_path: metadata["log_file_path"] = log_file_path  # NEW
    ...
```

## DATA

- Response JSON gains `metadata.log_file_path: str` (absolute or relative
  path string of the event-log JSONL).
- `app_core.stream_llm` now references `self._event_log.current_path`
  (added in Step 1).

## Test Cases

1. `store_session` test: pass `log_file_path="/tmp/x.jsonl"`, parse the
   written JSON file, assert `metadata["log_file_path"] ==
   "/tmp/x.jsonl"`.
2. `store_session` test: omit `log_file_path`, assert
   `"log_file_path" not in metadata`.
3. AppCore test: with a real `EventLog` in `tmp_path` and a `FakeLLMService`,
   call `app_core.stream_llm("hi")`, exhaust the iterator, then read the
   stored response JSON (`tmp_path/.mcp-coder/responses/...`) and assert
   `metadata["log_file_path"]` matches `event_log.current_path`. (Use a
   `monkeypatch` of `os.getcwd` or pass `store_path` if the existing
   helper supports it; otherwise verify via the function's return value.)

## Out of Scope

- Reading the field back during resume — Step 11.
- Refusing to resume on missing field — Step 11.
