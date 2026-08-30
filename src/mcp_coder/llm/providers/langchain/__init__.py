"""LangChain provider package.

Entry point for the LangChain provider. Supports OpenAI, Gemini, and Anthropic backends.
All LangChain library imports are deferred to the backend modules so that
importing this package does not fail when langchain is not installed.
"""

from __future__ import annotations

import asyncio
import json
import queue
import threading
import time
from collections.abc import Iterator
from datetime import datetime
from typing import Any

from mcp_coder.llm.storage.session_storage import (
    load_langchain_history,
    store_langchain_history,
)
from mcp_coder.llm.types import LLM_RESPONSE_VERSION, LLMResponseDict, StreamEvent

from ._config_diagnostics import dialed_url
from ._errors_404 import _format_404_hint
from ._errors_404 import _is_404_error as _is_404_error  # re-exported for tests
from ._exceptions import LLMMCPLaunchError
from ._messages import assemble_messages, serialize_messages
from ._preflight import _ollama_preflight

# Re-exported: the call sites below stay in this module, so the existing
# `mcp_coder.llm.providers.langchain._load_langchain_config` / `._create_chat_model`
# patches keep resolving through this module's globals.
from ._setup import _build_system_messages as _build_system_messages
from ._setup import _create_chat_model as _create_chat_model
from ._setup import _handle_provider_error as _handle_provider_error
from ._setup import _load_langchain_config as _load_langchain_config
from ._setup import _resolve_session_id as _resolve_session_id
from ._usage import _extract_usage
from .approval_bridge import ApprovalBridge

# Agent streaming timeout constants (seconds)
_AGENT_OVERALL_TIMEOUT = 3600  # 60 minutes


def ask_langchain(
    question: str,
    session_id: str | None = None,
    timeout: int = 30,
    mcp_config: str | None = None,
    env_vars: dict[str, str] | None = None,
    system_prompt: str | None = None,
    project_prompt: str | None = None,
) -> LLMResponseDict:
    """Entry point called by interface.prompt_llm() for provider='langchain'.

    When *mcp_config* is provided the request is routed through the LangGraph
    ReAct agent (agent mode).  Otherwise the existing text-only backend
    dispatch is used.

    Args:
        question: The user's prompt text.
        session_id: Optional session ID for conversation history.
        timeout: Request timeout in seconds.
        mcp_config: Optional path to .mcp.json for agent mode.
        env_vars: Optional environment variables for agent subprocesses.
        system_prompt: Optional system-level prompt text.
        project_prompt: Optional project-level prompt text.

    Returns:
        LLMResponseDict with the model's response.

    Raises:
        ValueError: If the langchain backend is not configured, or if
            *session_id* was supplied but has no history file.
    """
    config = _load_langchain_config()
    backend = config["backend"]

    if not backend:
        raise ValueError(
            "llm.langchain.backend not configured. "
            "Set [llm.langchain] backend in config.toml "
            "or MCP_CODER_LLM_LANGCHAIN_BACKEND env var."
        )

    sid = _resolve_session_id(session_id)
    sys_msgs = _build_system_messages(system_prompt, project_prompt)

    if mcp_config:
        # Agent mode needs a longer timeout than text mode — MCP tool calls
        # involve multiple subprocess round-trips.
        agent_timeout = max(timeout, 300)
        return _ask_agent(
            question=question,
            config=config,
            session_id=sid,
            mcp_config=mcp_config,
            env_vars=env_vars,
            timeout=agent_timeout,
            system_messages=sys_msgs,
        )

    return _ask_text(
        question=question,
        config=config,
        backend=backend,
        session_id=sid,
        timeout=timeout,
        system_messages=sys_msgs,
    )


def _ask_text(
    question: str,
    config: dict[str, str | None],
    backend: str | None,
    session_id: str,
    timeout: int,
    system_messages: list[Any] | None = None,
) -> LLMResponseDict:
    """Text-only backend dispatch using unified chat model factory.

    Args:
        question: The user's prompt text.
        config: LangChain configuration dict.
        backend: Backend name ("openai", "gemini", "anthropic").
        session_id: Session ID for conversation history.
        timeout: Request timeout in seconds.
        system_messages: Optional list of system messages to prepend.

    Returns:
        LLMResponseDict with the model's text response.

    Raises:
        ValueError: If the model is not found on the configured backend.
    """  # Also raises LLMAuthError / LLMConnectionError via _handle_provider_error.
    history = load_langchain_history(session_id)
    lc_messages = assemble_messages(system_messages, history, question)

    chat_model = _create_chat_model(config, timeout=timeout)

    try:
        ai_msg = chat_model.invoke(lc_messages)
    except Exception as exc:
        _handle_provider_error(exc, backend, dialed_url(chat_model))
        if _is_404_error(exc):
            raise ValueError(_format_404_hint(config)) from exc
        raise

    text = ai_msg.content if isinstance(ai_msg.content, str) else str(ai_msg.content)

    raw: dict[str, object] = {
        "backend": backend,
        "model": config.get("model", ""),
        "response_content": text,
        "usage": _extract_usage(ai_msg),
    }

    store_langchain_history(session_id, serialize_messages(lc_messages + [ai_msg]))

    return LLMResponseDict(
        version=LLM_RESPONSE_VERSION,
        timestamp=datetime.now().isoformat(),
        text=text,
        session_id=session_id,
        provider="langchain",
        raw_response=raw,
    )


def _ask_agent(
    question: str,
    config: dict[str, str | None],
    session_id: str,
    mcp_config: str,
    env_vars: dict[str, str] | None = None,
    timeout: int = 30,
    system_messages: list[Any] | None = None,
) -> LLMResponseDict:
    """Agent mode: route through LangGraph ReAct agent with MCP tools.

    Args:
        question: The user's prompt text.
        config: LangChain configuration dict.
        session_id: Session ID for conversation history.
        mcp_config: Path to .mcp.json configuration file.
        env_vars: Optional environment variables for agent subprocesses.
        timeout: Request timeout in seconds.
        system_messages: Optional list of system messages to prepend.

    Returns:
        LLMResponseDict with the agent's text response and tool usage stats.
        ``session_id`` is None when no history file exists for the session; a
        resumed session whose turn stored nothing keeps its id. The rule lives
        in ``run_agent_stream``'s done event and ``run_agent`` relays it.
    """  # Also raises LLMAuthError / LLMConnectionError via _handle_provider_error.
    from .agent import _check_agent_dependencies, run_agent

    _check_agent_dependencies()
    _ollama_preflight(config)

    chat_model = _create_chat_model(config, timeout=timeout)
    history: list[dict[str, Any]] = load_langchain_history(session_id)

    agent_backend = config.get("backend")
    try:
        text, messages, stats, resumable_sid = asyncio.run(
            run_agent(
                question=question,
                chat_model=chat_model,
                messages=history,
                mcp_config_path=mcp_config,
                session_id=session_id,
                env_vars=env_vars,
                timeout=timeout,
                system_messages=system_messages,
            )
        )
    except Exception as exc:
        _handle_provider_error(exc, agent_backend, dialed_url(chat_model))
        raise

    # No storage here: run_agent drains run_agent_stream, which is the single
    # persistence site for the agent path.
    raw_response: dict[str, Any] = {
        "messages": messages,
        "backend": config.get("backend", ""),
        "model": config.get("model", ""),
        **stats,
    }

    return LLMResponseDict(
        version=LLM_RESPONSE_VERSION,
        timestamp=datetime.now().isoformat(),
        text=text,
        session_id=resumable_sid,
        provider="langchain",
        raw_response=raw_response,
    )


#: ``done`` keys that exist only for the in-process drainer of
#: ``run_agent_stream`` and must not cross the provider boundary.
_INTERNAL_DONE_KEYS = ("messages", "stats")


def _strip_internal_done_keys(event: StreamEvent) -> StreamEvent:
    """Return *event* without the drainer-only ``done`` keys.

    ``done["messages"]`` is the whole serialized conversation and
    ``done["stats"]["tool_trace"]`` repeats every tool call's name/args/result.
    Both are consumed only by the in-process drainer, which reads
    ``run_agent_stream`` directly; every consumer above this boundary instead
    *persists* the event — into ``raw_response["events"]`` via
    ``ResponseAssembler`` and into the icoder JSONL event log via
    ``AppCore.stream_llm`` — so leaving ``messages`` on would grow both sinks
    quadratically with turn count. Stripping both here, once, is what keeps
    those consumers free of their own filters.

    ``result`` is deliberately *not* stripped: ``ResponseAssembler`` uses it as
    the response text when no ``text_delta`` was seen.

    Args:
        event: A stream event from ``run_agent_stream``.

    Returns:
        Non-``done`` events unchanged; ``done`` events as a shallow copy
        without the internal keys.
    """
    if event.get("type") != "done":
        return event
    return {k: v for k, v in event.items() if k not in _INTERNAL_DONE_KEYS}


def _ask_agent_stream(
    question: str,
    config: dict[str, str | None],
    session_id: str,
    mcp_config: str,
    env_vars: dict[str, str] | None = None,
    timeout: int = 30,
    tools: list[Any] | None = None,
    system_messages: list[Any] | None = None,
    approval_bridge: ApprovalBridge | None = None,
) -> Iterator[StreamEvent]:
    """Stream agent events via thread+queue bridge from async to sync.

    Runs ``run_agent_stream()`` in a background thread with ``asyncio.run()``
    and bridges events through a ``queue.Queue``.

    Args:
        question: The user's prompt text.
        config: LangChain configuration dict.
        session_id: Session ID for conversation history.
        mcp_config: Path to .mcp.json configuration file.
        env_vars: Optional environment variables for agent subprocesses.
        timeout: Request timeout in seconds.
        tools: Optional pre-built LangChain tools (e.g. from MCPManager).
            When provided, skips MultiServerMCPClient creation.
        system_messages: Optional list of system messages to prepend.
        approval_bridge: Optional runtime approval engine. Attached to this
            turn's queue for the whole turn, so an ``ask``-gated tool call can
            emit an ``approval_request`` and park on a human decision. Both
            streaming timeouts are suspended while it reports pending work.

    Yields:
        StreamEvent dicts from the agent.

    Raises:
        TimeoutError: If no-progress or overall timeout is exceeded.
    """
    from .agent import _check_agent_dependencies, run_agent_stream

    _check_agent_dependencies()
    _ollama_preflight(config)
    chat_model = _create_chat_model(config, timeout=timeout)
    history: list[dict[str, Any]] = load_langchain_history(session_id)

    q: queue.Queue[StreamEvent | None] = queue.Queue()
    error_holder: list[Exception] = []
    cancel = threading.Event()
    cancelled = False

    # Cleanup is conditioned on its own setup having succeeded: `thread` is bound
    # inside the `try` below, so an `attach()` failure would leave it unbound and
    # a `thread.start()` failure would leave it unstarted — either would raise
    # out of the `finally` and mask the original exception.
    thread: threading.Thread | None = None
    thread_started = False
    attached = False

    # A pending approval suspends both timeouts as a timestamped *window*, not as
    # keepalive events: the overall cap is checked inside the consumer loop after
    # `q.get()` returns, so keepalives would arm it rather than reset it, and they
    # would also reach the session .jsonl and the replay path.
    start = time.monotonic()
    paused = 0.0
    pause_began: float | None = None
    pause_epoch = 0

    def _sync_pause() -> None:
        """Open or close the pending window from the bridge's count."""
        nonlocal paused, pause_began, pause_epoch
        waiting = approval_bridge is not None and approval_bridge.pending() > 0
        now = time.monotonic()
        if waiting and pause_began is None:
            pause_began = now
        elif not waiting and pause_began is not None:
            paused += now - pause_began  # real wall time, not `timeout` units
            pause_began = None
            # ... and the inactivity budget of any wait this window overlapped
            # is void (see the `queue.Empty` branch).
            pause_epoch += 1

    def _elapsed() -> float:
        """Return the turn's elapsed time with every human pause deducted."""
        now = time.monotonic()
        open_window = now - pause_began if pause_began is not None else 0.0
        return (now - start) - paused - open_window

    try:
        # First statement in the try: everything below can fail, and the engine
        # must never stay attached to a dead turn.
        if approval_bridge is not None:
            approval_bridge.attach(q.put)
            attached = True

        async def _run() -> None:
            try:
                async for event in run_agent_stream(
                    question=question,
                    chat_model=chat_model,
                    messages=history,
                    mcp_config_path=mcp_config,
                    session_id=session_id,
                    cancel_event=cancel,
                    env_vars=env_vars,
                    tools=tools,
                    system_messages=system_messages,
                ):
                    q.put(_strip_internal_done_keys(event))
            except asyncio.CancelledError:
                # Hard cancel: the approval engine cancelled the future a parked
                # interceptor was awaiting, which unwinds the whole turn. This is
                # expected, not an error, so `error_holder` stays empty. It needs
                # its own clause because `CancelledError` is a `BaseException`:
                # `agent.py`'s `except Exception` misses it and so does the one
                # below, and `_thread_main` is a bare `asyncio.run`, which would
                # print the traceback on stderr — i.e. onto a live Textual screen.
                pass
            except Exception as exc:  # pylint: disable=broad-except
                error_holder.append(exc)
            finally:
                q.put(None)  # sentinel

        def _thread_main() -> None:
            asyncio.run(_run())

        thread = threading.Thread(target=_thread_main, daemon=True)
        thread.start()
        thread_started = True

        while True:
            epoch_at_wait_start = pause_epoch  # snapshot BEFORE the wait
            try:
                event = q.get(timeout=timeout)
            except queue.Empty as exc:
                _sync_pause()
                # Re-wait on a still-open pause, and equally on one that opened
                # and closed inside this wait: `q.get` gives every call a fresh
                # `timeout`, so a pause overlapping the wait would otherwise eat
                # the whole budget and trip the inactivity error moments after
                # the user approved. Only a wait with no pause at all may raise.
                if pause_began is not None or pause_epoch != epoch_at_wait_start:
                    continue
                cancel.set()
                raise TimeoutError(
                    f"LLM inactivity timeout (langchain): no response for {timeout}s. "
                    "Connection closed. You can retry, or use --timeout to increase the limit."
                ) from exc
            _sync_pause()  # sampled before the yield blocks on the UI
            if event is None:
                break
            if _elapsed() > _AGENT_OVERALL_TIMEOUT:
                cancel.set()
                raise TimeoutError(
                    f"Agent execution exceeded {_AGENT_OVERALL_TIMEOUT}s overall timeout"
                )
            yield event
    except GeneratorExit:
        cancel.set()
        cancelled = True
    finally:
        # Detach BEFORE the join, never after: detach cancels every still-pending
        # future, which is the only thing that can unpark an interceptor blocked
        # on one. Joining first would burn the full 5s and return with the agent
        # thread still parked. On the normal path the registry is already empty
        # and this is a no-op.
        if attached and approval_bridge is not None:
            approval_bridge.detach()
        if thread is not None and thread_started:
            thread.join(timeout=5)

    # If the async thread raised an exception but the consumer exited
    # normally (sentinel received), re-raise that error. Skipped when
    # cancelled (GeneratorExit) to avoid masking the exit.
    if error_holder and not cancelled:
        held_exc = error_holder[0]
        _handle_provider_error(held_exc, config.get("backend"), dialed_url(chat_model))
        raise held_exc


def ask_langchain_stream(
    question: str,
    session_id: str | None = None,
    timeout: int = 600,
    mcp_config: str | None = None,
    env_vars: dict[str, str] | None = None,
    tools: list[Any] | None = None,
    system_prompt: str | None = None,
    project_prompt: str | None = None,
    approval_bridge: ApprovalBridge | None = None,
) -> Iterator[StreamEvent]:
    """Stream LangChain responses as events.

    Same parameters as ask_langchain(). For text mode (no mcp_config),
    routes to _ask_text_stream() for real streaming. For agent mode
    (mcp_config present), routes to _ask_agent_stream() for real
    streaming via thread+queue bridge.

    ``approval_bridge`` is the optional runtime approval engine; it only
    reaches the agent branch. The text branch has no tools to gate, so it
    ignores the bridge entirely — non-iCoder CLI callers pass nothing and keep
    working unchanged.

    Yields:
        StreamEvent dicts: text_delta, tool_use_start, tool_result, done, error, raw_line

    Raises:
        ValueError: If the langchain backend is not configured, or if
            *session_id* was supplied but has no history file.
    """
    config = _load_langchain_config()
    backend = config["backend"]

    if not backend:
        raise ValueError(
            "llm.langchain.backend not configured. "
            "Set [llm.langchain] backend in config.toml "
            "or MCP_CODER_LLM_LANGCHAIN_BACKEND env var."
        )

    sid = _resolve_session_id(session_id)
    sys_msgs = _build_system_messages(system_prompt, project_prompt)

    if mcp_config:
        yield from _ask_agent_stream(
            question=question,
            config=config,
            session_id=sid,
            mcp_config=mcp_config,
            env_vars=env_vars,
            timeout=timeout,
            tools=tools,
            system_messages=sys_msgs,
            approval_bridge=approval_bridge,
        )
        return

    yield from _ask_text_stream(
        question=question,
        config=config,
        backend=backend,
        session_id=sid,
        timeout=timeout,
        system_messages=sys_msgs,
    )


def _ask_text_stream(
    question: str,
    config: dict[str, str | None],
    backend: str | None,
    session_id: str,
    timeout: int,
    system_messages: list[Any] | None = None,
) -> Iterator[StreamEvent]:
    """Stream text-only responses using chat_model.stream().

    Yields:
        raw_line events for each chunk (JSON serialization),
        text_delta events for each chunk, then done event.

    Raises:
        ValueError: If the model is not found (404/NOT_FOUND in error).
        TimeoutError: If no LLM output is received within the timeout period.
    """
    from langchain_core.messages import AIMessage

    history = load_langchain_history(session_id)
    lc_messages = assemble_messages(system_messages, history, question)

    chat_model = _create_chat_model(config, timeout=timeout)

    try:
        all_text_parts: list[str] = []
        last_chunk_with_usage: Any = None
        last_activity = time.time()
        for chunk in chat_model.stream(lc_messages):
            if time.time() - last_activity > timeout:
                raise TimeoutError(
                    f"LLM inactivity timeout (langchain): no output for {timeout}s. "
                    "Stream stalled. You can retry, or use --timeout to increase the limit."
                )
            last_activity = time.time()
            if getattr(chunk, "usage_metadata", None):
                last_chunk_with_usage = chunk
            chunk_dict = (
                chunk.model_dump() if hasattr(chunk, "model_dump") else chunk.dict()
            )
            yield {"type": "raw_line", "line": json.dumps(chunk_dict)}
            content = (
                chunk.content if isinstance(chunk.content, str) else str(chunk.content)
            )
            yield {"type": "text_delta", "text": content}
            all_text_parts.append(content)

        # Store history with the complete AI response
        full_text = "".join(all_text_parts)
        ai_msg = AIMessage(content=full_text)
        store_langchain_history(session_id, serialize_messages(lc_messages + [ai_msg]))

        usage = _extract_usage(last_chunk_with_usage) if last_chunk_with_usage else {}
        yield {"type": "done", "session_id": session_id, "usage": usage}
    except TimeoutError:
        raise
    except Exception as exc:
        _handle_provider_error(exc, backend, dialed_url(chat_model))
        # Handle 404/model-not-found errors (mirrors _ask_text() path)
        if _is_404_error(exc):
            hint = _format_404_hint(config)
            yield {"type": "error", "message": hint}
            raise ValueError(hint) from exc
        yield {"type": "error", "message": str(exc)}
        raise
