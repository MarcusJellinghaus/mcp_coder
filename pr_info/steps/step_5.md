# Step 5 — Agent pre-flight capability check

This step reuses the `check_ollama_tool_capability()` helper landed in
Step 4 inside `_ask_agent()` and `_ask_agent_stream()` in
`__init__.py`. When `backend == "ollama"` the helper is called BEFORE
`run_agent()` / `run_agent_stream()` (which is where
`create_react_agent` is invoked); on failure a clear error is raised
so no LLM round-trip is wasted.

The pre-flight lives in `__init__.py`, NOT `agent.py`, so `agent.py`
stays backend-agnostic.

## WHERE

**Modify:**
- `src/mcp_coder/llm/providers/langchain/__init__.py`:
  - `_ask_agent()` — call the helper when `config.get("backend") ==
    "ollama"`, raise `ValueError(cap["value"])` if not ok.
  - `_ask_agent_stream()` — same check before the thread / queue
    bridge spins up. The check runs synchronously on the calling
    thread; if it raises, the iterator never starts.

**Create:**
- `tests/llm/providers/langchain/test_langchain_ollama_agent.py` —
  agent pre-flight tests scoped to Ollama.

## WHAT

A small private helper, kept inline in `__init__.py` to avoid
introducing a new module:

```python
def _ollama_preflight(config: dict[str, str | None]) -> None:
    """Raise ValueError if Ollama tools capability is missing."""
```

## HOW

- `_ollama_preflight()` is called at the top of `_ask_agent()` AND at
  the top of `_ask_agent_stream()` (synchronously, before the
  thread/queue bridge in the stream variant).
- It is a no-op when `config["backend"] != "ollama"`.
- When `backend == "ollama"`:
  ```python
  from ._models import check_ollama_tool_capability
  cap = check_ollama_tool_capability(
      model=config.get("model") or "",
      api_key=os.getenv("OLLAMA_API_KEY") or config.get("api_key"),
      endpoint=config.get("endpoint"),
  )
  if not cap["ok"]:
      raise ValueError(cap["value"])
  ```
- The raised `ValueError` propagates naturally through the existing
  exception handling in both functions:
  - `_ask_agent` lets `ValueError` propagate out (no wrapping).
  - `_ask_agent_stream` lets `ValueError` propagate out of the
    generator before the thread is started.

## ALGORITHM

```
def _ask_agent(question, config, ...):
    _ollama_preflight(config)   # raises ValueError if capability missing
    # ... existing body unchanged ...

def _ask_agent_stream(question, config, ...):
    _ollama_preflight(config)   # raises ValueError if capability missing
    # ... existing body unchanged ...
```

## DATA

- No new return values.
- `_ollama_preflight()` returns `None` on success.
- Raises `ValueError` with the wording produced by
  `check_ollama_tool_capability()` (same string a verify run would
  print).

## Tests (write FIRST, TDD)

`tests/llm/providers/langchain/test_langchain_ollama_agent.py`:

- `test_ask_agent_raises_when_ollama_capability_missing`:
  - Patch `check_ollama_tool_capability` to return
    `{"ok": False, "value": "model 'foo' does not advertise..."}`.
  - Call `_ask_agent(question="x", config={"backend": "ollama",
    "model": "foo", ...}, ...)`.
  - Assert `ValueError` raised, message matches the capability dict's
    `value`.
  - Assert `run_agent` was NOT called (mock it, assert
    `assert_not_called()`).

- `test_ask_agent_proceeds_when_ollama_capability_ok`:
  - Patch helper to return `{"ok": True, ...}`.
  - Patch `run_agent` to return a stub tuple.
  - Assert `run_agent` was called.

- `test_ask_agent_does_not_call_capability_for_non_ollama_backends`:
  - `backend="openai"` — patch helper, assert `assert_not_called()`.

- `test_ask_agent_stream_raises_when_ollama_capability_missing`:
  - Same shape as `_ask_agent` test but consume the iterator
    (`list(...)`); the `ValueError` should propagate when iteration
    begins, before any thread spins up.

- `test_ask_agent_stream_proceeds_when_ollama_capability_ok`:
  - Patch helper + `run_agent_stream` (or the queue.Queue path) and
    confirm the underlying stream runs.

- `test_ask_agent_stream_does_not_call_capability_for_non_ollama`:
  - `backend="anthropic"` — helper not called.

## Definition of done

- All pre-flight tests pass.
- Existing `_ask_agent` / `_ask_agent_stream` tests still pass — the
  pre-flight is a no-op for non-Ollama backends, so other tests don't
  need new mocking.
- A user with an un-tools-capable Ollama model now sees a clear error
  immediately when invoking agent mode, instead of a late LangGraph
  failure.
- All three MCP code-quality checks pass.

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_5.md.

Implement Step 5 only. Follow TDD: create
tests/llm/providers/langchain/test_langchain_ollama_agent.py with the
six tests FIRST, then add the _ollama_preflight() helper and call
sites in src/mcp_coder/llm/providers/langchain/__init__.py.

Do NOT touch agent.py. The pre-flight runs in __init__.py at the
top of _ask_agent() and _ask_agent_stream() (synchronously, before
the thread/queue bridge in the stream variant).

Reuse the helper from Step 4 — check_ollama_tool_capability() — and
raise ValueError(cap["value"]) so the wording matches the verify
output.

The pre-flight MUST be a no-op when config["backend"] != "ollama".
Confirm with a dedicated test that the helper is not called for
non-Ollama backends.

After the edits, run all three MCP code-quality checks and confirm
zero issues before reporting the step complete.
```
