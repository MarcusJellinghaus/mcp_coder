"""End-to-end in-band approval through the **real** agent path (#1045, Step 11).

Every other module in this feature tests one seam: the engine on pure asyncio
(``tests/icoder/test_permissions_approval.py``), the gateway against a fake
engine, the provider's pause against a scripted producer
(``test_approval_stream_bridge.py``). This one wires the whole chain together —
scripted chat model -> ``create_react_agent`` -> ``ToolNode`` -> the MCP-shaped
tool -> :meth:`LangchainEnforcementGateway.interceptor` -> :class:`ApprovalEngine`
-> the per-turn queue -> ``_ask_agent_stream`` — and drives it exactly the way
iCoder does: the generator runs on a consumer thread while the *test* thread
answers, which is the two-loop topology the whole design exists for.

**Why the tool is \"MCP-shaped\" rather than a real MCP tool.** In production the
interceptor is installed by ``convert_mcp_tool_to_langchain_tool``, which needs
a live MCP server. The tools below instead call ``gateway.interceptor`` from
their own coroutine, passing the same four attributes the interceptor reads
(``server_name``, ``name``, ``args`` and ``runtime.tool_call_id``). Everything
downstream of that call — the pause, the deny ``ToolMessage``, langgraph's
handling of it — is the production code path, unmodified.

``tool_call_id`` is **injected by langchain** (``InjectedToolCallId``) rather
than hard-coded, because that is the whole point of the deny case: the spike's
FINDINGS §10 recorded that a deny carrying ``tool_call_id=\"\"`` leaves the
model's tool call unpaired, so ``create_react_agent`` raises
``INVALID_CHAT_HISTORY`` and the agent never continues. Test 2 is that
regression, and it can only be one if the id is genuinely the model's.

Session storage needs no isolation here: this directory's autouse ``_tmp_home``
fixture already redirects ``Path.home()`` to ``tmp_path`` (R12), which is where
``run_agent_stream``'s unconditional history write lands.

Every ``pytest.importorskip`` and every langchain import lives *inside* a
function, and both fake models are subclassed inside one — see
``approval_harness`` for why CI makes the module-scope version wrong, and why
``importorskip`` alone is not enough in this directory.
"""

from __future__ import annotations

import asyncio
import threading
import time
from collections.abc import Callable, Generator, Iterator, Sequence
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Annotated, Any, cast
from unittest.mock import patch
from uuid import uuid4

import pytest

from mcp_coder.icoder.permissions.approval import ApprovalDecision, ApprovalEngine
from mcp_coder.icoder.permissions.gateway import (
    _DENY_USER,
    LangchainEnforcementGateway,
)
from mcp_coder.icoder.permissions.model import (
    Matcher,
    PermissionConfig,
    Policy,
    Rule,
)
from mcp_coder.llm.types import StreamEvent
from tests.llm.providers.langchain.approval_harness import (
    TOOL_NAME,
    make_fake_chat_model,
    require_real_langchain,
    wait_for,
)

_MOD_LC = "mcp_coder.llm.providers.langchain"
_MOD_AGENT = "mcp_coder.llm.providers.langchain.agent"

#: The MCP server name both tools below claim to come from. With ``TOOL_NAME``
#: it forms the canonical ``mcp__test__ping`` the gateway reconstructs.
_SERVER = "test"

#: A second tool, deliberately matched by **no** rule, so it resolves to the
#: config default (``ALWAYS``) and must not be blocked behind a pending approval.
_UNGATED = "pong"

#: How long a test waits for the consumer thread to finish. Comfortably above
#: the provider's own ``thread.join(timeout=5)``.
_JOIN_TIMEOUT = 20.0

#: How long a test waits for an event to reach the consumer.
_EVENT_TIMEOUT = 20.0


# --- the adapter request shape ------------------------------------------------


@dataclass
class _Runtime:
    """The adapter's per-call runtime, reduced to the field the gateway reads.

    Attributes:
        tool_call_id: The model's own ``call_N`` id for this call.
    """

    tool_call_id: str


@dataclass
class _Request:
    """A ``langchain-mcp-adapters`` tool-call request, reduced to four fields.

    Attributes:
        server_name: The MCP server the call targets.
        name: The bare tool name (the gateway rebuilds ``mcp__server__tool``).
        args: The call arguments.
        runtime: Carries the emitted ``tool_call_id``.
    """

    server_name: str
    name: str
    args: dict[str, Any]
    runtime: _Runtime


@dataclass
class _ToolLog:
    """What the MCP-shaped tools recorded while a turn ran.

    Attributes:
        ran: The bare names of the calls that reached the real handler, in
            completion order — empty for a denied call.
        agent_thread: The thread the tool coroutine ran on, i.e. the provider's
            internal agent thread. Captured here because it is the one thing the
            cancel criterion asserts on and ``_ask_agent_stream`` never exposes.
    """

    ran: list[str] = field(default_factory=list)
    agent_thread: threading.Thread | None = None


# --- building blocks ----------------------------------------------------------


def _provider_config() -> dict[str, str | None]:
    """Return a minimal langchain config dict for the agent branch.

    Returns:
        The config mapping ``_ask_agent_stream`` expects.
    """
    return {
        "provider": "langchain",
        "backend": "openai",
        "model": "gpt-4o",
        "api_key": None,
        "base_url": None,
        "api_version": None,
    }


def _make_gateway(engine: ApprovalEngine) -> LangchainEnforcementGateway:
    """Build a gateway whose only rule puts ``TOOL_NAME`` behind an approval.

    Args:
        engine: The engine the ``AFTER_APPROVAL`` branch prompts through.

    Returns:
        A gateway with one authored ``ask`` rule; every other tool falls through
        to the config default, which the resolver maps to ``ALWAYS``.
    """
    config = PermissionConfig(
        rules=(Rule(Matcher(_SERVER, TOOL_NAME), Policy.AFTER_APPROVAL, "project"),)
    )
    return LangchainEnforcementGateway(config, engine)


def _make_mcp_shaped_tool(
    gateway: LangchainEnforcementGateway,
    log: _ToolLog,
    name: str,
    delay: float = 0.0,
) -> Any:
    """Build a tool that routes its own call through the permission gateway.

    Args:
        gateway: The gateway whose ``interceptor`` gates the call.
        log: Where the tool records the calls that reached the real handler and
            the agent thread it ran on.
        name: The bare tool name the model asks for.
        delay: Seconds the real handler sleeps, used to slow a looping agent.

    Returns:
        A ``StructuredTool`` usable with ``create_react_agent``.
    """
    require_real_langchain("langchain_core")

    from langchain_core.tools import (  # pylint: disable=import-error
        InjectedToolCallId,
        StructuredTool,
    )

    async def _handler(request: Any) -> str:
        """Stand in for the adapter's real downstream handler."""
        if delay:
            await asyncio.sleep(delay)
        log.ran.append(request.name)
        return f"{request.name}-ok"

    async def _call(tool_call_id: Annotated[str, InjectedToolCallId]) -> Any:
        """Enforce policy on this call, exactly as the real adapter would."""
        log.agent_thread = threading.current_thread()
        request = _Request(
            server_name=_SERVER,
            name=name,
            args={},
            runtime=_Runtime(tool_call_id=tool_call_id),
        )
        return await gateway.interceptor(request, _handler)

    # ``from __future__ import annotations`` stores the signature above as
    # *strings*, and ``StructuredTool.from_function`` resolves them with
    # ``get_type_hints`` against this module's globals — where
    # ``InjectedToolCallId`` does not exist, because the import above is
    # deliberately deferred into this function (see ``require_real_langchain``
    # for why every langchain import in this directory has to be). Rebinding the
    # annotations to the real objects makes them resolvable while keeping the id
    # genuinely injected; hard-coding it instead would void the FINDINGS §10
    # deny-pairing regression this module exists for.
    _call.__annotations__ = {
        "tool_call_id": Annotated[str, InjectedToolCallId],
        "return": Any,
    }

    return StructuredTool.from_function(
        coroutine=_call,
        name=name,
        description=f"MCP-shaped {name!r} call routed through the gateway.",
    )


def _make_two_call_model() -> Any:
    """Build a model that asks for the gated **and** the ungated tool at once.

    The Step 3 harness model asks for a single tool, which cannot express \"an
    ungated call runs while a gated one is parked\": ``ToolNode`` only runs calls
    concurrently when they arrive in the *same* ``AIMessage``. Only one test
    needs the wider shape, so the shared harness stays untouched.

    Returns:
        A fresh model instance counting its invokes on ``invoke_count``.
    """
    require_real_langchain("langchain_core")

    from langchain_core.language_models.chat_models import (  # pylint: disable=import-error
        BaseChatModel,
    )
    from langchain_core.messages import AIMessage  # pylint: disable=import-error
    from langchain_core.outputs import (  # pylint: disable=import-error
        ChatGeneration,
        ChatResult,
    )

    class _TwoCallModel(BaseChatModel):  # type: ignore[misc]
        """Two parallel tool calls on the first invoke, plain text after."""

        invoke_count: int = 0

        def bind_tools(self, tools: Any, **kw: Any) -> "_TwoCallModel":
            return self

        def _generate(self, messages, stop=None, run_manager=None, **kw):  # type: ignore[no-untyped-def]
            raise NotImplementedError(
                "_TwoCallModel implements _agenerate, not _generate"
            )

        async def _agenerate(self, messages, stop=None, run_manager=None, **kw):  # type: ignore[no-untyped-def]
            self.invoke_count += 1
            if self.invoke_count == 1:
                message = AIMessage(
                    content="",
                    tool_calls=[
                        {"name": TOOL_NAME, "args": {}, "id": "call_1"},
                        {"name": _UNGATED, "args": {}, "id": "call_2"},
                    ],
                )
            else:
                message = AIMessage(content="done")
            return ChatResult(generations=[ChatGeneration(message=message)])

        @property
        def _llm_type(self) -> str:
            return "fake-approval-two-call"

    return _TwoCallModel()


def _make_looping_model(tool_name: str) -> Any:
    """Build a model that asks for *tool_name* on **every** invoke.

    The backstop test needs a turn that is still producing events when the
    consumer closes the generator: ``run_agent_stream`` reads ``cancel_event``
    only *between* ``astream_events`` iterations, so a turn parked on a silent
    tool could never show the backstop working.

    Args:
        tool_name: The tool the model keeps asking for.

    Returns:
        A fresh model instance counting its invokes on ``invoke_count``.
    """
    require_real_langchain("langchain_core")

    from langchain_core.language_models.chat_models import (  # pylint: disable=import-error
        BaseChatModel,
    )
    from langchain_core.messages import AIMessage  # pylint: disable=import-error
    from langchain_core.outputs import (  # pylint: disable=import-error
        ChatGeneration,
        ChatResult,
    )

    class _LoopingModel(BaseChatModel):  # type: ignore[misc]
        """Never answers: one tool call per invoke, forever."""

        invoke_count: int = 0

        def bind_tools(self, tools: Any, **kw: Any) -> "_LoopingModel":
            return self

        def _generate(self, messages, stop=None, run_manager=None, **kw):  # type: ignore[no-untyped-def]
            raise NotImplementedError(
                "_LoopingModel implements _agenerate, not _generate"
            )

        async def _agenerate(self, messages, stop=None, run_manager=None, **kw):  # type: ignore[no-untyped-def]
            self.invoke_count += 1
            message = AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": tool_name,
                        "args": {},
                        "id": f"call_{self.invoke_count}",
                    }
                ],
            )
            return ChatResult(generations=[ChatGeneration(message=message)])

        @property
        def _llm_type(self) -> str:
            return "fake-approval-looping"

    return _LoopingModel()


@contextmanager
def _patched_provider(model: Any) -> Iterator[None]:
    """Run the agent branch against *model* and pre-built tools.

    Only the two things a credential-free box cannot supply are stubbed: the
    chat-model factory and the adapter/langgraph dependency assertion (``tools``
    is passed explicitly, so no MCP adapter is needed). History *loading* is
    stubbed because the session ids here are synthetic; the **write** is left
    real and lands under the autouse ``_tmp_home`` redirect.

    Args:
        model: The chat model ``_create_chat_model`` should hand back.

    Yields:
        None, with the provider's agent-mode dependencies stubbed.
    """
    with (
        patch(f"{_MOD_LC}.load_langchain_history", return_value=[]),
        patch(f"{_MOD_LC}._create_chat_model", return_value=model),
        patch(f"{_MOD_AGENT}._check_agent_dependencies"),
    ):
        yield


# --- the turn driver ----------------------------------------------------------


@dataclass
class _Live:
    """Everything one gated turn exposes to the test thread.

    Attributes:
        engine: The engine the turn is attached to.
        model: The scripted chat model, for its ``invoke_count``.
        log: What the MCP-shaped tools recorded.
        events: Stream events, appended by the consumer thread.
        errors: What escaped the consumer thread's iteration. A non-empty list
            means ``error_holder`` was re-raised out of the generator.
        escaped: What reached ``threading.excepthook``, i.e. what production
            would have printed on stderr — onto a live Textual screen.
    """

    engine: ApprovalEngine
    model: Any
    log: _ToolLog
    events: list[StreamEvent] = field(default_factory=list)
    errors: list[BaseException] = field(default_factory=list)
    escaped: list[Any] = field(default_factory=list)

    def of_type(self, event_type: str) -> list[StreamEvent]:
        """Return the recorded events of one type, in arrival order.

        Args:
            event_type: The ``type`` value to select.

        Returns:
            The matching events.
        """
        return [e for e in list(self.events) if e.get("type") == event_type]

    def types(self) -> list[str]:
        """Return the recorded event types in arrival order.

        Returns:
            One string per event.
        """
        return [str(e.get("type")) for e in list(self.events)]

    def approval_id(self) -> str:
        """Return the id carried by the first ``approval_request``.

        Returns:
            The registry key :meth:`ApprovalEngine.resolve_pending` answers with.
        """
        requests = self.of_type("approval_request")
        assert requests, "no approval_request reached the consumer"
        return str(requests[0]["approval_id"])


def _consume(gen: Iterator[StreamEvent], live: _Live) -> None:
    """Drain *gen* into *live*, recording whatever escapes.

    Args:
        gen: The provider generator, driven on this (consumer) thread.
        live: Where events and escaping exceptions are recorded.
    """
    try:
        for event in gen:
            live.events.append(event)
    except BaseException as exc:  # pylint: disable=broad-exception-caught
        live.errors.append(exc)


def _run_gated_turn(
    on_pending: Callable[[_Live], None],
    monkeypatch: pytest.MonkeyPatch,
    model: Any | None = None,
    tool_names: Sequence[str] = (TOOL_NAME,),
) -> _Live:
    """Run one turn that parks on an approval, and answer it from *this* thread.

    The generator runs on a consumer thread precisely because that is iCoder's
    topology: the thread that would answer is never the thread inside ``q.get``.

    Args:
        on_pending: Called on the test thread once an ``approval_request`` has
            reached the consumer. Typically resolves or cancels.
        monkeypatch: Used to capture ``threading.excepthook`` rather than let a
            hard cancel print a traceback.
        model: The scripted chat model; defaults to the Step 3 harness model.
        tool_names: The MCP-shaped tools to expose to the agent.

    Returns:
        The completed turn's observations.
    """
    require_real_langchain("langchain_core", "langgraph")

    from mcp_coder.llm.providers.langchain import _ask_agent_stream

    engine = ApprovalEngine()
    gateway = _make_gateway(engine)
    live = _Live(
        engine=engine,
        model=model if model is not None else make_fake_chat_model(),
        log=_ToolLog(),
    )
    tools = [_make_mcp_shaped_tool(gateway, live.log, name) for name in tool_names]
    monkeypatch.setattr(threading, "excepthook", live.escaped.append)

    with _patched_provider(live.model):
        gen = _ask_agent_stream(
            question=f"please call {TOOL_NAME}",
            config=_provider_config(),
            session_id=f"approval-e2e-{uuid4().hex}",
            mcp_config="",
            timeout=30,
            tools=tools,
            approval_bridge=engine,
        )
        consumer = threading.Thread(target=_consume, args=(gen, live), daemon=True)
        consumer.start()
        try:
            assert wait_for(
                lambda: bool(live.of_type("approval_request")), _EVENT_TIMEOUT
            ), f"no approval_request arrived; saw {live.types()}"
            on_pending(live)
            consumer.join(timeout=_JOIN_TIMEOUT)
        finally:
            if consumer.is_alive():
                # Never leave a turn parked on an unanswered approval: the pause
                # suspends both streaming timeouts, so it would wait forever.
                engine.cancel_all()
                consumer.join(timeout=_JOIN_TIMEOUT)

    assert not consumer.is_alive(), "the consumer thread never finished"
    return live


def _allow(live: _Live) -> None:
    """Approve the pending request once, from the test thread."""
    live.engine.resolve_pending(live.approval_id(), ApprovalDecision("allow", "once"))


# --- 1. allow ------------------------------------------------------------------


def test_allow_runs_the_gated_call_and_the_turn_completes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The gated call blocks, is approved, then runs; the agent continues.

    ``invoke_count == 2`` is the discriminator for \"the agent continued\": the
    second invoke can only happen after the tool result rejoined the history.
    """
    live = _run_gated_turn(_allow, monkeypatch)

    assert live.errors == [], f"the turn raised: {live.errors!r}"
    assert (
        live.escaped == []
    ), f"an exception escaped the agent thread: {live.escaped!r}"
    assert live.of_type("error") == []
    assert live.log.ran == [TOOL_NAME], "the approved call never reached the handler"
    assert live.model.invoke_count == 2, "the agent did not continue past the approval"
    assert live.of_type("done"), f"the turn never completed; saw {live.types()}"

    results = live.of_type("tool_result")
    assert len(results) == 1
    assert results[0]["output"] == f"{TOOL_NAME}-ok"
    assert results[0]["is_error"] is False


# --- 2. deny -------------------------------------------------------------------


def test_deny_returns_a_paired_error_tool_message_and_the_agent_continues(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A refusal becomes a clean ``ToolMessage(status=\"error\")``, not a wedge.

    The ``tool_call_id`` assertion is the FINDINGS §10 regression: with the
    empty id the shipped I2.3 code used, the model's ``call_1`` stays unpaired,
    ``create_react_agent`` raises ``INVALID_CHAT_HISTORY`` and ``invoke_count``
    never reaches 2. Both halves are asserted, because only the second one
    fails when the deny message is unpaired — the stream event cosmetically
    masks an empty id with the langgraph ``run_id``.
    """

    def _deny(live: _Live) -> None:
        live.engine.resolve_pending(
            live.approval_id(), ApprovalDecision("deny", "once")
        )

    live = _run_gated_turn(_deny, monkeypatch)

    assert live.errors == [], f"the turn raised: {live.errors!r}"
    assert live.of_type("error") == []
    assert live.log.ran == [], "a denied call reached the real handler"

    results = live.of_type("tool_result")
    assert len(results) == 1
    assert results[0]["is_error"] is True
    assert results[0]["output"] == _DENY_USER
    assert results[0]["tool_call_id"] == "call_1", "the deny lost the model's call id"

    assert live.model.invoke_count == 2, "the agent did not continue past the deny"
    assert live.of_type("done"), f"the turn never completed; saw {live.types()}"


# --- 3. an ungated call is not blocked behind a pending approval ---------------


def test_ungated_call_runs_while_a_gated_one_is_pending(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """One parked approval must not stall the sibling calls of the same step.

    ``ToolNode`` gathers the two calls of one ``AIMessage`` concurrently, so the
    ungated ``pong`` has to complete while ``ping`` is still parked. The
    snapshot taken *before* the answer is what makes that ordering an assertion
    rather than a coincidence of the final list.
    """
    observed: list[list[str]] = []

    def _check_then_allow(live: _Live) -> None:
        assert wait_for(
            lambda: _UNGATED in live.log.ran, _EVENT_TIMEOUT
        ), "the ungated call was blocked behind the pending approval"
        observed.append(list(live.log.ran))
        _allow(live)

    live = _run_gated_turn(
        _check_then_allow,
        monkeypatch,
        model=_make_two_call_model(),
        tool_names=(TOOL_NAME, _UNGATED),
    )

    assert observed == [[_UNGATED]], "the gated call ran before it was approved"
    assert live.errors == []
    assert sorted(live.log.ran) == sorted([_UNGATED, TOOL_NAME])
    assert live.model.invoke_count == 2
    assert live.of_type("done"), f"the turn never completed; saw {live.types()}"


# --- 4. cancel while pending ---------------------------------------------------


def test_cancel_while_pending_unwinds_the_turn_without_replanning(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``cancel_all()`` is the only path that can reach a parked interceptor.

    The four assertions are the acceptance criterion: the turn does not
    re-plan (``invoke_count == 1``), the agent thread is dead after the
    provider's own ``join(timeout=5)``, nothing reached the thread excepthook
    (i.e. nothing on stderr, over a live Textual screen), and ``error_holder``
    stayed empty — a hard cancel is an unwind, not an error.
    """
    live = _run_gated_turn(lambda live: live.engine.cancel_all(), monkeypatch)

    assert live.model.invoke_count == 1, "the turn re-planned instead of unwinding"
    assert live.log.ran == [], "the cancelled call reached the handler anyway"
    assert (
        live.escaped == []
    ), f"an exception escaped the agent thread: {live.escaped!r}"
    assert live.errors == [], f"the cancel surfaced as an error: {live.errors!r}"
    assert live.of_type("error") == []

    agent_thread = live.log.agent_thread
    assert agent_thread is not None, "the tool coroutine never ran"
    assert (
        agent_thread.is_alive() is False
    ), "agent thread still parked after join(5) — the cancel did not unwind it"


# --- 5. the generic backstop still works with nothing pending ------------------


def test_generator_close_still_stops_a_turn_with_no_approval_pending(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """With nothing parked, closing the consumer still ends the turn.

    The direct cancel channel exists because the generic paths cannot reach a
    parked interceptor — not because they stopped working. Here the tool is
    ungated, so events keep flowing and ``run_agent_stream``'s ``cancel_event``
    check is reachable again: ``GeneratorExit`` sets it, the agent breaks at its
    next event, and the agent thread is dead well inside the 5s join.
    """
    require_real_langchain("langchain_core", "langgraph")

    from mcp_coder.llm.providers.langchain import _ask_agent_stream

    engine = ApprovalEngine()
    gateway = _make_gateway(engine)
    log = _ToolLog()
    escaped: list[Any] = []
    monkeypatch.setattr(threading, "excepthook", escaped.append)
    model = _make_looping_model(_UNGATED)
    tool = _make_mcp_shaped_tool(gateway, log, _UNGATED, delay=0.05)

    with _patched_provider(model):
        # Cast because ``_ask_agent_stream`` is annotated with the wider
        # ``Iterator``, and this test needs ``close()`` to reach the
        # ``GeneratorExit`` path.
        gen = cast(
            Generator[StreamEvent, None, None],
            _ask_agent_stream(
                question=f"please call {_UNGATED}",
                config=_provider_config(),
                session_id=f"approval-e2e-{uuid4().hex}",
                mcp_config="",
                timeout=30,
                tools=[tool],
                approval_bridge=engine,
            ),
        )
        seen: list[str] = []
        for event in gen:
            seen.append(str(event.get("type")))
            if event.get("type") == "tool_result":
                break
        started = time.monotonic()
        gen.close()
        elapsed = time.monotonic() - started

    assert "tool_result" in seen, f"the turn produced no tool result; saw {seen}"
    assert engine.pending() == 0, "nothing should have been pending in this turn"
    assert engine.is_attached() is False, "the turn never detached"
    assert escaped == [], f"an exception escaped the agent thread: {escaped!r}"
    assert elapsed < 5.0, (
        f"close() burned the whole join budget ({elapsed:.1f}s) — the backstop "
        "did not stop the agent"
    )

    agent_thread = log.agent_thread
    assert agent_thread is not None, "the tool coroutine never ran"
    assert (
        agent_thread.is_alive() is False
    ), "agent thread still alive after join(5) — the backstop did not stop the turn"


# --- 6. ordering ---------------------------------------------------------------


def test_approval_request_arrives_after_that_tools_tool_use_start(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The request for a call cannot precede that call's own start row.

    #1045 flags this as a scheduling claim that was never verified: the
    interceptor runs *inside* the tool coroutine, and ``on_tool_start`` fires
    before that coroutine is awaited, so ``tool_use_start`` should reach the
    queue first. A wrong result here is cosmetic — I3.3 would pop a modal for a
    row not yet drawn — so it is reported, not designed around (R17 already
    says the two events share no correlation key).
    """
    live = _run_gated_turn(_allow, monkeypatch)

    types = live.types()
    assert "tool_use_start" in types, f"no tool_use_start was emitted; saw {types}"
    assert "approval_request" in types, f"no approval_request was emitted; saw {types}"
    assert types.index("tool_use_start") < types.index("approval_request"), (
        "approval_request overtook its own tool_use_start — the interceptor "
        f"emitted before langgraph's on_tool_start reached the queue: {types}"
    )
