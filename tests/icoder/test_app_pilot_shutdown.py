from __future__ import annotations

import asyncio
import contextlib
import logging
import queue
import threading
from collections.abc import Callable, Iterator

import pytest

from mcp_coder.icoder.core.app_core import AppCore
from mcp_coder.icoder.core.event_log import EventLog
from mcp_coder.icoder.permissions.approval import ApprovalEngine
from mcp_coder.icoder.permissions.model import PermissionFrame
from mcp_coder.icoder.ui.app import ICoderApp
from mcp_coder.llm.types import StreamEvent
from tests.icoder.test_app_pilot import _submit_and_wait

pytestmark = pytest.mark.textual_integration


#: Hard cap on the quit-with-an-approval-pending case, deliberately far below
#: the provider's 300s inactivity timeout: a stall must fail fast rather than
#: pass for a stalled-then-timed-out turn.
_QUIT_TIMEOUT = 30.0


class _ApprovalPendingLLMService:
    """Fake service reproducing ``_ask_agent_stream``'s two-loop topology.

    ``ApprovalEngine.request_approval`` runs on a background thread with its own
    ``asyncio.run`` loop (the stand-in agent loop) and the emitted event travels
    through a ``queue.Queue``, so the Textual worker parks in ``q.get`` while the
    approval future lives on a *different* loop -- exactly the shape R9 is about,
    without needing a real agent.
    """

    def __init__(self, engine: ApprovalEngine) -> None:
        self._engine = engine
        self.agent_thread: threading.Thread | None = None
        #: Set once the UI has handled the emitted event and the consumer has
        #: gone back to ``q.get`` -- i.e. the approval is genuinely pending.
        self.dispatched = threading.Event()

    def stream(
        self, question: str, *, frame: PermissionFrame | None = None
    ) -> Iterator[StreamEvent]:
        q: queue.Queue[StreamEvent | None] = queue.Queue()

        async def _ask() -> None:
            try:
                await self._engine.request_approval(
                    tool_name="mcp__srv__do_it", args={}, source="project"
                )
            finally:
                q.put(None)  # sentinel, like the provider's producer half

        def _agent_main() -> None:
            # Production keeps the CancelledError off ``asyncio.run``: the
            # provider's ``_run`` wraps its ``run_agent_stream`` drain in an
            # ``except asyncio.CancelledError`` and returns normally, so the
            # agent thread exits quietly with the sentinel already queued. This
            # fake has no drain to wrap -- ``_ask`` is the whole coroutine --
            # so it catches at the thread top instead. Same observable result,
            # which is what the pilot tests below assert: a silent thread exit
            # and no stray traceback over a live Textual screen.
            with contextlib.suppress(BaseException):  # pylint: disable=broad-exception-caught
                asyncio.run(_ask())

        self._engine.attach(q.put)
        thread = threading.Thread(target=_agent_main, daemon=True)
        self.agent_thread = thread
        thread.start()
        try:
            while True:
                event = q.get(timeout=_QUIT_TIMEOUT)
                if event is None:
                    return
                yield event
                self.dispatched.set()
        finally:
            # Same order as the provider: detach (cancelling what is left)
            # BEFORE the join, so a parked interceptor unwinds while it waits.
            self._engine.detach()
            thread.join(timeout=5)

    @property
    def provider(self) -> str:
        return "claude"

    @property
    def session_id(self) -> str | None:
        return None

    def reset_session(self) -> None:
        pass

    def set_session_id(self, session_id: str | None) -> None:
        pass


async def test_quit_with_approval_pending_exits_and_unwinds_worker(
    event_log: EventLog, monkeypatch: pytest.MonkeyPatch
) -> None:
    """R9 on the real exit path: quitting with an approval pending must not hang.

    Asserting only that ``on_unmount`` called ``cancel_pending_approvals()``
    would be a proxy for the hook, not for R9 -- it would stay green while the
    unwound worker blocked forever in ``call_from_thread`` against a dead
    message pump. So this drives the whole path: the app exits, the parked
    agent thread dies, and the ``_stream_llm`` worker body returns.
    """
    engine = ApprovalEngine()
    service = _ApprovalPendingLLMService(engine)
    app = ICoderApp(
        AppCore(llm_service=service, event_log=event_log, approval_engine=engine)
    )

    # Textual thread workers run in a pooled, reused thread, so ``is_alive()``
    # says nothing about the worker *body*. Wrap it instead: the event is set
    # only once ``_stream_llm`` actually returns.
    worker_done = threading.Event()
    worker_error: list[BaseException] = []
    original_stream_llm = app._stream_llm

    def _tracked(text: str, skill_name: str | None = None) -> None:
        try:
            original_stream_llm(text, skill_name)
        except BaseException as exc:  # pylint: disable=broad-exception-caught
            worker_error.append(exc)
        finally:
            worker_done.set()

    monkeypatch.setattr(app, "_stream_llm", _tracked)

    async def _turn_then_quit() -> None:
        async with app.run_test() as pilot:
            await _submit_and_wait(app, pilot, text="use the tool")
            for _ in range(200):
                if service.dispatched.is_set():
                    break
                await pilot.pause(delay=0.05)
            assert service.dispatched.is_set(), (
                "the approval_request never reached the UI"
            )
            assert engine.pending() == 1, "nothing pending: R9 is not being exercised"
            app.exit()
            await pilot.pause()

    await asyncio.wait_for(_turn_then_quit(), timeout=_QUIT_TIMEOUT)

    assert not app.is_running, "the app did not exit"
    assert engine.cancelled, "on_unmount never reached the engine"
    # Both halves of R9 in one pair of asserts. Without the closed-app guard the
    # worker tail's ``call_from_thread`` hops reach a torn-down app: either they
    # block on a loop this (blocking) wait is keeping busy, or they run and
    # explode on the cleared widget tree.
    assert worker_done.wait(timeout=10.0), "the _stream_llm worker body never returned"
    assert worker_error == [], f"the worker tail hit a torn-down app: {worker_error!r}"
    assert service.agent_thread is not None
    assert service.agent_thread.is_alive() is False, (
        "the parked approval future was never cancelled"
    )


async def test_shutdown_guard_drops_every_ui_call_from_worker_tail(
    make_icoder_app: Callable[..., ICoderApp], monkeypatch: pytest.MonkeyPatch
) -> None:
    """With ``_shutting_down`` set, the worker issues no ``call_from_thread``.

    Driven from the UI thread on purpose: with the guard up not a single
    cross-thread hop is attempted, so the body is free to run here -- and the
    call the tail would otherwise make (``_reset_busy_indicator``, on the
    ``elif not _error_handled`` branch) is the exact one that hangs a quit.
    """
    app = make_icoder_app(
        responses=[[{"type": "text_delta", "text": "hi"}, {"type": "done"}]]
    )
    async with app.run_test() as pilot:
        await pilot.pause()
        calls: list[Callable[..., None]] = []
        monkeypatch.setattr(
            app, "call_from_thread", lambda callback, *args: calls.append(callback)
        )
        app._shutting_down.set()

        app._stream_llm("hello")  # returns instead of blocking on a dead pump

        assert calls == []


async def test_shutdown_race_runtime_error_is_logged_not_propagated(
    make_icoder_app: Callable[..., ICoderApp],
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A ``RuntimeError`` in the race window is caught and logged, never raised.

    ``_shutting_down`` is deliberately NOT set here: this is the narrow window
    where the flag is still down but ``App._loop`` has already gone, so
    ``call_from_thread`` raises. It must not escape the worker.
    """
    app = make_icoder_app(
        responses=[[{"type": "text_delta", "text": "hi"}, {"type": "done"}]]
    )

    def _pump_is_gone(callback: Callable[..., None], *args: object) -> None:
        raise RuntimeError("App is not running")

    async with app.run_test() as pilot:
        await pilot.pause()
        monkeypatch.setattr(app, "call_from_thread", _pump_is_gone)
        with caplog.at_level(logging.DEBUG, logger="mcp_coder.icoder.ui.stream_view"):
            app._stream_llm("hello")

        assert any(
            "call_from_thread dropped during shutdown" in record.getMessage()
            for record in caplog.records
        )
