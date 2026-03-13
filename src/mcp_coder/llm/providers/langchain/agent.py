"""Agent utilities for MCP tool-use support in the LangChain provider.

Provides environment variable substitution, MCP server configuration loading,
and the core agent execution function for the LangChain agent mode (issue #517).
"""

import json
import logging
import os
import re
from pathlib import Path
from typing import Any, cast

logger = logging.getLogger(__name__)

AGENT_MAX_STEPS: int = 50


def _check_agent_dependencies() -> None:
    """Runtime import check for langchain-mcp-adapters and langgraph.

    Raises ImportError with clear install instructions if missing.
    """
    missing: list[str] = []
    try:
        import langchain_mcp_adapters  # noqa: F401
    except ImportError:
        missing.append("langchain-mcp-adapters")
    try:
        import langgraph  # noqa: F401
    except ImportError:
        missing.append("langgraph")
    if missing:
        packages = " ".join(missing)
        raise ImportError(
            f"Agent mode requires additional packages: {', '.join(missing)}.\n"
            f"Install with: pip install {packages}"
        )


_KNOWN_FIELDS = {"command", "args", "env", "transport"}


def _resolve_env_vars(value: str, env: dict[str, str]) -> str:
    """Replace ``${VAR}`` placeholders in *value* with values from *env*.

    Unknown variables are left as-is (``${UNKNOWN}`` stays unchanged).
    Uses a single-pass ``re.sub`` so replacement values that themselves
    contain ``${…}`` patterns are **not** re-substituted.
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

    Parameters
    ----------
    mcp_config_path:
        Absolute path to the ``.mcp.json`` configuration file.
        (Callers should use ``resolve_mcp_config_path()`` from ``cli/utils.py``.)
    env_vars:
        Optional extra environment variables.  These are merged on top of
        ``os.environ`` (i.e. *env_vars* wins on conflicts).

    Returns
    -------
    dict
        Mapping of server names to their resolved configuration, suitable for
        ``MultiServerMCPClient``.
    """
    path = Path(mcp_config_path)
    with open(path, encoding="utf-8") as fh:
        raw_config: dict[str, object] = json.load(fh)

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
            else:
                resolved[key] = value

        # Always set transport to stdio
        resolved["transport"] = "stdio"

        result[server_name] = resolved

    return result


async def run_agent(
    question: str,
    chat_model: Any,
    messages: list[dict[str, object]],
    mcp_config_path: str,
    execution_dir: str | None = None,
    env_vars: dict[str, str] | None = None,
) -> tuple[str, list[dict[str, object]], dict[str, object]]:
    """Run a LangGraph ReAct agent with MCP tools.

    Parameters
    ----------
    question:
        The user question / prompt to send to the agent.
    chat_model:
        A LangChain ``BaseChatModel`` instance (e.g. from a backend).
    messages:
        Prior conversation history as a list of dicts (LangChain native
        serialization via ``.dict()`` / ``messages_from_dict()``).
    mcp_config_path:
        Absolute path to the ``.mcp.json`` configuration file.
    execution_dir:
        Optional working directory (currently unused, reserved for future).
    env_vars:
        Optional extra environment variables for MCP server resolution.

    Returns
    -------
    tuple
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
    from langgraph.prebuilt import create_react_agent

    server_config = _load_mcp_server_config(mcp_config_path, env_vars)

    async with MultiServerMCPClient(cast(Any, server_config)) as client:
        tools = await client.get_tools()
        agent = create_react_agent(chat_model, tools)

        # Build input: prior history + new question
        input_messages = messages_from_dict(messages) + [HumanMessage(content=question)]

        result = await agent.ainvoke(
            {"messages": input_messages},
            config={"recursion_limit": AGENT_MAX_STEPS},
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
        tool_trace: list[dict[str, object]] = []
        trace_by_id: dict[str, dict[str, object]] = {}

        for msg in output_messages:
            if isinstance(msg, AIMessage) and getattr(msg, "tool_calls", None):
                agent_steps += 1
                for tc in msg.tool_calls:
                    total_tool_calls += 1
                    entry: dict[str, object] = {
                        "name": tc.get("name", ""),
                        "args": tc.get("args", {}),
                        "result": "",
                    }
                    tool_trace.append(entry)
                    tc_id = tc.get("id", "")
                    if tc_id:
                        trace_by_id[tc_id] = entry

        # Fill tool results from ToolMessages, matched by tool_call_id
        for msg in output_messages:
            if isinstance(msg, ToolMessage):
                tc_id = getattr(msg, "tool_call_id", "")
                if tc_id and tc_id in trace_by_id:
                    trace_by_id[tc_id]["result"] = msg.content

        stats: dict[str, object] = {
            "agent_steps": agent_steps,
            "total_tool_calls": total_tool_calls,
            "tool_trace": tool_trace,
        }

        # Serialize full history
        serialized: list[dict[str, object]] = []
        for msg in output_messages:
            if hasattr(msg, "model_dump"):
                serialized.append(msg.model_dump())
            else:
                serialized.append(msg.dict())

        return (final_text, serialized, stats)
