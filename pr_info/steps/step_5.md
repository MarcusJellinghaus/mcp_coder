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

- `_ollama_preflight()` is a **private helper inline in
  `__init__.py`** — do NOT create a new module for it (keeps the
  module surface small and matches `summary.md`).
- It is called at the top of `_ask_agent()` AND at the top of
  `_ask_agent_stream()` (synchronously, before the thread/queue
  bridge in the stream variant).
- **Ordering inside `_ask_agent` / `_ask_agent_stream`:** the
  pre-flight call is placed **AFTER** the existing
  `_check_agent_dependencies()` call but **BEFORE**
  `_create_chat_model(config)` / agent construction. Rationale:
  otherwise an Ollama-configured user without `langgraph` installed
  would get the model-tool-capability error rather than the more
  actionable "install langgraph" `ImportError`. The dependency check
  always wins on missing-dependency errors.
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
  - `_ask_agent_stream` — the function is a generator, so the
    `ValueError` propagates when iteration begins. This is generator
    semantics and is intentional: do NOT refactor the function to
    eager-raise (no eager wrapper is needed). The error surfaces as
    soon as the caller starts iterating, which is before the
    thread/queue bridge spins up.

## ALGORITHM

```
def _ask_agent(question, config, ...):
    _check_agent_dependencies()  # existing — wins on missing langgraph
    _ollama_preflight(config)    # NEW — raises ValueError if capability missing
    # ... existing body (model creation, agent construction, run) unchanged ...

def _ask_agent_stream(question, config, ...):
    _check_agent_dependencies()  # existing — wins on missing langgraph
    _ollama_preflight(config)    # NEW — raises ValueError if capability missing
    # ... existing body (model creation, thread/queue bridge, run) unchanged ...
```

Ordering matters: `_check_agent_dependencies()` first (so users
missing `langgraph` get the actionable "install langgraph" error
rather than a tool-capability error), `_ollama_preflight(config)`
second, `_create_chat_model(config)` / agent construction third.

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
  - **Assert no thread is started.** Patch `threading.Thread` (the
    name used by the streaming code path) and assert it was NOT
    called when the generator is iterated and raises. The intent is
    to verify the capability failure surfaces before any background
    work begins. Adjust the exact patch target / mechanism to fit the
    streaming code's actual structure (e.g. `patch(
    "mcp_coder.llm.providers.langchain.threading.Thread")`), but the
    assertion semantics remain: generator raises before any thread
    spins up.

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
