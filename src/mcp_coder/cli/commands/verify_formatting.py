"""Formatting primitives for the verify command.

Pure leaf module: the row/section formatters and the constant maps they use.
Depends only on the standard library and two leaf helpers; nothing here reaches
back into ``verify.py`` (one-directional edge ``verify.py -> verify_formatting``).
"""

import keyword
import re
import textwrap
from typing import Any, cast

from ...llm.providers.claude.claude_mcp_guard import (
    find_exposed_mcp_tools,
    find_fatal_mcp_servers,
    find_unavailable_mcp_servers,
)
from ...utils.mcp_verification import ClaudeMCPStatus

STATUS_SYMBOLS: dict[str, str] = {
    "success": "[OK]",
    "failure": "[ERR]",
    "warning": "[WARN]",
}

_MARKER_SLOT_WIDTH: int = max(len(v) for v in STATUS_SYMBOLS.values())
_LABEL_WIDTH: int = 22  # global minimum label slot; sections may widen via label_width=


def _format_row_prefix(
    label: str, marker: str, *, indent: int, label_width: int = _LABEL_WIDTH
) -> str:
    """Render the column-aligned prefix portion of a tabular row.

    Empty marker is padded to ``_MARKER_SLOT_WIDTH`` so the value column
    starts at the same horizontal position regardless of marker presence.
    Labels longer than ``label_width`` overrun (no truncation) — keep
    labels concise, or pass a wider ``label_width`` for sections whose
    labels are known to exceed the default.

    Args:
        label: Row label (may be empty for label-less rows).
        marker: Status marker (e.g. ``[OK]``, ``[ERR]``, ``[WARN]``, or "").
        indent: Number of leading spaces.
        label_width: Minimum width of the label column.

    Returns:
        ``indent + label_field + " " + marker_field + " "`` WITHOUT
        rstrip — the trailing space and the full marker-slot padding are
        preserved. Used directly by callers that need the prefix without
        a value (e.g. ``textwrap.wrap`` continuation indent).
    """
    return f"{' ' * indent}{label:<{label_width}s} {marker:<{_MARKER_SLOT_WIDTH}s} "


def _format_row(
    label: str, marker: str, value: str, *, indent: int, label_width: int = _LABEL_WIDTH
) -> str:
    """Render a tabular row (labeled or label-less).

    Composed on top of ``_format_row_prefix``; appends the value and
    rstrips trailing whitespace. Label-less rows pass ``label=""``;
    the empty label is padded so the value column aligns with
    neighbouring labeled rows.

    Args:
        label: Row label (may be empty for label-less rows).
        marker: Status marker (e.g. ``[OK]``, ``[ERR]``, ``[WARN]``, or "").
        value: Row value text.
        indent: Number of leading spaces.
        label_width: Minimum width of the label column.

    Returns:
        Formatted row string with trailing whitespace stripped.
    """
    return (
        _format_row_prefix(label, marker, indent=indent, label_width=label_width)
        + value
    ).rstrip()


_VALUE_COLUMN_INDENT: int = len(_format_row_prefix("", "", indent=2))


def _pad(title: str) -> str:
    r"""Return a section header line padded to 75 chars with '='."""
    prefix = f"=== {title} "
    return "\n" + prefix + "=" * max(0, 75 - len(prefix))


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
    "langchain_core": "LangChain core",
    "backend_package": "Backend package",
    "endpoint_shape": "Endpoint",
    "available_models": "Available models",
    # MCP adapter section
    "mcp_adapters": "MCP adapters",
    "langgraph": "LangGraph",
    # Ollama section
    "ollama_daemon": "Local Ollama daemon",
    "ollama_tools_capability": "Tool-calling capability",
    # MLflow section
    "installed": "MLflow installed",
    "enabled": "MLflow enabled",
    "tracking_uri": "Tracking URI",
    "connection": "Connection",
    "experiment": "Experiment",
    "artifact_location": "Artifact location",
    "tracking_data": "Tracking data",
    # GitHub section
    "api_base_url": "API base URL",
    "network_proxy": "Network / proxy",
    "token_configured": "Token configured",
    "authenticated_user": "Authenticated user",
    "repo_url": "Repo URL",
    "repo_accessible": "Repo accessible",
    "branch_protection": "Branch protection",
    "ci_checks_required": "CI checks required",
    "strict_mode": "Strict mode",
    "force_push": "Force push",
    "branch_deletion": "Branch deletion",
    "auto_delete_branches": "Auto-delete branches",
    "perm_contents_read": "Contents: Read",
    "perm_administration_read": "Administration: Read",
    "perm_pull_requests_read": "Pull requests: Read",
    "perm_issues_read": "Issues: Read",
    "perm_workflows_read": "Actions: Read",
    "perm_statuses_read": "Commit statuses: Read",
    # Git section
    "git_binary": "Git binary",
    "git_repo": "Repository",
    "user_identity": "Git identity",
    "signing_intent": "Signing enabled",
    "signing_consistency": "Signing config consistent",
    "signing_format": "Signing format",
    "signing_key": "Signing key",
    "signing_binary": "Signing binary",
    "signing_key_accessible": "Signing key accessible",
    "agent_reachable": "GPG agent",
    "allowed_signers": "Allowed signers file",
    "verify_head": "HEAD signature",
    "actual_signature": "End-to-end sign test",
}


_BRANCH_PROTECTION_CHILDREN = frozenset(
    {"ci_checks_required", "strict_mode", "force_push", "branch_deletion"}
)


def _format_section(title: str, result: dict[str, Any], symbols: dict[str, str]) -> str:
    """Format a verification section for terminal output.

    Args:
        title: Section title (e.g. "BASIC VERIFICATION")
        result: Dict from a domain verify function
        symbols: Dict with 'success', 'failure', 'warning' keys

    Returns:
        Formatted multi-line string for the section.
    """
    lines: list[str] = [_pad(title)]
    bp_ok: bool | None = None  # track branch_protection parent state
    permissions_header_emitted: bool = False
    # NOTE: relies on dict insertion order — branch_protection must precede its
    # children in the result dict. This is guaranteed by verify_github() in
    # mcp-workspace.
    for key, entry in result.items():
        if key == "overall_ok":
            continue
        if not isinstance(entry, dict):
            continue
        label = _LABEL_MAP.get(key, key)
        ok = entry.get("ok")
        value = str(entry.get("value", ""))
        if key == "branch_protection":
            bp_ok = ok
        elif key in _BRANCH_PROTECTION_CHILDREN:
            if bp_ok is False:
                continue  # suppress children when parent failed
            if key == "strict_mode":
                lines.append(_format_row(label, "", value, indent=4))
            else:
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
                lines.append(_format_row(label, symbol, row_value, indent=4))
            continue
        if key.startswith("perm_") and not permissions_header_emitted:
            lines.append("")
            lines.append("  [Permissions]")
            permissions_header_emitted = True
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
        indent = 4 if key.startswith("perm_") else 2
        lines.append(_format_row(label, symbol, row_value, indent=indent))
        if key == "token_configured" and entry.get("token_source"):
            src = entry["token_source"]
            suffix = (
                "GITHUB_TOKEN env var" if src == "env" else "~/.mcp_coder/config.toml"
            )
            fingerprint = entry.get("token_fingerprint")
            if fingerprint:
                suffix = f"{suffix} ({fingerprint})"
            lines.append(f"{' ' * _VALUE_COLUMN_INDENT}from {suffix}")
        if ok is False and "install_hint" in entry:
            lines.append(f"{' ' * _VALUE_COLUMN_INDENT}-> {entry['install_hint']}")
    return "\n".join(lines)


def _format_mcp_section(
    mcp_results: dict[str, Any],
    symbols: dict[str, str],
    *,
    list_mcp_tools: bool = False,
    for_completeness: bool = False,
) -> str:
    """Format MCP server health check results.

    Args:
        mcp_results: Dict containing server health check results.
        symbols: Dict with 'success', 'failure', 'warning' keys.
        list_mcp_tools: When True, render each tool on its own indented line
            with descriptions aligned globally across all servers.
        for_completeness: If True, append "for completeness" to section title.

    Returns:
        Formatted multi-line string for the MCP servers section.
    """
    title_suffix = " — for completeness" if for_completeness else ""
    lines: list[str] = [_pad(f"MCP SERVERS (via langchain-mcp-adapters{title_suffix})")]
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
                lines.append(
                    _format_row(
                        name, symbol, f"{len(tool_names)} tools available", indent=2
                    )
                )
                for tool_name, desc in tool_names:
                    if desc:
                        lines.append(f"    {tool_name:<{max_name + 2}s} {desc}")
                    else:
                        lines.append(f"    {tool_name}")
            else:
                lines.append(_format_row(name, symbol, value, indent=2))
    else:
        for name, entry in servers.items():
            ok = entry.get("ok")
            value = entry.get("value", "")
            symbol = symbols["success"] if ok else symbols["failure"]
            tool_names = entry.get("tool_names")
            if tool_names:
                prefix = _format_row_prefix(name, symbol, indent=2)
                names_only = [n for n, _d in tool_names]
                tools_text = f"{len(tool_names)} tools: {', '.join(names_only)}"
                wrapped = textwrap.wrap(
                    tools_text,
                    width=80,
                    initial_indent=prefix,
                    subsequent_indent=" " * len(prefix),
                )
                lines.extend(wrapped)
            else:
                lines.append(_format_row(name, symbol, value, indent=2))
    return "\n".join(lines)


def _format_claude_mcp_section(
    statuses: list[ClaudeMCPStatus],
    symbols: dict[str, str],
    *,
    for_completeness: bool = False,
) -> str:
    """Format MCP server connection status from ``claude mcp list``.

    Args:
        statuses: Parsed connection statuses.
        symbols: Dict with 'success', 'failure' keys.
        for_completeness: If True, append "for completeness" to section title.

    Returns:
        Formatted multi-line string.
    """
    title_suffix = " — for completeness" if for_completeness else ""
    lines: list[str] = [_pad(f"MCP SERVERS (via Claude Code{title_suffix})")]
    for status in statuses:
        symbol = symbols["success"] if status.ok else symbols["failure"]
        lines.append(_format_row(status.name, symbol, status.status_text, indent=2))
    return "\n".join(lines)


def _format_tools_exposed_section(
    system_message: dict[str, Any] | None,
    symbols: dict[str, str],
) -> tuple[list[str], bool | None]:
    """Build the "MCP tools exposed to model" row(s) + exit signal.

    Reads the init event captured by the Claude provider and reports how many
    ``mcp__*`` tools were actually exposed to the model, mirroring the runtime
    guard's status classification.

    Args:
        system_message: The init ``system`` event (``raw_response["system"]``),
            or None when no init event was captured.
        symbols: Dict with 'success', 'failure', 'warning' keys.

    Returns:
        ``(lines, ok)`` where ``ok`` mirrors the runtime guard:
          - ``True``  -> connected with >=1 tool exposed
          - ``None``  -> a server is pending (WARN only; never fails the build)
          - ``False`` -> a server is fatal (failed/unknown) OR
            connected-but-0-tools
    """
    label = "MCP tools exposed to model"
    if system_message is None:
        return (
            [
                _format_row(
                    label,
                    symbols["warning"],
                    "unavailable (no init event)",
                    indent=2,
                )
            ],
            None,
        )
    guard_msg = cast(Any, system_message)
    fatal = find_fatal_mcp_servers(guard_msg)
    unavailable = find_unavailable_mcp_servers(guard_msg)
    pending = {k: v for k, v in unavailable.items() if k not in fatal}
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
            "-> server connected but exposed 0 tools; "
            "check 'alwaysLoad' in .mcp.json"
        )
    else:
        marker, ok, value = (
            symbols["success"],
            True,
            f"{len(tools)} ({', '.join(names)})",
        )

    lines = [_format_row(label, marker, value, indent=2)]
    if hint is not None:
        lines.append(f"{' ' * _VALUE_COLUMN_INDENT}{hint}")
    return lines, ok
