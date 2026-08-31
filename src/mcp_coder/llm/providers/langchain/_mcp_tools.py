"""MCP server configuration and tool-building helpers for the LangChain provider.

Turns an ``.mcp.json`` file into a ``MultiServerMCPClient`` server mapping
(with ``${VAR}`` substitution) and turns raw MCP tools into LangChain tools
(with schema sanitization). Extracted from ``agent.py`` to keep that module
under the file-size gate; ``agent.py`` re-exports these names, so existing
``agent.<helper>`` imports and patch targets keep working.
"""

from __future__ import annotations

import copy
import json
import logging
import os
import re
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_KNOWN_FIELDS = {"command", "args", "env", "transport", "type"}


def _format_launch_error(server_name: str, command: object, exc: BaseException) -> str:
    """Format the user-facing message for a failed MCP server launch.

    Args:
        server_name: Name of the MCP server that failed to launch.
        command: The configured command (may be missing, non-string, or empty).
        exc: The original exception that caused the launch failure.

    Returns:
        A formatted message suitable for use in an LLMMCPLaunchError.
    """
    cmd_str = command if isinstance(command, str) and command else "<unknown>"
    return (
        f"MCP server {server_name!r} failed to launch: "
        f"{cmd_str} ({type(exc).__name__})"
    )


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


def _convert_server_tools(
    raw_tools: list[Any],
    connection: Any,
    server_name: str,
    tool_interceptors: list[Any] | None = None,
) -> list[Any]:
    """Convert one server's raw MCP tools to LangChain tools.

    Single home for the ``sanitize -> model_copy -> convert`` inner loop shared
    by ``run_agent_stream`` (else-branch) and
    ``MCPManager._connect_and_discover``. Optional ``tool_interceptors`` are
    forwarded verbatim to ``convert_mcp_tool_to_langchain_tool`` (the injection
    point for host-side permission enforcement, issue I2.3).

    No canonical-name metadata stamping is done here — that stays the caller's
    job so the stamp can remain pinned to the raw MCP tool name rather than the
    (possibly renamed) LangChain tool name.

    Args:
        raw_tools: Raw MCP tool objects from ``session.list_tools()``.
        connection: The MCP connection object for this server.
        server_name: Name of the MCP server the tools belong to.
        tool_interceptors: Optional call-level interceptors forwarded to
            ``convert_mcp_tool_to_langchain_tool``. ``None`` means no
            enforcement (the default at every non-manager site).

    Returns:
        LangChain tools in the same order as *raw_tools*.
    """
    from langchain_mcp_adapters.tools import convert_mcp_tool_to_langchain_tool

    lc_tools: list[Any] = []
    for tool in raw_tools:
        sanitized = _sanitize_tool_schema(tool.inputSchema)
        # Shallow copy to avoid mutating the original MCP tool
        tool = tool.model_copy(update={"inputSchema": sanitized})
        lc_tools.append(
            convert_mcp_tool_to_langchain_tool(
                None,
                tool,
                connection=connection,
                server_name=server_name,
                tool_interceptors=tool_interceptors,
            )
        )
    return lc_tools
