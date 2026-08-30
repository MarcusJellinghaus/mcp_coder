"""Provider-side plumbing for the in-band approval pause (#1045, Step 7).

Covers the four things ``_ask_agent_stream`` gains when an ``ApprovalBridge`` is
threaded into it:

* the **pause** — a pending approval suspends both streaming timeouts, as a
  timestamped window (overall cap) plus an epoch counter (inactivity budget);
* the **attach/detach lifecycle** — one site, in the ``try``/``finally`` that
  already owns ``thread.join(timeout=5)``, with ``detach()`` *before* the join;
* ``_run``'s ``except asyncio.CancelledError``, which keeps a hard cancel out of
  ``error_holder`` and off stderr;
* the **no-op** on the text branch, which non-iCoder callers still use.

The turns here are driven by a scripted stand-in for ``run_agent_stream`` rather
than by the real agent: the pause is a property of the *consumer loop*, and a
scripted producer is what makes “the tool went quiet for longer than the
inactivity timeout” a deterministic 1.6 seconds instead of a langchain
installation. Test 5 reuses the Step 3 harness's parked-on-a-Future shape
directly rather than importing it, because the thing under test there is the
``detach()``-then-``join()`` ordering, not langgraph's unwind — which
``test_approval_cancel_path.py`` already pins down against the real agent.

Every ``mcp_coder.llm.providers.langchain`` import stays inside a function, per
this directory's convention (see ``approval_harness`` for why CI makes the
module-scope version wrong).
"""

from __future__ import annotations

import asyncio
import threading
from collections.abc import AsyncIterator, Callable, Generator, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, cast
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.llm.types import StreamEvent

if TYPE_CHECKING:
    from mcp_coder.llm.providers.langchain.approval_bridge import ApprovalBridge

_MOD_LC = "mcp_coder.llm.providers.langchain"
_MOD_AGENT = "mcp_coder.llm.providers.langchain.agent"

#: The inactivity timeout every agent-branch turn below is given. It is an
#: ``int`` because that is what the provider's signature accepts, which sets the
#: floor for every duration in this module.
_INACTIVITY = 1


def _make_config(backend: str = "openai") -> dict[str, str | None]:
    """Return a minimal langchain config dict for the agent branch."""
    return {
        "provider": "langchain",
        "backend": backend,
        "model": "gpt-4o",
        "api_key": None,
        "base_url": None,
        "api_version": None,
    }


class _FakeBridge:
    """An ``ApprovalBridge`` the *test* drives instead of a real engine.

    ``open_approval`` deliberately increments the pending count **before** it
    emits, which is the ordering the real engine guarantees (summary §2.2) and
    the reason the consumer's pause window is always open by the time it
    dequeues an ``approval_request``.
    """

    def __init__(self) -> None:
        self.attached_emits: list[Callable[[StreamEvent], None]] = []
        #: The object each sink is bound to — ``q`` itself, for ``q.put``.
        self.attached_queues: list[Any] = []
        self.detach_count = 0
        self.on_detach: Callable[[], None] | None = None
        self._emit: Callable[[StreamEvent], None] | None = None
        self._pending = 0

    # --- the ApprovalBridge Protocol ---

    def attach(self, emit: Callable[[StreamEvent], None]) -> None:
        """Bind the turn's sink and record it for the lifecycle assertions."""
        self._emit = emit
        self._pending = 0
        self.attached_emits.append(emit)
        self.attached_queues.append(getattr(emit, "__self__", None))

    def detach(self) -> None:
        """Unbind the sink, running the test's cancel hook like the engine does."""
        self.detach_count += 1
        self._emit = None
        self._pending = 0
        if self.on_detach is not None:
            self.on_detach()

    def pending(self) -> int:
        """Return the number of approvals awaiting a decision."""
        return self._pending

    # --- driver side, called from the agent thread ---

    def open_approval(self, approval_id: str = "a1") -> None:
        """Register an approval and emit its request, in that order."""
        self._pending += 1
        if self._emit is not None:
            self._emit(
                {
                    "type": "approval_request",
                    "approval_id": approval_id,
                    "tool": "ping",
                    "args": {},
                }
            )

    def close_approval(self) -> None:
        """Record that the human answered."""
        self._pending = max(0, self._pending - 1)


def _as_bridge(bridge: _FakeBridge) -> "ApprovalBridge":
    """Assert (through mypy) that the fake really satisfies the Protocol.

    Args:
        bridge: The fake to check.

    Returns:
        The same object, typed as the Protocol the provider consumes.
    """
    return bridge


@dataclass
class _ParkedTurn:
    """What a parked fake agent publishes about itself, for test 5.

    Attributes:
        loop: The agent loop, captured inside the coroutine.
        future: The Future the fake agent is parked on.
        thread: The agent thread, so the test can assert it died.
    """

    loop: asyncio.AbstractEventLoop | None = None
    future: asyncio.Future[None] | None = None
    thread: threading.Thread | None = None


_Script = Callable[[], AsyncIterator[StreamEvent]]


@contextmanager
def _patched(script: _Script, overall: float = 3600.0) -> Iterator[None]:
    """Run the agent branch against *script* instead of the real agent.

    Args:
        script: Builds the async iterator that stands in for
            ``run_agent_stream``.
        overall: Value monkeypatched over ``_AGENT_OVERALL_TIMEOUT``.

    Yields:
        None, with the provider's agent-mode dependencies stubbed.
    """

    def _fake_run_agent_stream(**_kwargs: Any) -> AsyncIterator[StreamEvent]:
        return script()

    with (
        patch(f"{_MOD_LC}.load_langchain_history", return_value=[]),
        patch(f"{_MOD_LC}.store_langchain_history"),
        patch(f"{_MOD_LC}._create_chat_model", return_value=MagicMock()),
        patch(f"{_MOD_LC}._AGENT_OVERALL_TIMEOUT", overall),
        patch(f"{_MOD_AGENT}._check_agent_dependencies"),
        patch(f"{_MOD_AGENT}.run_agent_stream", _fake_run_agent_stream),
    ):
        yield


def _turn(bridge: _FakeBridge | None) -> Generator[StreamEvent, None, None]:
    """Start an agent-mode turn with *bridge* attached.

    Args:
        bridge: The bridge to thread in, or None for the negative control.

    Returns:
        The unstarted generator. Cast because ``_ask_agent_stream`` is annotated
        with the wider ``Iterator``, and two tests need ``close()`` to reach the
        ``GeneratorExit`` path.
    """
    from mcp_coder.llm.providers.langchain import _ask_agent_stream

    return cast(
        Generator[StreamEvent, None, None],
        _ask_agent_stream(
            question="Hi",
            config=_make_config(),
            session_id="s1",
            mcp_config=".mcp.json",
            timeout=_INACTIVITY,
            approval_bridge=None if bridge is None else _as_bridge(bridge),
        ),
    )


# --- 1. the pause defeats both timeouts ---


def test_pause_defeats_both_timeouts() -> None:
    """A tool that outlasts both timeouts still completes while an approval pends.

    The pause is 1.6s: longer than the 1s inactivity timeout (so ``queue.Empty``
    fires at least once) and longer than the 0.5s overall cap.
    """
    bridge = _FakeBridge()

    async def _script() -> AsyncIterator[StreamEvent]:
        yield {"type": "text_delta", "text": "hi"}
        bridge.open_approval()
        await asyncio.sleep(1.6)
        bridge.close_approval()
        yield {"type": "done", "session_id": "s1"}

    with _patched(_script, overall=0.5):
        events = list(_turn(bridge))

    assert [e["type"] for e in events] == ["text_delta", "approval_request", "done"]


# --- 2. a pause shorter than the inactivity timeout is still excluded ---


def test_sub_inactivity_pause_is_excluded_from_the_overall_cap() -> None:
    """A pause with no ``queue.Empty`` at all is still credited to ``paused``.

    ``timeout`` is 30s here, so the 1s pause never expires a ``q.get`` — there is
    no ``queue.Empty`` to hang an accumulator off. Only the timestamped window
    keeps the turn under the 0.3s cap; ``paused += timeout`` in the
    ``queue.Empty`` branch would credit nothing and the turn would die.
    """
    bridge = _FakeBridge()

    async def _script() -> AsyncIterator[StreamEvent]:
        bridge.open_approval()
        await asyncio.sleep(1.0)
        bridge.close_approval()
        yield {"type": "done", "session_id": "s1"}

    from mcp_coder.llm.providers.langchain import _ask_agent_stream

    with _patched(_script, overall=0.3):
        events = list(
            _ask_agent_stream(
                question="Hi",
                config=_make_config(),
                session_id="s1",
                mcp_config=".mcp.json",
                timeout=30,  # large enough that no queue.Empty ever fires
                approval_bridge=_as_bridge(bridge),
            )
        )

    assert [e["type"] for e in events] == ["approval_request", "done"]


# --- 2b. a pause that ends mid-wait does not consume the inactivity budget ---


def test_pause_ending_mid_wait_restarts_the_inactivity_budget() -> None:
    """The answer lands inside a ``q.get`` wait, then the tool runs on quietly.

    ``q.get`` restarts its full ``timeout`` on every call, so the pause that
    opened and closed inside the first wait would otherwise have eaten the whole
    budget: the ``queue.Empty`` at t=1.0 sees ``pending() == 0`` and, without the
    ``pause_epoch`` snapshot, raises ``TimeoutError("no response for 1s")`` after
    0.3s of real inactivity. This is the 250s-answer + 60s-tool scenario.
    """
    bridge = _FakeBridge()

    async def _script() -> AsyncIterator[StreamEvent]:
        bridge.open_approval()
        await asyncio.sleep(0.7)  # the human answers, mid-wait
        bridge.close_approval()
        await asyncio.sleep(0.7)  # the approved tool then runs quietly
        yield {"type": "done", "session_id": "s1"}

    with _patched(_script):
        events = list(_turn(bridge))

    assert [e["type"] for e in events] == ["approval_request", "done"]


# --- 3. negative control ---


def test_without_a_bridge_the_same_turn_times_out() -> None:
    """The identical script raises ``TimeoutError`` with no bridge attached.

    Proves the pause is load-bearing rather than vacuous: nothing else in the
    setup keeps tests 1 and 2b alive.
    """
    bridge = _FakeBridge()  # never attached; only drives the script's timing

    async def _script() -> AsyncIterator[StreamEvent]:
        yield {"type": "text_delta", "text": "hi"}
        bridge.open_approval()
        await asyncio.sleep(1.6)
        bridge.close_approval()
        yield {"type": "done", "session_id": "s1"}

    with _patched(_script, overall=0.5):
        with pytest.raises(
            TimeoutError, match=r"no response for 1s\. Connection closed"
        ):
            list(_turn(None))

    assert bridge.attached_emits == []


# --- 4. attach/detach lifecycle ---


def _quiet_script(bridge: _FakeBridge) -> _Script:
    """Build a script that emits one approval request and finishes at once."""

    async def _script() -> AsyncIterator[StreamEvent]:
        bridge.open_approval()
        bridge.close_approval()
        yield {"type": "done", "session_id": "s1"}

    return _script


def test_attach_receives_this_turns_queue_and_detach_runs_on_completion() -> None:
    """``attach`` gets a sink that feeds *this* generator; ``detach`` runs once."""
    bridge = _FakeBridge()

    with _patched(_quiet_script(bridge)):
        events = list(_turn(bridge))

    assert len(bridge.attached_emits) == 1
    assert [e["type"] for e in events] == ["approval_request", "done"]
    assert bridge.detach_count == 1


def test_detach_runs_when_the_generator_is_closed() -> None:
    """Closing the consumer mid-stream still detaches (the cancel path)."""
    bridge = _FakeBridge()

    async def _script() -> AsyncIterator[StreamEvent]:
        yield {"type": "text_delta", "text": "hi"}
        await asyncio.sleep(5.0)
        yield {"type": "done", "session_id": "s1"}

    with _patched(_script):
        gen = _turn(bridge)
        assert next(gen)["type"] == "text_delta"
        assert bridge.detach_count == 0
        gen.close()

    assert bridge.detach_count == 1


def test_two_turns_never_share_a_queue() -> None:
    """Each turn attaches a sink bound to its own queue (the stale-``q`` bug)."""
    bridge = _FakeBridge()

    with _patched(_quiet_script(bridge)):
        list(_turn(bridge))
        list(_turn(bridge))

    assert len(bridge.attached_queues) == 2
    first = bridge.attached_queues[0]
    second = bridge.attached_queues[1]
    assert first is not None and second is not None
    assert first is not second
    assert bridge.detach_count == 2


# --- 5. generator closed while an approval is pending ---


def test_close_while_pending_detaches_before_the_join() -> None:
    """The parked agent thread is dead after the join, not leaked for the process.

    ``detach()`` cancels the Future the fake agent is parked on — exactly what
    the real engine does — and it must run *before* ``thread.join(timeout=5)``:
    joining first would burn the full 5s against a thread nothing can unpark.
    """
    bridge = _FakeBridge()
    parked = _ParkedTurn()

    def _cancel_like_the_engine() -> None:
        loop, future = parked.loop, parked.future
        if loop is not None and future is not None:
            loop.call_soon_threadsafe(future.cancel)

    bridge.on_detach = _cancel_like_the_engine

    async def _script() -> AsyncIterator[StreamEvent]:
        loop = asyncio.get_running_loop()
        parked.loop = loop
        parked.future = loop.create_future()
        parked.thread = threading.current_thread()
        bridge.open_approval()
        await parked.future  # the interceptor's park
        yield {"type": "done", "session_id": "s1"}

    with _patched(_script):
        gen = _turn(bridge)
        assert next(gen)["type"] == "approval_request"
        gen.close()

    assert bridge.detach_count == 1
    assert parked.thread is not None
    assert (
        parked.thread.is_alive() is False
    ), "agent thread still parked after join(5) — detach did not cancel the future"


# --- 6. CancelledError inside _run ---


def test_cancelled_error_in_run_is_not_an_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A hard cancel escapes nothing, records nothing, and still ends the turn.

    ``CancelledError`` is a ``BaseException``, so without its own clause it
    escapes ``_run`` entirely, reaches ``_thread_main``'s bare ``asyncio.run``
    and lands in the thread excepthook — whose default prints a traceback on
    stderr, i.e. onto a live Textual screen. The sentinel is put either way (the
    ``finally`` sees to that), so the excepthook recorder is the assertion that
    discriminates; a non-empty ``error_holder`` would re-raise out of ``list()``.
    """
    escaped: list[Any] = []
    monkeypatch.setattr(threading, "excepthook", escaped.append)

    bridge = _FakeBridge()

    async def _script() -> AsyncIterator[StreamEvent]:
        yield {"type": "text_delta", "text": "hi"}
        raise asyncio.CancelledError()

    with _patched(_script):
        events = list(_turn(bridge))

    assert escaped == [], f"an exception escaped the agent thread: {escaped!r}"
    assert [e["type"] for e in events] == ["text_delta"]
    assert bridge.detach_count == 1


# --- 7. no-op on the text branch ---


def test_text_branch_ignores_the_bridge() -> None:
    """Without ``mcp_config`` the bridge is never attached (R13)."""
    bridge = _FakeBridge()

    chunk = MagicMock()
    chunk.content = "tok"
    chunk.model_dump.return_value = {"type": "AIMessageChunk", "content": "tok"}
    mock_model = MagicMock()
    mock_model.stream.return_value = iter([chunk])

    with (
        patch(f"{_MOD_LC}._load_langchain_config", return_value=_make_config()),
        patch(f"{_MOD_LC}.load_langchain_history", return_value=[]),
        patch(f"{_MOD_LC}.store_langchain_history"),
        patch(f"{_MOD_LC}._create_chat_model", return_value=mock_model),
    ):
        from mcp_coder.llm.providers.langchain import ask_langchain_stream

        events = list(ask_langchain_stream("Hi", approval_bridge=_as_bridge(bridge)))

    assert any(e["type"] == "text_delta" for e in events)
    assert bridge.attached_emits == []
    assert bridge.detach_count == 0
