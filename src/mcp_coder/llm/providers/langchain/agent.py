"""Agent utilities for MCP tool-use support in the LangChain provider.

Provides environment variable substitution, MCP server configuration loading,
and the core agent execution function for the LangChain agent mode (issue #517).
"""

from __future__ import annotations

import asyncio
import copy
import json
import logging
import os
import re
import threading
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

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


_KNOWN_FIELDS = {"command", "args", "env", "transport", "type"}


def _resolve_env_vars(value: str, env: dict[str, str]) -> str:
    """Replace ``${VAR}`` placeholders in *value* with values from *env*.

    Unknown variables are left as-is (``${UNKNOWN}`` stays unchanged).
    Uses a single-pass ``re.sub`` so replacement values that themselves
    contain ``${…}`` patterns are **not** re-substituted.

    Returns:
        The input string with all known ``${VAR}`` placeholders replaced by
        their corresponding values from *env*.
    """
    pattern = r"\$\{([^}]+)\}"

    def _replacer(match: re.Match[str]) -> str:
        var_name = match.group(1)
        return env.get(var_name, match.group(0))

    return re.sub(pattern, _replacer, value)


def _load_mcp_server_config(
    mcp_config_path: str,
    env_vars: dict[str, str] | None = None,
) -> dict[str, dict[str, object]]:
    """Load an ``.mcp.json`` file and resolve ``${VAR}`` placeholders.

    Args:
        mcp_config_path: Absolute path to the ``.mcp.json`` configuration file.
            Callers should use ``resolve_mcp_config_path()`` from ``cli/utils.py``.
        env_vars: Optional extra environment variables. These are merged on top
            of ``os.environ`` (i.e. *env_vars* wins on conflicts).

    Returns:
        Mapping of server names to their resolved configuration, suitable for
        ``MultiServerMCPClient``.

    Raises:
        ValueError: If MCP config file is not found or invalid.
    """
    path = Path(mcp_config_path)
    with open(path, encoding="utf-8") as fh:
        try:
            raw_config: dict[str, object] = json.load(fh)
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"Failed to parse MCP config file {mcp_config_path}: {exc}"
            ) from exc

    # Build merged environment: os.environ as base, env_vars overrides
    merged_env: dict[str, str] = {**os.environ, **(env_vars or {})}

    servers_raw = raw_config.get("mcpServers")
    if not isinstance(servers_raw, dict):
        raise ValueError(
            f"Expected 'mcpServers' dict in {mcp_config_path}, "
            f"got {type(servers_raw).__name__}"
        )

    result: dict[str, dict[str, object]] = {}

    for server_name, server_cfg in servers_raw.items():
        if not isinstance(server_cfg, dict):
            logger.warning(
                "Skipping non-dict server entry %r in %s",
                server_name,
                mcp_config_path,
            )
            continue

        resolved: dict[str, object] = {}

        for key, value in server_cfg.items():
            if key not in _KNOWN_FIELDS:
                logger.warning(
                    "Unknown field %r (value: %r) in server %r — ignoring",
                    key,
                    value,
                    server_name,
                )
                continue

            if key == "command" and isinstance(value, str):
                resolved["command"] = _resolve_env_vars(value, merged_env)
            elif key == "args" and isinstance(value, list):
                resolved["args"] = [
                    (
                        _resolve_env_vars(item, merged_env)
                        if isinstance(item, str)
                        else item
                    )
                    for item in value
                ]
            elif key == "env" and isinstance(value, dict):
                resolved["env"] = {
                    k: _resolve_env_vars(v, merged_env) if isinstance(v, str) else v
                    for k, v in value.items()
                }
            elif key == "type":
                # 'type' is a VS Code / Claude Desktop convention;
                # MultiServerMCPClient uses 'transport' instead.
                pass
            elif key == "transport" and isinstance(value, str) and value != "stdio":
                logger.warning(
                    "Server %r specifies transport %r — only 'stdio' is "
                    "supported; falling back to 'stdio'",
                    server_name,
                    value,
                )
            else:
                resolved[key] = value

        # Always set transport to stdio
        resolved["transport"] = "stdio"

        result[server_name] = resolved

    return result


def _sanitize_tool_schema(schema: dict[str, Any]) -> dict[str, Any]:
    """Return a copy of *schema* with a ``type`` for every property.

    Some MCP servers (e.g. FastMCP with ``Any``-typed parameters) emit
    property definitions like ``{"title": "Content"}`` without a ``type``
    field.  ``langchain-mcp-adapters`` passes these schemas to Pydantic's
    ``StructuredTool`` which rejects them.

    This function adds ``"type": "string"`` as a safe default for any
    property that is missing both ``type`` and ``anyOf``/``allOf``/``oneOf``.

    A deep copy is made so the original MCP tool schema is never mutated.

    Returns:
        A deep copy of the schema dict with ``"type": "string"`` added to any
        property that was missing type information.
    """
    schema = copy.deepcopy(schema)

    props = schema.get("properties")
    if not isinstance(props, dict):
        return schema

    for prop_name, prop_def in props.items():
        if not isinstance(prop_def, dict):
            continue
        has_type_info = any(
            k in prop_def for k in ("type", "anyOf", "allOf", "oneOf", "$ref")
        )
        if not has_type_info:
            prop_def["type"] = "string"
            logger.debug("Added default type 'string' to schema property %r", prop_name)

    return schema


async def run_agent(
    question: str,
    chat_model: BaseChatModel,
    messages: list[dict[str, Any]],
    mcp_config_path: str,
    execution_dir: str | None = None,  # pylint: disable=unused-argument
    env_vars: dict[str, str] | None = None,
    timeout: int = 30,
) -> tuple[str, list[dict[str, Any]], dict[str, Any]]:
    """Run a LangGraph ReAct agent with MCP tools.

    Args:
        question: The user question / prompt to send to the agent.
        chat_model: A LangChain ``BaseChatModel`` instance (e.g. from a backend).
        messages: Prior conversation history as a list of dicts (LangChain native
            serialization via ``.dict()`` / ``messages_from_dict()``).
        mcp_config_path: Absolute path to the ``.mcp.json`` configuration file.
        execution_dir: Optional working directory (currently unused, reserved
            for future).
        env_vars: Optional extra environment variables for MCP server resolution.
        timeout: Maximum time in seconds for the agent invocation.

    Returns:
        ``(final_text, full_message_history, stats_dict)``.
        *stats_dict* contains: ``agent_steps``, ``total_tool_calls``,
        ``tool_trace``.
    """
    # Deferred imports — only needed when agent mode is active
    from langchain_core.messages import (
        AIMessage,
        HumanMessage,
        ToolMessage,
        messages_from_dict,
    )
    from langchain_mcp_adapters.client import MultiServerMCPClient
    from langchain_mcp_adapters.tools import convert_mcp_tool_to_langchain_tool
    from langgraph.prebuilt import create_react_agent

    server_config = _load_mcp_server_config(mcp_config_path, env_vars)

    # Load tools with schema sanitization.
    # We cannot use MultiServerMCPClient.get_tools() directly because it
    # passes raw MCP schemas to StructuredTool, which fails on properties
    # without a 'type' field (e.g. FastMCP Any-typed params).
    client = MultiServerMCPClient(cast(Any, server_config))
    all_tools = []
    for server_name, connection in client.connections.items():
        async with client.session(server_name) as session:
            raw_tools = await session.list_tools()
            for tool in raw_tools.tools:
                sanitized = _sanitize_tool_schema(tool.inputSchema)
                # Shallow copy to avoid mutating the original MCP tool
                tool = tool.model_copy(update={"inputSchema": sanitized})
                lc_tool = convert_mcp_tool_to_langchain_tool(
                    None,
                    tool,
                    connection=connection,
                    server_name=server_name,
                )
                all_tools.append(lc_tool)

    agent = create_react_agent(chat_model, all_tools)

    # Build input: prior history + new question
    input_messages = messages_from_dict(messages) + [HumanMessage(content=question)]

    result = await asyncio.wait_for(
        agent.ainvoke(
            {"messages": input_messages},
            config={"recursion_limit": AGENT_MAX_STEPS},
        ),
        timeout=float(timeout),
    )

    output_messages = result["messages"]

    # Extract final text from the last AIMessage
    final_text = ""
    for msg in reversed(output_messages):
        if isinstance(msg, AIMessage):
            final_text = msg.content if isinstance(msg.content, str) else ""
            break

    # Compute stats
    agent_steps = 0
    total_tool_calls = 0
    tool_trace: list[dict[str, Any]] = []
    trace_by_id: dict[str, dict[str, Any]] = {}

    for msg in output_messages:
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
    for msg in output_messages:
        if isinstance(msg, ToolMessage):
            tc_id = getattr(msg, "tool_call_id", "")
            if tc_id and tc_id in trace_by_id:
                trace_by_id[tc_id]["result"] = msg.content

    stats: dict[str, Any] = {
        "agent_steps": agent_steps,
        "total_tool_calls": total_tool_calls,
        "tool_trace": tool_trace,
    }

    # Serialize full history in the format expected by messages_from_dict:
    # {"type": "human", "data": {"content": "...", ...}}
    serialized: list[dict[str, Any]] = []
    for msg in output_messages:
        if hasattr(msg, "model_dump"):
            dump = cast(dict[str, Any], msg.model_dump())
        else:
            dump = cast(dict[str, Any], msg.dict())
        msg_type = dump.pop("type", "unknown")
        serialized.append({"type": msg_type, "data": dump})

    return (final_text, serialized, stats)


async def run_agent_stream(
    question: str,
    chat_model: BaseChatModel,
    messages: list[dict[str, Any]],
    mcp_config_path: str,
    session_id: str,
    cancel_event: threading.Event | None = None,
    execution_dir: str | None = None,  # pylint: disable=unused-argument
    env_vars: dict[str, str] | None = None,
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
        execution_dir: Optional working directory (reserved for future).
        env_vars: Optional extra environment variables for MCP server resolution.

    Yields:
        ``StreamEvent`` dicts: ``text_delta``, ``tool_use_start``,
        ``tool_result``, ``raw_line``, ``error``, and ``done``.
    """
    from langchain_core.messages import (
        AIMessage,
        HumanMessage,
        ToolMessage,
        messages_from_dict,
    )
    from langchain_mcp_adapters.client import MultiServerMCPClient
    from langchain_mcp_adapters.tools import convert_mcp_tool_to_langchain_tool
    from langgraph.prebuilt import create_react_agent

    server_config = _load_mcp_server_config(mcp_config_path, env_vars)

    # Load tools with schema sanitization (inline, same as run_agent)
    client = MultiServerMCPClient(cast(Any, server_config))
    all_tools = []
    for server_name, connection in client.connections.items():
        async with client.session(server_name) as session:
            raw_tools = await session.list_tools()
            for tool in raw_tools.tools:
                sanitized = _sanitize_tool_schema(tool.inputSchema)
                tool = tool.model_copy(update={"inputSchema": sanitized})
                lc_tool = convert_mcp_tool_to_langchain_tool(
                    None,
                    tool,
                    connection=connection,
                    server_name=server_name,
                )
                all_tools.append(lc_tool)

    agent = create_react_agent(chat_model, all_tools)

    input_messages = messages_from_dict(messages) + [HumanMessage(content=question)]

    # Accumulators for history reconstruction
    accumulated_text = ""
    tool_calls_by_run_id: dict[str, dict[str, Any]] = {}
    tool_results_list: list[dict[str, Any]] = []

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
                tool_calls_by_run_id[run_id] = {"name": name, "args": input_data}
                yield {
                    "type": "tool_use_start",
                    "name": name,
                    "args": json.dumps(input_data),
                    "tool_call_id": run_id,
                }

            elif event_kind == "on_tool_end":
                output = event.get("data", {}).get("output", "")
                run_id = event.get("run_id", "")
                name = event.get("name", "")
                tool_call_id = getattr(output, "tool_call_id", None) or run_id
                tool_results_list.append(
                    {
                        "name": name,
                        "output": str(output),
                        "tool_call_id": tool_call_id,
                        "run_id": run_id,
                    }
                )
                yield {
                    "type": "tool_result",
                    "name": name,
                    "output": str(output),
                    "tool_call_id": tool_call_id,
                }

    except Exception as exc:
        yield {"type": "error", "message": str(exc)}
        raise

    # Reconstruct and store conversation history
    ai_tool_calls = []
    for run_id, tc_info in tool_calls_by_run_id.items():
        result_entry = next(
            (r for r in tool_results_list if r["run_id"] == run_id), None
        )
        tc_id = result_entry["tool_call_id"] if result_entry else run_id
        ai_tool_calls.append(
            {"name": tc_info["name"], "args": tc_info["args"], "id": tc_id}
        )

    history_messages = list(input_messages)
    if accumulated_text or ai_tool_calls:
        ai_kwargs: dict[str, Any] = {"content": accumulated_text}
        if ai_tool_calls:
            ai_kwargs["tool_calls"] = ai_tool_calls
        history_messages.append(AIMessage(**ai_kwargs))
    for tr in tool_results_list:
        history_messages.append(
            ToolMessage(content=tr["output"], tool_call_id=tr["tool_call_id"])
        )

    serialized: list[dict[str, Any]] = []
    for msg in history_messages:
        if hasattr(msg, "model_dump"):
            dump = cast(dict[str, Any], msg.model_dump())
        else:
            dump = cast(dict[str, Any], msg.dict())
        msg_type = dump.pop("type", "unknown")
        serialized.append({"type": msg_type, "data": dump})

    from mcp_coder.llm.storage.session_storage import (
        store_langchain_history as _store_history,
    )

    _store_history(session_id, serialized)

    yield {"type": "done", "session_id": session_id}
