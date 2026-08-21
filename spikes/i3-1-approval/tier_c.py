"""Tier C — real MCP + real ``tool_interceptors``, end-to-end (Step 5, #1044).

The HEAVIEST tier and the central go/no-go of the spike. A throwaway FastMCP
**stdio** server (``server.py``, D4) is driven through a real ``MCPManager`` with
a real ``tool_interceptors=[gate.interceptor]``, over a stubbed ``FakeChatModel``
(from ``_common.py``). It proves, on the REAL langchain-mcp-adapters call path:

  * ``scenario_resume`` — the real interceptor coroutine actually FIRES even with
    the model stubbed (``gate.fired``); its loop identity, captured *inside* the
    coroutine via ``asyncio.get_running_loop()`` (D6), equals the AGENT loop
    (an independent reference: ``FakeChatModel.loop_id``) and is DISTINCT from
    the ``MCPManager`` daemon loop; and on resolve the agent proceeds PAST the
    gated call (tool_result + the fake's final ``'done'`` text).
  * ``scenario_deny`` — the shipped ``build_deny_tool_message`` returns a
    ``ToolMessage(status="error")`` and the agent still reaches its final
    message (#5), plus a **recorded probe** (F13, NOT a gating assert) of
    whether langgraph's ``ToolNode`` fills the empty post-deny ``tool_call_id``.

Run directly::

    python spikes/i3-1-approval/tier_c.py

Requires the REAL ``langchain`` / ``langgraph`` / ``langchain-mcp-adapters>=0.3``
/ ``mcp`` in the venv. Exits 0 with a ``PASS:`` line per mechanic; the deny
``tool_call_id`` probe prints ``PASS: deny-tool-call-id-filled`` OR
``OBSERVED: deny-tool-call-id-empty (...)`` and exits 0 EITHER way. Every OTHER
assertion is gating (raises ``AssertionError`` -> non-zero exit).
"""

from __future__ import annotations

import asyncio
import sys
import threading
import uuid
from pathlib import Path
from typing import Any, Callable

from langchain_core.messages import AIMessage, ToolMessage

# Allow ``python spikes/i3-1-approval/tier_c.py`` to import the sibling module.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import FakeChatModel, wait_for  # noqa: E402

from mcp_coder.llm.providers.langchain.agent import run_agent_stream  # noqa: E402
from mcp_coder.llm.providers.langchain.mcp_manager import MCPManager  # noqa: E402
from mcp_coder.llm.providers.langchain.permission_bridge import (  # noqa: E402
    build_deny_tool_message,
)

_SERVER_PATH = str(Path(__file__).resolve().parent / "server.py")
_DENY_TEXT = "This tool requires approval — not yet available."
_EMITTED_TOOL_CALL_ID = "call_1"


def _tier_c_script() -> list[AIMessage]:
    """Two-invoke script for the REAL ``ping(text)`` tool.

    Unlike ``_common._default_script`` (whose ``args={}`` suits Tier B's
    no-arg blocking tool), the real server tool requires ``text``; langgraph's
    ToolNode validates the tool_call against the tool schema BEFORE the tool
    coroutine — hence the interceptor — runs, so an empty ``args`` would fail
    validation and the interceptor would never fire. Invoke 1 -> tool_call to
    ``ping`` with ``text``; invoke 2 -> assistant text ``'done'``.
    """
    return [
        AIMessage(
            content="",
            tool_calls=[
                {"name": "ping", "args": {"text": "spike"}, "id": _EMITTED_TOOL_CALL_ID}
            ],
        ),
        AIMessage(content="done"),
    ]


class InterceptorGate:
    """Real async ``tool_interceptors`` hook: ``(request, handler) -> Any``.

    Named ``InterceptorGate``, not ``Gate``, so it cannot be confused with
    ``_common.Gate`` (the blocking-tool cross-thread handoff) — different
    mechanism, different file (F14).

    ``deny=False`` (approve): record fire + loop identity, publish a fresh
    Future, ``await`` it (a bare resolver thread approves via
    ``call_soon_threadsafe``), then delegate to the real ``handler``.
    ``deny=True``: record fire + loop identity, then return the shipped deny
    ``ToolMessage`` WITHOUT awaiting (no resolver needed).
    """

    def __init__(self, deny: bool = False) -> None:
        self.deny = deny
        self.fired: bool = False
        self.loop_id: int | None = None
        self.loop: asyncio.AbstractEventLoop | None = None  # captured inside (D6)
        self.future: asyncio.Future[str] | None = None  # the pending approval

    async def interceptor(
        self, request: Any, handler: Callable[[Any], Any]
    ) -> Any:
        """Record fire + loop identity; approve -> await Future -> handler.

        The loop handle is obtained with ``asyncio.get_running_loop()`` INSIDE
        the coroutine (never a build-time handle on the daemon loop) — this is
        the D6 fact on the real adapter path, and ``self.fired`` is the
        "interceptor really fired" assertion.
        """
        self.loop = asyncio.get_running_loop()
        self.loop_id = id(self.loop)
        self.future = self.loop.create_future()
        self.fired = True

        if self.deny:
            # Explicit "" keeps this frozen spike run byte-identical to the
            # pre-#1118 behaviour it recorded (empty tool_call_id).
            return build_deny_tool_message(_DENY_TEXT, request.name, "")

        # Approve: block until a bare thread resolves the Future, then run the
        # real MCP tool via the downstream handler.
        await self.future
        return await handler(request)


def build_server_config() -> dict[str, dict[str, object]]:
    """Return the stdio server dict for the throwaway FastMCP ``ping`` server.

    ``command=sys.executable`` + absolute ``server.py`` path keeps the spike
    CWD-independent (Notes).
    """
    return {
        "spike": {
            "command": sys.executable,
            "args": [_SERVER_PATH],
            "transport": "stdio",
        }
    }


def _run_agent_collect(
    model: FakeChatModel, tools: list[Any]
) -> tuple[list[Any], threading.Thread, list[BaseException]]:
    """Drive the REAL agent over ``tools`` on its own ``asyncio.run`` loop.

    Returns ``(events, thread, errors)``. ``events`` fills live as the agent
    streams; ``thread`` is the agent loop thread (same loop the interceptor and
    ``FakeChatModel._agenerate`` run on); ``errors`` captures any exception the
    stream raised so the caller can surface it instead of it vanishing on the
    worker thread.
    """
    events: list[Any] = []
    errors: list[BaseException] = []

    def _thread_main() -> None:
        async def _collect() -> None:
            async for event in run_agent_stream(
                question="please call ping",
                chat_model=model,
                messages=[],
                mcp_config_path="",
                session_id=f"spike-i3-1-tierc-{uuid.uuid4()}",
                tools=tools,
            ):
                events.append(event)

        try:
            asyncio.run(_collect())
        except BaseException as exc:  # noqa: BLE001  # pylint: disable=broad-except
            errors.append(exc)

    thread = threading.Thread(target=_thread_main, daemon=True)
    thread.start()
    return events, thread, errors


def _assistant_text_in_stream(events: list[Any], text: str) -> bool:
    """Was the fake's final assistant ``text`` visible in the event stream?

    The stubbed model implements ``_agenerate`` (not ``_astream``), so langchain
    falls back to a single non-streaming ``ainvoke`` and emits NO
    ``on_chat_model_stream`` -> the driver yields no ``text_delta`` for it (a
    Tier-C gotcha for FINDINGS). The assistant message still surfaces on the
    ``on_chat_model_end`` event, which the driver mirrors verbatim as a
    ``raw_line`` (``json.dumps(event, default=str)``), so the content is
    observable there.
    """
    needle = f"content='{text}'"
    return any(
        e.get("type") == "raw_line" and needle in e.get("line", "") for e in events
    )


def _final_tool_message(model: FakeChatModel) -> ToolMessage | None:
    """Return the ``ToolMessage`` in the fake's SECOND-invoke message list.

    That list is the post-``ToolNode`` state the agent handed the model on
    invoke 2, so its ``ToolMessage`` carries whatever ``tool_call_id``
    ``ToolNode`` produced downstream (the deny probe reads it).
    """
    messages = model.last_messages or []
    for msg in messages:
        if isinstance(msg, ToolMessage):
            return msg
    return None


def scenario_resume() -> None:
    """Approve path: interceptor fired on the AGENT loop + agent proceeds past."""
    gate = InterceptorGate(deny=False)
    manager = MCPManager(build_server_config(), tool_interceptors=[gate.interceptor])
    try:
        tools = manager.tools()
        daemon_loop_id = id(manager._loop)  # MCPManager daemon loop (mcp_manager.py)
        assert tools, "no tools discovered from the spike MCP server"

        model = FakeChatModel(responses=_tier_c_script())
        events, thread, errors = _run_agent_collect(model, tools)

        # Bare resolver thread: PUSH the approval onto the agent loop once the
        # interceptor has published its Future (never poll the Future object).
        def _resolver() -> None:
            if wait_for(lambda: gate.loop is not None and gate.future is not None):
                assert gate.loop is not None and gate.future is not None
                gate.loop.call_soon_threadsafe(gate.future.set_result, "approve")

        threading.Thread(target=_resolver, daemon=True).start()

        thread.join(timeout=60)
        assert not thread.is_alive(), "agent thread did not finish within 60s"
        assert not errors, f"agent stream raised: {errors[0]!r}"

        # --- the interceptor really fired (even with the model stubbed) ---
        assert gate.fired is True, "real interceptor coroutine never fired"
        print("PASS: interceptor-fired")

        # --- D6 loop identity, the go/no-go, on the REAL adapter path ---
        assert gate.loop_id is not None
        assert model.loop_id is not None, "FakeChatModel never recorded its loop"
        assert gate.loop_id == model.loop_id, (
            f"interceptor loop {gate.loop_id} != agent loop {model.loop_id} "
            "(interceptor did NOT run on the agent loop)"
        )
        assert gate.loop_id != daemon_loop_id, (
            f"interceptor loop {gate.loop_id} == MCPManager daemon loop "
            f"{daemon_loop_id} (should be distinct)"
        )
        print(
            f"PASS: loop-identity-real-path "
            f"(agent={gate.loop_id} daemon={daemon_loop_id})"
        )

        # --- agent proceeded PAST the gate (NOT the unconditional done event) ---
        tool_results = [e for e in events if e.get("type") == "tool_result"]
        assert tool_results, "no tool_result event — agent never got past the gate"
        assert model.invoke_count == 2, (
            f"agent did not invoke the model a 2nd time (invoke_count="
            f"{model.invoke_count}); it did not proceed past the gate"
        )
        assert _assistant_text_in_stream(events, "done"), (
            "the fake's final 'done' assistant message never surfaced in the "
            f"stream. event types seen: {[e.get('type') for e in events]}"
        )
        # The real ping echoes text="spike" straight back through MCP.
        assert any("spike" in str(e.get("output", "")) for e in tool_results), (
            f"tool_result did not carry the echoed MCP output: {tool_results!r}"
        )
        print("PASS: resume-past-gate")
    finally:
        manager.close()


def _wedged_on_empty_id(errors: list[BaseException]) -> bool:
    """Did the run raise langgraph's INVALID_CHAT_HISTORY over the deny call?

    The empty ``tool_call_id`` on the deny ``ToolMessage`` leaves the agent's
    ``ping``/``call_1`` tool_call unpaired; ``create_react_agent`` validates the
    history on the NEXT turn and raises a ``ValueError`` naming the unpaired
    call. That error IS the post-``ToolNode`` proof the id stayed empty.
    """
    if not errors:
        return False
    text = str(errors[0])
    return "corresponding ToolMessage" in text and _EMITTED_TOOL_CALL_ID in text


def scenario_deny() -> None:
    """Deny path: ToolMessage(status='error') shape + tool_call_id probe (F13).

    The deny shape (``status='error'``) is a gating assert. Whether the agent
    then CONTINUES is not independent of the probe: it is gated on ``ToolNode``
    filling the empty ``tool_call_id``. So continuation and the probe are
    determined jointly, and the empty-id branch (agent wedges) is a valid
    RECORDED finding under F13 — exit 0 either way; only a genuinely
    unexplained state raises.
    """
    gate = InterceptorGate(deny=True)
    manager = MCPManager(build_server_config(), tool_interceptors=[gate.interceptor])
    try:
        tools = manager.tools()
        assert tools, "no tools discovered from the spike MCP server"

        model = FakeChatModel(responses=_tier_c_script())
        events, thread, errors = _run_agent_collect(model, tools)

        thread.join(timeout=60)
        assert not thread.is_alive(), "agent thread did not finish within 60s"

        # --- GATING: the real deny interceptor fired ---
        assert gate.fired is True, "deny interceptor never fired"

        # --- GATING: shipped deny shape reached the stream as status='error' ---
        tool_results = [e for e in events if e.get("type") == "tool_result"]
        assert tool_results, "deny produced no tool_result event"
        assert any(e.get("is_error") is True for e in tool_results), (
            f"deny tool_result not flagged is_error: {tool_results!r}"
        )
        assert any(_DENY_TEXT in str(e.get("output", "")) for e in tool_results), (
            f"deny tool_result did not carry the deny text: {tool_results!r}"
        )
        print("PASS: deny-shape")  # ToolMessage(status='error') surfaced

        # --- RECORDED PROBE (F13) + continuation, determined jointly ---
        tm = _final_tool_message(model)
        continued = model.invoke_count == 2 and not errors
        filled = tm is not None and tm.tool_call_id == _EMITTED_TOOL_CALL_ID

        if continued and filled:
            # ToolNode filled the empty id; agent looped back and finished.
            print("PASS: deny-tool-call-id-filled")
            assert _assistant_text_in_stream(events, "done"), (
                "agent did not reach its final 'done' message after deny"
            )
            print("PASS: deny-continues")
        elif continued and not filled:
            # Empty id survived but the (stub) history validation let it pass and
            # the agent still continued — the id is empty, continuation holds.
            tcid = tm.tool_call_id if tm is not None else None
            print(
                "OBSERVED: deny-tool-call-id-empty "
                f"(finding for I3.2 / latent I2.3 bug) [tool_call_id={tcid!r}]"
            )
            print("OBSERVED: deny-continues-despite-empty-id")
        elif _wedged_on_empty_id(errors):
            # THE OBSERVED OUTCOME on this platform/stack: ToolNode did NOT fill
            # the id (permission_bridge's 'ToolNode overwrites it' docstring is
            # FALSE); the unpaired history makes create_react_agent raise
            # INVALID_CHAT_HISTORY on the next turn, so the deny path WEDGES the
            # agent (invoke_count stays 1). Both facts are recorded findings.
            print(
                "OBSERVED: deny-tool-call-id-empty "
                "(finding for I3.2 / latent I2.3 bug) "
                "[ToolNode did NOT fill it -> langgraph INVALID_CHAT_HISTORY]"
            )
            print(
                "OBSERVED: deny-path-wedges-agent "
                "(empty tool_call_id -> unpaired history -> agent does NOT "
                f"continue past deny; invoke_count={model.invoke_count})"
            )
        else:
            raise AssertionError(
                "unexplained deny outcome: "
                f"invoke_count={model.invoke_count} errors={errors!r} tm={tm!r}"
            )
    finally:
        manager.close()


def main() -> None:
    scenario_resume()
    scenario_deny()


if __name__ == "__main__":
    main()
