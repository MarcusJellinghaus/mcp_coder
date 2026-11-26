"""Section formatters for the verify command.

Pure leaf module: builds the rows of the Claude, LangChain, MLflow, Jenkins and
MCP sections from domain verify results, plus the label map they use. The GIT,
GITHUB and GITHUB SECURITY sections come from mcp-workspace's formatters.
Row/section primitives come from ``mcp_coder.utils.verify_render``; nothing
here reaches back into ``verify.py`` (one-directional edge
``verify.py -> verify_formatting``).
"""

import keyword
import re
from typing import Any, cast

from ...llm.providers.claude.claude_mcp_guard import (
    MCP_NEEDS_AUTH_STATUS,
    find_exposed_mcp_tools,
    find_fatal_mcp_servers,
    find_unavailable_mcp_servers,
)
from ...utils.mcp_verification import ClaudeMCPStatus
from ...utils.verify_render import Line, Row, hint_row

_KEY_REGEX = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _looks_like_key(token: str) -> bool:
    """Return True if *token* is a non-keyword Python identifier."""
    return bool(_KEY_REGEX.match(token)) and not keyword.iskeyword(token)


_LABEL_MAP: dict[str, str] = {
    # Claude section
    "cli_found": "Claude CLI Found",
    "cli_path": "Path",
    "cli_version": "Version",
    "cli_works": "Executable Works",
    "api_integration": "API Integration",
    # LangChain section
    "backend": "Backend",
    "model": "Model",
    "api_key": "API key",
    "api_version": "API version",
    "langchain_core": "LangChain core",
    "backend_package": "Backend package",
    # "base_url" (contract finding) and "base_url_shape" (heuristic) share a
    # label but are mutually exclusive by construction: the shape check runs
    # only for non-Azure openai, while contract base_url findings arise only
    # in Azure mode or on backends that ignore the key.
    "base_url": "Base URL",
    "base_url_shape": "Base URL",
    "base_url_redirect": "Base URL redirect",
    "api_key_override": "API key override",
    "available_models": "Available models",
    "model_check": "Model available",
    # MCP adapter section
    "mcp_adapters": "MCP adapters",
    "langgraph": "LangGraph",
    # Ollama section
    "ollama_daemon": "Local Ollama daemon",
    "ollama_tools_capability": "Tool-call capability",
    # MLflow section
    "installed": "MLflow installed",
    "enabled": "MLflow enabled",
    "tracking_uri": "Tracking URI",
    "connection": "Connection",
    "experiment": "Experiment",
    "artifact_location": "Artifact location",
    "tracking_data": "Tracking data",
    # Jenkins section (JENKINS JOBS keys are repo names and pass through unmapped)
    "server": "Server",
    "authentication": "Authentication",
    "overall_read": "Overall/Read",
}


def _format_section(result: dict[str, Any], symbols: dict[str, str]) -> list[Line]:
    """Build the rows of a verification section.

    Args:
        result: Dict from a domain verify function
        symbols: Dict with 'success', 'failure', 'warning' keys

    Returns:
        The section's lines (without the title header), ready for rendering.
    """
    lines: list[Line] = []
    for key, entry in result.items():
        if key == "overall_ok":
            continue
        if not isinstance(entry, dict):
            continue
        label = _LABEL_MAP.get(key, key)
        ok = entry.get("ok")
        value = str(entry.get("value", ""))
        if ok is True:
            symbol = symbols["success"]
        elif ok is False:
            symbol = symbols["failure"]
        else:
            symbol = symbols["warning"]
        row_value = value
        error = entry.get("error")
        if error and ok is False:
            row_value = f"{value} ({error})"
        lines.append(Row(label, symbol, row_value))
        if ok is False and "install_hint" in entry:
            lines.append(hint_row(f"-> {entry['install_hint']}"))
    return lines


def _format_mcp_section(
    mcp_results: dict[str, Any],
    symbols: dict[str, str],
    *,
    list_mcp_tools: bool = False,
    for_completeness: bool = False,
) -> tuple[str, list[Line]]:
    """Build the MCP server health check section.

    Args:
        mcp_results: Dict containing server health check results.
        symbols: Dict with 'success', 'failure', 'warning' keys.
        list_mcp_tools: When True, render each tool on its own indented line
            with descriptions aligned globally across all servers.
        for_completeness: If True, append "for completeness" to section title.

    Returns:
        ``(title, lines)`` for the MCP servers section.
    """
    title_suffix = " — for completeness" if for_completeness else ""
    title = f"MCP SERVERS (via langchain-mcp-adapters{title_suffix})"
    lines: list[Line] = []
    servers = mcp_results["servers"]

    if list_mcp_tools:
        # Compute global max tool name width across ALL servers
        max_name = max(
            (
                len(name)
                for srv in servers.values()
                if srv.get("tool_names")
                for name, _ in srv["tool_names"]
            ),
            default=0,
        )
        for name, entry in servers.items():
            ok = entry.get("ok")
            value = entry.get("value", "")
            symbol = symbols["success"] if ok else symbols["failure"]
            tool_names = entry.get("tool_names")
            if tool_names:
                lines.append(Row(name, symbol, f"{len(tool_names)} tools available"))
                for tool_name, desc in tool_names:
                    if desc:
                        lines.append(f"    {tool_name:<{max_name + 2}s} {desc}")
                    else:
                        lines.append(f"    {tool_name}")
            else:
                lines.append(Row(name, symbol, value))
    else:
        for name, entry in servers.items():
            ok = entry.get("ok")
            value = entry.get("value", "")
            symbol = symbols["success"] if ok else symbols["failure"]
            tool_names = entry.get("tool_names")
            if tool_names:
                names_only = [n for n, _d in tool_names]
                tools_text = f"{len(tool_names)} tools: {', '.join(names_only)}"
                lines.append(Row(name, symbol, tools_text, wrap=True))
            else:
                lines.append(Row(name, symbol, value))
    return title, lines


def _format_claude_mcp_section(
    statuses: list[ClaudeMCPStatus],
    symbols: dict[str, str],
    *,
    for_completeness: bool = False,
) -> tuple[str, list[Line]]:
    """Build the MCP server connection section from ``claude mcp list``.

    Args:
        statuses: Parsed connection statuses.
        symbols: Dict with 'success', 'failure' keys.
        for_completeness: If True, append "for completeness" to section title.

    Returns:
        ``(title, lines)`` for the section.
    """
    title_suffix = " — for completeness" if for_completeness else ""
    lines: list[Line] = [
        Row(s.name, symbols["success"] if s.ok else symbols["failure"], s.status_text)
        for s in statuses
    ]
    return f"MCP SERVERS (via Claude Code{title_suffix})", lines


def _format_tools_exposed_section(
    system_message: dict[str, Any] | None,
    symbols: dict[str, str],
) -> tuple[list[Line], bool | None]:
    """Build the "Tools exposed to model" row(s) + exit signal.

    Reads the init event captured by the Claude provider and reports how many
    ``mcp__*`` tools were actually exposed to the model, mirroring the runtime
    guard's status classification.

    Args:
        system_message: The init ``system`` event (``raw_response["system"]``),
            or None when no init event was captured.
        symbols: Dict with 'success', 'failure', 'warning' keys.

    Returns:
        ``(rows, ok)`` where ``ok`` mirrors the runtime guard:
          - ``True``  -> connected with >=1 tool exposed
          - ``None``  -> a server is pending (WARN only; never fails the build)
          - ``False`` -> a server is fatal (failed/unknown) OR
            connected-but-0-tools

        ``needs-auth`` servers (unauthenticated claude.ai account connectors)
        are excluded from the health assessment: needs-auth-only yields the
        same outcome as all-connected (subject to the 0-tools check), with
        the connectors listed on an extra labeled info line.
    """
    label = "Tools exposed to model"
    if system_message is None:
        return [Row(label, symbols["warning"], "unavailable (no init event)")], None
    guard_msg = cast(Any, system_message)
    fatal = find_fatal_mcp_servers(guard_msg)
    unavailable = find_unavailable_mcp_servers(guard_msg)
    needs_auth = {k: v for k, v in unavailable.items() if v == MCP_NEEDS_AUTH_STATUS}
    pending = {
        k: v for k, v in unavailable.items() if k not in fatal and k not in needs_auth
    }
    tools = find_exposed_mcp_tools(guard_msg)
    names = [
        str(s["name"])
        for s in system_message.get("mcp_servers") or []
        if isinstance(s, dict) and s.get("name")
    ]

    marker: str
    ok: bool | None
    value: str
    hint: str | None = None
    if fatal:
        marker, ok, value = symbols["failure"], False, f"{len(tools)} ({fatal})"
        hint = "-> check the MCP server logs / .mcp.json config"
    elif pending:
        marker, ok, value = (
            symbols["warning"],
            None,
            f"{len(tools)} (pending: {sorted(pending)})",
        )
    elif not tools:
        marker, ok, value = symbols["failure"], False, "0 tools exposed"
        hint = (
            "-> server connected but exposed 0 tools; check 'alwaysLoad' in .mcp.json"
        )
    else:
        marker, ok, value = (
            symbols["success"],
            True,
            f"{len(tools)} ({', '.join(names)})",
        )

    lines: list[Line] = [Row(label, marker, value)]
    if hint is not None:
        lines.append(hint_row(hint))
    if needs_auth:
        note = (
            "-> unauthenticated account connector(s), "
            f"not part of health assessment: {sorted(needs_auth)}"
        )
        lines.append(hint_row(note))
    return lines, ok
