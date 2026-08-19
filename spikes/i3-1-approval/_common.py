"""Shared harness for the I3.1 approval spike (#1044) — Tier B / Tier C.

Imported by ``tier_b_cancel.py`` (Step 2), ``tier_b_pause.py`` (Step 3) and
``tier_c.py`` (Step 5). Holds exactly one copy each of:

  * ``FakeChatModel`` — a scripted ``BaseChatModel`` that runs on the agent loop
    and records the loop identity + the messages it was handed, per invoke.
  * ``Gate`` + ``make_blocking_tool`` — a per-scenario cross-thread handoff and
    the tool coroutine that blocks on it (bound in by closure, never shared).
  * ``run_bridge`` / ``BridgeRun`` — a **verbatim reconstruction** of the
    production thread+queue+``join(timeout=5)`` consumer bridge.

Requires the REAL ``langchain-core`` / ``langgraph`` in the venv. Do NOT import
the repo's test conftest — it swaps in stub langchain classes that would void
the loop-mechanics proof (see ``pr_info/steps/summary.md``).
"""

from __future__ import annotations

import asyncio
import queue
import threading
import time
from dataclasses import dataclass
from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage
from langchain_core.outputs import ChatGeneration, ChatResult

# ---------------------------------------------------------------------------
# Fake chat model
# ---------------------------------------------------------------------------


def _default_script() -> list[AIMessage]:
    """The 2-entry script EVERY current scenario uses (Steps 2, 3, 5).

    Invoke 1 -> one tool_call to ``ping``; invoke 2 -> assistant *text*
    ``'done'`` (NOT the ``{"type": "done"}`` StreamEvent at agent.py:698).
    """
    return [
        AIMessage(content="", tool_calls=[{"name": "ping", "args": {}, "id": "call_1"}]),
        AIMessage(content="done"),
    ]


class FakeChatModel(BaseChatModel):
    """Replays a caller-supplied script of ``AIMessage``s, one per invoke.

    ``responses`` is the script; invoke N returns ``responses[N-1]``. The
    DEFAULT script is the 2-entry one every current scenario uses (tool_call ->
    ``AIMessage('done')``). The ``responses`` parameter stays regardless: the
    script IS the configuration, so a scenario needing a different one passes
    it instead of reaching for a knob that does not exist.

    Usable by ``create_react_agent``, which calls ``model.bind_tools(tools)`` —
    ``BaseChatModel.bind_tools`` raises ``NotImplementedError``, so it is
    overridden to return ``self`` (ignoring the tools; the script decides the
    tool_calls).

    Implements the ASYNC method ``_agenerate``, not ``_generate``. The agent
    path is ``astream_events``; ``BaseChatModel``'s default ``_agenerate``
    delegates to ``run_in_executor(None, self._generate, ...)`` — a model
    implementing only ``_generate`` would therefore run on a THREAD-POOL thread
    with no running loop, where ``asyncio.get_running_loop()`` raises
    ``RuntimeError`` and ``loop_id`` is destroyed. ``_generate`` exists only to
    satisfy the ABC and raises.

    Records, per invoke (inside ``_agenerate``): ``loop_id`` =
    ``id(asyncio.get_running_loop())`` (the independent agent-loop reference the
    D6 check needs) and ``last_messages`` (the message list it was handed;
    Step 5 asserts the post-``ToolNode`` ``ToolMessage`` is present in the 2nd
    invoke's list). ``invoke_count`` is the same counter that indexes
    ``responses`` — ``scenario_backstop`` asserts it stayed at 1.
    """

    responses: list[AIMessage] = []  # always supplied via __init__ (default script)
    invoke_count: int = 0
    loop_id: int | None = None
    last_messages: Any = None

    def __init__(self, responses: list[AIMessage] | None = None, **kw: Any) -> None:
        super().__init__(responses=responses or _default_script(), **kw)

    def bind_tools(self, tools: Any, **kw: Any) -> "FakeChatModel":
        return self

    def _generate(self, messages, stop=None, run_manager=None, **kw):  # type: ignore[no-untyped-def]
        # Exists only to satisfy the BaseChatModel ABC. The agent path is async
        # (astream_events -> _agenerate); reaching here would mean the model ran
        # on a thread-pool thread with no running loop (see class docstring).
        raise NotImplementedError("FakeChatModel implements _agenerate, not _generate")

    async def _agenerate(self, messages, stop=None, run_manager=None, **kw):  # type: ignore[no-untyped-def]
        # Runs on the agent's asyncio.run loop — this is where loop identity is
        # captured (D6) and where the post-ToolNode message list is observed.
        self.loop_id = id(asyncio.get_running_loop())
        self.last_messages = list(messages)
        msg = self.responses[self.invoke_count]
        self.invoke_count += 1
        return ChatResult(generations=[ChatGeneration(message=msg)])

    @property
    def _llm_type(self) -> str:
        return "fake"


# ---------------------------------------------------------------------------
# Per-scenario cross-thread handoff + blocking tool
# ---------------------------------------------------------------------------


@dataclass
class Gate:
    """PER-SCENARIO handoff the driver thread uses to reach the agent loop.

    NOT module/class-level state: ``scenario_inert`` deliberately never
    resolves, so a shared ``fired`` flag would stay True forever; the next
    scenario's wait-for-fired would then pass immediately — possibly before the
    new tool coroutine has published its loop/future — and resolve against the
    STALE loop/future. That breaks the determinism AC. One fresh instance per
    scenario, bound into the tool by ``make_blocking_tool``.
    """

    loop: asyncio.AbstractEventLoop | None = None
    future: "asyncio.Future[str] | None" = None
    fired: bool = False


def make_blocking_tool(gate: Gate):  # type: ignore[no-untyped-def]
    """Factory -> tool coroutine closed over THIS scenario's ``gate``.

    The coroutine captures the agent loop via ``get_running_loop()`` (never a
    build-time handle), publishes it plus a fresh Future onto ``gate``, sets
    ``gate.fired = True``, then awaits the Future. The driver thread resolves it
    with ``gate.loop.call_soon_threadsafe(gate.future.set_result, ...)``.
    """

    async def ping() -> str:
        loop = asyncio.get_running_loop()
        gate.loop = loop
        gate.future = loop.create_future()
        gate.fired = True
        return await gate.future

    return ping


# ---------------------------------------------------------------------------
# Verbatim reconstruction of the production consumer bridge
# ---------------------------------------------------------------------------


class BridgeRun:
    """Handle for a running bridge so the main thread can poke it mid-block.

    The verbatim consumer copy (below) is a *generator* (it ``yield``s) and a
    blocking calling-thread consumer cannot be poked (``cancel_event``,
    ``gen.close()``) while the tool is still blocked — which
    ``scenario_inert``/``direct``/``backstop`` all require. So the copied
    consumer generator runs on a **worker thread** here; this handle exposes
    what the scenarios assert on while the agent thread is still blocked.
    """

    def __init__(
        self,
        events: list[Any],
        agent_thread: threading.Thread,
        cancel_event: threading.Event,
        gen: Any,
    ) -> None:
        self.events = events  # filled live by the worker as events are yielded
        self.agent_thread = agent_thread  # the agent asyncio.run thread (is_alive)
        self.cancel_event = cancel_event  # the SAME Event run_agent_stream checks
        self._gen = gen  # the copied consumer generator
        self.worker_thread: threading.Thread | None = None
        # exception raised by the copied consumer ON THE WORKER THREAD, captured
        # for the main thread. Without this there is no error channel and Step 3's
        # negative control (F5) can never see the TimeoutError it must assert.
        self.error: BaseException | None = None
        # outcome of a close() attempt while blocked (F11): CPython refuses
        # gen.close() while the frame is executing.
        self.close_error: BaseException | None = None

    def close(self) -> None:
        """ATTEMPT ``gen.close()`` on the copied consumer (the :530 path).

        CPython refuses ``close()`` while the generator frame is executing, and
        the worker thread sitting in ``q.get(...)`` IS executing it — so this
        raises ``ValueError("generator already executing")``. The outcome is
        captured on ``self.close_error`` and exposed (not swallowed);
        ``scenario_inert`` asserts on it.
        """
        try:
            self._gen.close()
        except BaseException as exc:  # noqa: BLE001  # pylint: disable=broad-except
            self.close_error = exc

    def join(self, timeout: float | None = None) -> None:
        """Wait for the worker driving the copied consumer to drain."""
        if self.worker_thread is not None:
            self.worker_thread.join(timeout=timeout)


def run_bridge(  # type: ignore[no-untyped-def]
    gen_factory,
    inactivity_timeout: float = 300.0,
    overall_cap: float = 3600.0,
) -> BridgeRun:
    """Start a VERBATIM reconstruction of the production consumer bridge.

    Faithful reproduction of ``_ask_agent_stream`` in
    ``src/mcp_coder/llm/providers/langchain/__init__.py`` — the thread+queue
    bridge and its calling-thread consumer (``q``/``error_holder``/``cancel``
    through the ``join(timeout=5)`` finally and the ``error_holder`` re-raise;
    the range is ~ ``:479-534``). **Navigate by symbol, line numbers drift.**

    Two spike-only deviations, both required and both non-fidelity-bearing:
      * The production consumer is inline in a generator; here it is driven on a
        **worker thread** so the main thread can set ``cancel``, call
        ``.close()``, or resolve the Future while the tool is blocked.
      * Production hardcodes ``q.get(timeout=timeout)`` and
        ``_AGENT_OVERALL_TIMEOUT``; here they are the ``inactivity_timeout`` /
        ``overall_cap`` params (defaults match production: 300 / 3600). The
        production ``_handle_provider_error(...)`` before the final re-raise is
        provider-specific and dropped — a bare ``raise`` is kept.

    The worker thread is ``daemon=True``: ``scenario_inert`` deliberately
    abandons its run (its tool never resolves), so the worker stays parked in
    ``q.get(timeout=inactivity_timeout)`` for the full 300s default — a
    non-daemon worker would be joined at interpreter shutdown and the script
    would hang ~300s. (Spike-only thread, no production counterpart, so no
    fidelity constraint; the production *agent* thread is separately
    ``daemon=True`` at ``__init__.py:506`` and reproduced below.)

    ``gen_factory(cancel_event)`` returns the agent's async event iterator
    (real ``run_agent_stream(...)``), wired to the bridge-owned ``cancel``
    Event exactly as production passes its ``cancel`` into ``run_agent_stream``.
    Returns immediately with a ``BridgeRun`` handle.
    """
    # --- verbatim: producer side (thread + queue bridge) ---
    q: queue.Queue[Any] = queue.Queue()
    error_holder: list[BaseException] = []
    cancel = threading.Event()

    async def _run() -> None:
        try:
            async for event in gen_factory(cancel):
                q.put(event)
        except Exception as exc:  # pylint: disable=broad-except
            error_holder.append(exc)
        finally:
            q.put(None)  # sentinel

    def _thread_main() -> None:
        asyncio.run(_run())

    thread = threading.Thread(target=_thread_main, daemon=True)
    thread.start()

    events: list[Any] = []

    # --- verbatim: calling-thread consumer (driven on a worker thread here) ---
    def _consumer():  # type: ignore[no-untyped-def]
        cancelled = False
        start = time.monotonic()
        try:
            while True:
                try:
                    event = q.get(timeout=inactivity_timeout)
                except queue.Empty as exc:
                    cancel.set()
                    raise TimeoutError(
                        f"LLM inactivity timeout (langchain): no response for "
                        f"{inactivity_timeout}s. Connection closed."
                    ) from exc
                if event is None:
                    break
                if time.monotonic() - start > overall_cap:
                    cancel.set()
                    raise TimeoutError(
                        f"Agent execution exceeded {overall_cap}s overall timeout"
                    )
                yield event
        except GeneratorExit:
            cancel.set()
            cancelled = True
        finally:
            thread.join(timeout=5)

        if error_holder and not cancelled:
            raise error_holder[0]

    gen = _consumer()
    run = BridgeRun(events=events, agent_thread=thread, cancel_event=cancel, gen=gen)

    def _worker() -> None:
        try:
            for ev in gen:
                events.append(ev)
        except BaseException as exc:  # noqa: BLE001  # pylint: disable=broad-except
            run.error = exc

    worker = threading.Thread(target=_worker, daemon=True)
    run.worker_thread = worker
    worker.start()
    return run


def wait_for(predicate, timeout: float = 10.0, interval: float = 0.01) -> bool:  # type: ignore[no-untyped-def]
    """Poll ``predicate`` until true or ``timeout`` elapses. Returns the result."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(interval)
    return bool(predicate())
