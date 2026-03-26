# Step 3: Replace Agent Fallback with Thread+Queue Bridge (with Timeout and Cancellation)

**Commit message:** `feat(langchain): replace agent streaming fallback with real streaming`

**References:** [summary.md](summary.md) — "Async-to-Sync Bridge" and "Timeout Strategy" sections

## LLM Prompt

> Implement Step 3 from `pr_info/steps/step_3.md`.
> Read `pr_info/steps/summary.md` for full context (issue #603).
> Read the existing code in `src/mcp_coder/llm/providers/langchain/__init__.py` and
> `tests/llm/providers/langchain/test_langchain_streaming.py` before making changes.
> Also read `src/mcp_coder/llm/providers/langchain/agent.py` for `run_agent_stream()` added in Step 2.
> Follow TDD: write tests first, then implement, then run all three checks.

## WHERE

- `tests/llm/providers/langchain/test_langchain_streaming.py` — replace `TestAskLangchainStreamAgentFallback`, add new tests
- `src/mcp_coder/llm/providers/langchain/__init__.py` — modify `ask_langchain_stream()` agent branch

## WHAT — Tests (Replace + Add)

**Replace** `TestAskLangchainStreamAgentFallback` with `TestAskLangchainStreamAgentReal`:

```python
class TestAskLangchainStreamAgentReal:
    """Agent mode streams real events via thread+queue bridge."""

    def test_agent_streams_text_deltas(self) -> None:
        """Agent mode yields text_delta events from run_agent_stream."""
        # Mock run_agent_stream to yield known StreamEvents
        # Call ask_langchain_stream(mcp_config="/tmp/mcp.json")
        # Verify text_delta events received

    def test_agent_streams_tool_events(self) -> None:
        """Agent mode yields tool_use_start and tool_result events."""
        # Mock run_agent_stream to yield tool events
        # Verify tool events with tool_call_id

    def test_agent_streams_raw_lines(self) -> None:
        """Agent mode yields raw_line events."""

    def test_agent_streams_done_event(self) -> None:
        """Agent mode ends with done event."""

    def test_agent_error_propagation(self) -> None:
        """Errors from run_agent_stream propagate to caller."""
        # Mock run_agent_stream to raise an exception
        # Verify exception propagates through the bridge
```

**Add** `TestAskLangchainStreamAgentTimeouts` class:

```python
class TestAskLangchainStreamAgentTimeouts:
    """Timeout and cancellation behavior for agent streaming."""

    def test_no_progress_timeout_raises(self) -> None:
        """If agent produces no events for NO_PROGRESS_TIMEOUT, TimeoutError raised."""
        # Mock run_agent_stream as async generator that blocks forever (asyncio.sleep)
        # Use short timeout override for test speed (e.g., 0.5s)
        # Verify TimeoutError raised

    def test_overall_timeout_raises(self) -> None:
        """If total time exceeds OVERALL_TIMEOUT, TimeoutError raised."""
        # Mock run_agent_stream to yield events slowly (one every 0.3s)
        # Use short overall timeout (e.g., 0.5s)
        # Verify TimeoutError raised after overall cap

    def test_generator_exit_sets_cancel(self) -> None:
        """When consumer stops iterating, cancel_event is set."""
        # Mock run_agent_stream to yield many events
        # Consume only first event, then break (triggers GeneratorExit)
        # Verify cancel_event was set (check thread behavior)
```

**Testing notes for timeouts:** For fast tests, patch the timeout constants to small values:
```python
with patch(f"{_MOD_LC}._AGENT_NO_PROGRESS_TIMEOUT", 0.5):
    ...
```

**Key mocking approach:** Mock `run_agent_stream` as an async generator that yields
predetermined `StreamEvent` dicts. This tests the bridge without needing real LangChain.

## WHAT — Implementation

Modify `ask_langchain_stream()` in `__init__.py`:

**New imports at top:**
```python
import queue
import threading
import time
```

**Add module-level constants:**
```python
# Agent streaming timeout constants (seconds)
_AGENT_NO_PROGRESS_TIMEOUT = 600   # 10 minutes
_AGENT_OVERALL_TIMEOUT = 3600      # 60 minutes
```

**Replace the agent branch** (currently lines calling `ask_langchain()`) with:

```python
if mcp_config:
    config = _load_langchain_config()
    backend = config["backend"]
    if not backend:
        raise ValueError(...)
    sid = session_id or str(uuid.uuid4())
    yield from _ask_agent_stream(
        question=question,
        config=config,
        session_id=sid,
        mcp_config=mcp_config,
        execution_dir=execution_dir,
        env_vars=env_vars,
        timeout=timeout,
    )
    return
```

**Add new function `_ask_agent_stream()`:**

```python
def _ask_agent_stream(
    question: str,
    config: dict[str, str | None],
    session_id: str,
    mcp_config: str,
    execution_dir: str | None = None,
    env_vars: dict[str, str] | None = None,
    timeout: int = 30,
) -> Iterator[StreamEvent]:
```

## ALGORITHM

```python
def _ask_agent_stream(...) -> Iterator[StreamEvent]:
    from .agent import _check_agent_dependencies, run_agent_stream

    _check_agent_dependencies()
    ensure_truststore()
    chat_model = _create_chat_model(config, timeout=timeout)
    history = load_langchain_history(session_id)

    q: queue.Queue[StreamEvent | None] = queue.Queue()
    error_holder: list[Exception] = []
    cancel = threading.Event()

    async def _run() -> None:
        try:
            async for event in run_agent_stream(
                question=question,
                chat_model=chat_model,
                messages=history,
                mcp_config_path=mcp_config,
                session_id=session_id,
                cancel_event=cancel,
                execution_dir=execution_dir,
                env_vars=env_vars,
            ):
                q.put(event)
        except Exception as exc:
            error_holder.append(exc)
        finally:
            q.put(None)  # sentinel

    thread = threading.Thread(target=asyncio.run, args=(_run(),), daemon=True)
    thread.start()

    cancelled = False
    start = time.monotonic()

    try:
        while True:
            try:
                event = q.get(timeout=_AGENT_NO_PROGRESS_TIMEOUT)
            except queue.Empty:
                cancel.set()
                raise TimeoutError(
                    f"Agent produced no output for {_AGENT_NO_PROGRESS_TIMEOUT}s"
                )
            if event is None:
                break
            if time.monotonic() - start > _AGENT_OVERALL_TIMEOUT:
                cancel.set()
                raise TimeoutError(
                    f"Agent execution exceeded {_AGENT_OVERALL_TIMEOUT}s overall timeout"
                )
            yield event
    except GeneratorExit:
        cancel.set()
        cancelled = True
    finally:
        thread.join(timeout=5)

    if error_holder and not cancelled:
        exc = error_holder[0]
        _handle_provider_error(exc, config.get("backend"))
        raise exc
```

## DATA

- `q`: `queue.Queue[StreamEvent | None]` — events from async thread, `None` = sentinel
- `error_holder`: `list[Exception]` — captures exception from async thread
- `cancel`: `threading.Event` — signals cancellation to async generator
- `_AGENT_NO_PROGRESS_TIMEOUT`: `int = 600` — 10 min no-event timeout
- `_AGENT_OVERALL_TIMEOUT`: `int = 3600` — 60 min hard cap
- Both timeout constants raise `TimeoutError` with descriptive message

## HOW — Integration

- `_ask_agent_stream` follows same pattern as `_ask_agent` (config, dependencies, chat_model, history)
- `_handle_provider_error` reused for auth/connection error wrapping
- `run_agent_stream` imported from `.agent` (deferred import, same as existing `run_agent`)
- `ask_langchain()` and `_ask_agent()` (non-streaming path) are unchanged — their existing tests remain valid
- Thread is `daemon=True` so it doesn't prevent process exit

## Verification

Run all three checks after implementation:
1. `mcp__tools-py__run_pylint_check`
2. `mcp__tools-py__run_pytest_check` with `extra_args: ["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration and not langchain_integration"]`
3. `mcp__tools-py__run_mypy_check`
