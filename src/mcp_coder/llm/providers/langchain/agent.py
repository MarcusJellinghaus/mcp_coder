"""Agent utilities for MCP tool-use support in the LangChain provider.

Provides the core agent execution functions for the LangChain agent mode
(issue #517). MCP server configuration loading, environment variable
substitution and tool building live in ``_mcp_tools``.
"""

from __future__ import annotations

import asyncio
import inspect
import json
import logging
import threading
from typing import TYPE_CHECKING, Any, cast

from mcp_coder.llm.types import UsageInfo

from ._exceptions import LLMMCPLaunchError
from ._mcp_tools import (
    _convert_server_tools,
    _format_launch_error,
    _load_mcp_server_config,
)
from ._messages import assemble_messages, serialize_messages
from ._usage import _extract_usage, _sum_usage

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from langchain_core.language_models import BaseChatModel

    from mcp_coder.llm.types import StreamEvent

logger = logging.getLogger(__name__)

AGENT_MAX_STEPS: int = 50


def _check_agent_dependencies() -> None:
    """Runtime import check for langchain-mcp-adapters and langgraph.

    Raises:
        ImportError: If required packages are missing, with clear install
            instructions.
    """
    missing: list[str] = []
    try:
        import langchain_mcp_adapters  # noqa: F401  # pylint: disable=unused-import
    except ImportError:
        missing.append("langchain-mcp-adapters")
    try:
        import langgraph  # noqa: F401  # pylint: disable=unused-import
    except ImportError:
        missing.append("langgraph")
    if missing:
        packages = " ".join(missing)
        raise ImportError(
            f"Agent mode requires additional packages: {', '.join(missing)}.\n"
            f"Install with: pip install {packages}"
        )
    _assert_tool_interceptors_supported()


def _assert_tool_interceptors_supported() -> None:
    """Raise ImportError if the installed adapter lacks ``tool_interceptors``.

    Permission enforcement (issue I2.3) rides on the ``tool_interceptors``
    parameter of ``convert_mcp_tool_to_langchain_tool``, added in
    ``langchain-mcp-adapters>=0.3.0``. This reusable helper fails fast with a
    clear upgrade message so a ``<0.3.0`` adapter does not instead raise a raw
    ``TypeError: unexpected keyword argument 'tool_interceptors'`` at the first
    ``convert_...(tool_interceptors=...)`` call.

    The ``inspect.signature`` call is guarded so a non-introspectable or
    mock stand-in cannot be misread as an unsupported adapter:

    * If the signature cannot be read at all (``TypeError``/``ValueError``),
      the check is a silent no-op.
    * If the callable accepts arbitrary ``**kwargs`` (the shape reported for the
      langchain conftest ``MagicMock`` stand-in, ``(*args, **kwargs)``), then it
      would accept a ``tool_interceptors`` keyword too, so the check does not
      block.

    Raises:
        ImportError: If ``convert_mcp_tool_to_langchain_tool`` has an
            introspectable, fixed signature that does not accept a
            ``tool_interceptors`` parameter.
    """
    from langchain_mcp_adapters.tools import convert_mcp_tool_to_langchain_tool

    try:
        params = inspect.signature(convert_mcp_tool_to_langchain_tool).parameters
    except (TypeError, ValueError):
        # Not introspectable — cannot determine capability, so do not block.
        return
    if "tool_interceptors" in params:
        return
    if any(p.kind is inspect.Parameter.VAR_KEYWORD for p in params.values()):
        # Accepts arbitrary **kwargs (e.g. the conftest MagicMock stand-in whose
        # signature is (*args, **kwargs)) — tool_interceptors would be accepted
        # too, so this is not an unsupported real adapter.
        return
    raise ImportError(
        "Permission enforcement requires langchain-mcp-adapters>=0.3.0 "
        "(the installed version does not support tool_interceptors). "
        "Upgrade with: pip install 'langchain-mcp-adapters>=0.3.0'"
    )


def _is_node_cancelled(exc: BaseException) -> bool:
    """Return whether ``exc`` is langgraph's wrapper for a cancelled node.

    langgraph's retry layer converts an ``asyncio.CancelledError`` raised by a
    node body — which is what the approval engine's hard cancel (R7) produces
    inside ``ToolNode`` — into ``NodeCancelledError``, an ordinary
    ``Exception``. Without this check the cancel would be reported as a failed
    turn: it would match every ``except Exception`` on the way out and match no
    ``except asyncio.CancelledError`` at all.

    The import is deferred and guarded because langgraph is an optional extra,
    and because ``NodeCancelledError`` only exists in newer releases while
    ``pyproject.toml`` deliberately sets no upper bound.

    Args:
        exc: The exception caught while draining the agent stream.

    Returns:
        True if ``exc`` is a ``NodeCancelledError``, False otherwise —
        including when langgraph is absent or too old to define it.
    """
    try:
        from langgraph.errors import (  # pylint: disable=import-outside-toplevel
            NodeCancelledError,
        )
    except ImportError:
        return False
    return isinstance(exc, NodeCancelledError)


def _summarize_messages(messages: list[Any]) -> tuple[str, dict[str, Any]]:
    """Derive final text and tool stats from a graph's final message list.

    ``run_agent_stream`` is the sole caller — ``run_agent`` reaches it by
    draining that generator, so both agent entry points share this summary.
    Usage is deliberately *not* derived here: the stream owns it, accumulated
    from ``on_chat_model_end`` events, and adds it to these stats at the
    ``done`` yield site.

    Args:
        messages: The graph's final message list.

    Returns:
        ``(final_text, stats)`` where *final_text* is the content of the last
        ``AIMessage`` and *stats* carries ``agent_steps``, ``total_tool_calls``
        and ``tool_trace``.
    """
    from langchain_core.messages import AIMessage, ToolMessage

    # Extract final text from the last AIMessage
    final_text = ""
    for msg in reversed(messages):
        if isinstance(msg, AIMessage):
            final_text = msg.content if isinstance(msg.content, str) else ""
            break

    agent_steps = 0
    total_tool_calls = 0
    tool_trace: list[dict[str, Any]] = []
    trace_by_id: dict[str, dict[str, Any]] = {}

    for msg in messages:
        if isinstance(msg, AIMessage) and getattr(msg, "tool_calls", None):
            agent_steps += 1
            for tc in msg.tool_calls:
                total_tool_calls += 1
                entry: dict[str, Any] = {
                    "name": tc["name"],
                    "args": tc["args"],
                    "result": "",
                }
                tool_trace.append(entry)
                tc_id: str = tc.get("id") or ""
                if tc_id:
                    trace_by_id[tc_id] = entry

    # Fill tool results from ToolMessages, matched by tool_call_id
    for msg in messages:
        if isinstance(msg, ToolMessage):
            tc_id = getattr(msg, "tool_call_id", "")
            if tc_id and tc_id in trace_by_id:
                trace_by_id[tc_id]["result"] = msg.content

    stats: dict[str, Any] = {
        "agent_steps": agent_steps,
        "total_tool_calls": total_tool_calls,
        "tool_trace": tool_trace,
    }
    return (final_text, stats)


async def run_agent(
    question: str,
    chat_model: BaseChatModel,
    messages: list[dict[str, Any]],
    mcp_config_path: str,
    session_id: str,
    env_vars: dict[str, str] | None = None,
    timeout: int = 30,
    system_messages: list[Any] | None = None,
) -> tuple[str, list[dict[str, Any]], dict[str, Any], str | None]:
    """Run a LangGraph ReAct agent with MCP tools (non-streaming).

    A thin drainer of :func:`run_agent_stream`: it consumes that generator and
    returns what the terminal ``done`` event carries. Both agent entry points
    therefore persist an identical multi-step structure by construction, rather
    than via two reconstructions that happen to agree.

    **Storage happens inside** :func:`run_agent_stream` — this function stores
    nothing itself.

    Args:
        question: The user question / prompt to send to the agent.
        chat_model: A LangChain ``BaseChatModel`` instance (e.g. from a backend).
        messages: Prior conversation history as a list of dicts (LangChain native
            serialization via ``.dict()`` / ``messages_from_dict()``).
        mcp_config_path: Absolute path to the ``.mcp.json`` configuration file.
        session_id: Session identifier; ``run_agent_stream`` stores the resulting
            history under it.
        env_vars: Optional extra environment variables for MCP server resolution.
        timeout: Maximum time in seconds for the whole agent run. Note this now
            also covers MCP tool discovery: the drainer wraps the entire
            generator, whereas the previous implementation timed only the
            ``ainvoke`` call and left tool loading untimed.
        system_messages: Optional list of system messages to prepend to the
            conversation.

    Returns:
        ``(final_text, stored_messages, stats_dict, session_id)``.
        *stats_dict* contains: ``agent_steps``, ``total_tool_calls``,
        ``tool_trace`` and ``usage`` — all but ``usage`` are omitted when the
        run produced no terminal graph event, since they are derived from the
        final message list that is missing in that case.
        *session_id* is whatever the terminal ``done`` event carries, i.e.
        ``None`` when that event dropped the id as unresumable. The drainer
        reports the stream's decision rather than making its own.

    Raises:
        LLMMCPLaunchError: If an MCP server fails to launch (e.g. executable
            not found or permission denied).
        asyncio.TimeoutError: If the run exceeds *timeout* seconds.
    """  # noqa: DOC502 - both propagate: LLMMCPLaunchError from the drained
    # generator, asyncio.TimeoutError from the asyncio.wait_for below.

    async def _drain() -> tuple[str, list[dict[str, Any]], dict[str, Any], str | None]:
        final_text = ""
        stored: list[dict[str, Any]] = []
        stats: dict[str, Any] = {}
        resumable_sid: str | None = None
        async for event in run_agent_stream(
            question=question,
            chat_model=chat_model,
            messages=messages,
            mcp_config_path=mcp_config_path,
            session_id=session_id,
            env_vars=env_vars,
            system_messages=system_messages,
        ):
            if event.get("type") == "done":
                final_text = str(event.get("result", ""))
                stored = cast(list[dict[str, Any]], event.get("messages", []))
                stats = cast(dict[str, Any], event.get("stats", {}))
                # Absent when the stream judged the id unresumable.
                raw_sid = event.get("session_id")
                resumable_sid = raw_sid if isinstance(raw_sid, str) else None
        return (final_text, stored, stats, resumable_sid)

    return await asyncio.wait_for(_drain(), timeout=float(timeout))


async def run_agent_stream(
    question: str,
    chat_model: BaseChatModel,
    messages: list[dict[str, Any]],
    mcp_config_path: str,
    session_id: str,
    cancel_event: threading.Event | None = None,
    env_vars: dict[str, str] | None = None,
    tools: list[Any] | None = None,
    system_messages: list[Any] | None = None,
) -> AsyncIterator[StreamEvent]:
    """Stream agent execution events as an async generator.

    Uses LangChain's ``astream_events(version="v2")`` to yield incremental
    events as the agent processes tools and generates text.

    Args:
        question: The user question / prompt to send to the agent.
        chat_model: A LangChain ``BaseChatModel`` instance.
        messages: Prior conversation history as a list of dicts.
        mcp_config_path: Absolute path to the ``.mcp.json`` configuration file.
        session_id: Session identifier for history storage.
        cancel_event: Optional threading.Event to signal early cancellation.
        env_vars: Optional extra environment variables for MCP server resolution.
        tools: Optional pre-built LangChain tools (e.g. from MCPManager).
            When provided, skips MultiServerMCPClient creation.
        system_messages: Optional list of system messages to prepend to the
            conversation.

    Yields:
        ``StreamEvent`` dicts: ``text_delta``, ``tool_use_start``,
        ``tool_result``, ``raw_line``, ``error``, and ``done``. The ``done``
        event carries ``session_id``, ``usage``, the stored (system-free)
        ``messages``, the final ``result`` text and nested ``stats``.
        ``messages`` and ``stats`` are for in-process drainers only —
        ``_ask_agent_stream`` strips them at the provider boundary.
        Without a terminal graph event (cancelled turn, or no ``on_chain_end``
        matching the root ``run_id``) ``stats`` carries ``usage`` alone: the
        tool stats come from the final message list, so they are omitted
        rather than reported as zeros. Such a turn also drops ``session_id``
        unless a history file already exists for it — nothing was stored, so
        the id is not resumable and chaining it would fail the next turn.

    Raises:
        LLMMCPLaunchError: If an MCP server fails to launch (e.g. executable
            not found or permission denied).
        asyncio.CancelledError: If a hard cancel (R7) aborted a tool node.
            langgraph wraps the node's ``CancelledError`` in a
            ``NodeCancelledError``; it is unwrapped back to a
            ``CancelledError`` so callers see a cancel, not a failed turn.
    """
    from langgraph.prebuilt import create_react_agent

    if tools is not None:
        all_tools = tools
    else:
        from langchain_mcp_adapters.client import MultiServerMCPClient

        server_config = _load_mcp_server_config(mcp_config_path, env_vars)

        # Load tools with schema sanitization.
        # We cannot use MultiServerMCPClient.get_tools() directly because it
        # passes raw MCP schemas to StructuredTool, which fails on properties
        # without a 'type' field (e.g. FastMCP Any-typed params).
        client = MultiServerMCPClient(cast(Any, server_config))
        all_tools = []
        for server_name, connection in client.connections.items():
            try:
                async with client.session(server_name) as session:
                    raw_tools = await session.list_tools()
                    all_tools.extend(
                        _convert_server_tools(raw_tools.tools, connection, server_name)
                    )
            except (FileNotFoundError, PermissionError) as exc:
                raise LLMMCPLaunchError(
                    _format_launch_error(
                        server_name, server_config[server_name].get("command"), exc
                    )
                ) from exc

    agent = create_react_agent(chat_model, all_tools)

    input_messages = assemble_messages(system_messages, messages, question)

    # `accumulated_text` no longer feeds history reconstruction, but it is the
    # `result` fallback when no terminal graph event is captured. Without it
    # that branch would emit `result: ""`, and the non-stream agent path (which
    # drains this generator and reads `final_text` off that key) would return an
    # empty answer instead of merely skipping storage.
    accumulated_text = ""
    accumulated_usage: UsageInfo = {}
    root_run_id: str | None = None
    terminal_event_seen = False
    final_messages: list[Any] | None = None

    try:
        async for event in agent.astream_events(
            {"messages": input_messages},
            version="v2",
            config={"recursion_limit": AGENT_MAX_STEPS},
        ):
            if cancel_event and cancel_event.is_set():
                break

            yield {"type": "raw_line", "line": json.dumps(event, default=str)}

            event_kind = event.get("event", "")

            if event_kind == "on_chat_model_stream":
                chunk = event.get("data", {}).get("chunk")
                content = chunk.content if chunk else ""
                if isinstance(content, str) and content:
                    accumulated_text += content
                    yield {"type": "text_delta", "text": content}
                elif isinstance(content, list):
                    for block in content:
                        if isinstance(block, dict) and block.get("type") == "text":
                            text = block.get("text", "")
                            if text:
                                accumulated_text += text
                                yield {"type": "text_delta", "text": text}

            elif event_kind == "on_tool_start":
                run_id = event.get("run_id", "")
                input_data = event.get("data", {}).get("input", {})
                name = event.get("name", "")
                yield {
                    "type": "tool_use_start",
                    "name": name,
                    "args": input_data,
                    "tool_call_id": run_id,
                    "tool_run_id": run_id,
                }

            elif event_kind == "on_chat_model_end":
                output_msg = event.get("data", {}).get("output")
                if output_msg is not None:
                    msg_usage = _extract_usage(output_msg)
                    if msg_usage:
                        accumulated_usage = _sum_usage(accumulated_usage, msg_usage)

            elif event_kind == "on_tool_end":
                output = event.get("data", {}).get("output", "")
                run_id = event.get("run_id", "")
                name = event.get("name", "")
                tool_call_id = getattr(output, "tool_call_id", None) or run_id

                # Cascading content extraction from ToolMessage
                result_text: str | None = None
                if hasattr(output, "artifact") and isinstance(output.artifact, dict):
                    sc = output.artifact.get("structured_content")
                    if sc is not None:
                        result_text = json.dumps(sc)
                if result_text is None and hasattr(output, "content"):
                    if isinstance(output.content, list):
                        result_text = "\n".join(
                            b["text"]
                            for b in output.content
                            if isinstance(b, dict) and b.get("type") == "text"
                        )
                    elif isinstance(output.content, str):
                        result_text = output.content
                if result_text is None:
                    result_text = str(output)

                # A ToolMessage with status == "error" signals a failed tool.
                # Surface tool errors via is_error so the stream continues
                # rather than aborting the turn.
                is_error = getattr(output, "status", None) == "error"

                yield {
                    "type": "tool_result",
                    "name": name,
                    "output": result_text,
                    "tool_call_id": tool_call_id,
                    "tool_run_id": run_id,
                    "is_error": is_error,
                }

            elif event_kind == "on_chain_start":
                if root_run_id is None:
                    # The first on_chain_start is the outermost graph run.
                    root_run_id = event.get("run_id")

            elif (
                event_kind == "on_chain_end"
                and root_run_id is not None
                and event.get("run_id") == root_run_id
            ):
                # Matching by root run_id rather than by event name:
                # astream_events emits one on_chain_end per node/sub-chain, and
                # the names are version-specific LangGraph internals.
                terminal_event_seen = True
                chain_output = event.get("data", {}).get("output")
                if isinstance(chain_output, dict) and "messages" in chain_output:
                    final_messages = list(chain_output["messages"])
                else:
                    logger.warning(
                        "Terminal graph event carried no 'messages'; "
                        "history not stored"
                    )

    except Exception as exc:
        if _is_node_cancelled(exc):
            # Hard cancel (R7) wearing langgraph's wrapper: restore it to the
            # `CancelledError` the caller's cancel clause is written against,
            # and emit no error event — the user cancelled, nothing failed.
            raise asyncio.CancelledError(str(exc)) from exc
        yield {"type": "error", "message": str(exc)}
        raise

    if final_messages is None:
        # Cancelled, or no terminal graph event: there is no clean final
        # message list, so persist nothing and leave prior history untouched.
        # The streamed answer text still survives on `result`.
        if not terminal_event_seen and not (cancel_event and cancel_event.is_set()):
            # Not a cancel, and the malformed-output warning above did not fire
            # either: no on_chain_end ever matched the root run_id. Losing the
            # turn silently would look like an agent that forgets everything,
            # so make it visible.
            logger.warning(
                "No terminal graph event matched the root run_id for session "
                "%s; history not stored (the turn is not recorded)",
                session_id,
            )
        from mcp_coder.llm.storage.session_storage import langchain_history_exists

        # Tool stats are derived from the final message list, which is exactly
        # what is missing here. Reporting zeros would claim "no tools ran" for a
        # turn that may have made several calls, so the three tool-stat keys are
        # omitted entirely and only `usage` — which the stream accumulated
        # itself and therefore does know — is reported.
        done: StreamEvent = {
            "type": "done",
            "usage": accumulated_usage,
            "messages": [],
            "result": accumulated_text,
            "stats": {"usage": accumulated_usage},
        }
        # The id is only handed back when it is actually resumable. A brand-new
        # session stored nothing, so advertising it would make the next turn
        # raise on the missing history file instead of continuing. A resumed
        # session keeps its id: the prior history is still on disk.
        if langchain_history_exists(session_id):
            done["session_id"] = session_id
        yield done
        return

    # The graph's own final message list is the persisted history; the shared
    # serializer strips the leading SystemMessage(s) that were prepended for
    # this call. This is the single storage site for the agent path.
    stored = serialize_messages(final_messages)

    from mcp_coder.llm.storage.session_storage import (
        store_langchain_history as _store_history,
    )

    _store_history(session_id, stored)

    final_text, stats = _summarize_messages(final_messages)

    yield {
        "type": "done",
        "session_id": session_id,
        "usage": accumulated_usage,
        "messages": stored,
        "result": final_text,
        # Usage is the stream's own on_chat_model_end accumulator;
        # _summarize_messages covers only text and tool stats.
        "stats": {**stats, "usage": accumulated_usage},
    }
