"""Pure helpers for building the iCoder runtime/startup banner."""

from __future__ import annotations

from collections.abc import Mapping

from mcp_coder.icoder.env_setup import RuntimeInfo


def _connection_status_suffix(
    server_name: str,
    statuses: object,
) -> str:
    """Return '✓ Connected' or '✗ <text>' for a server, or '' if not found.

    Accepts a list of ``ClaudeMCPStatus``/dicts (live) or a mapping of
    name → ``{"ok": bool, "status_text": str}`` (session_start replay).
    """
    if statuses is None:
        return ""
    if isinstance(statuses, Mapping):
        entry = statuses.get(server_name)
        if not isinstance(entry, Mapping):
            return ""
        if bool(entry.get("ok", False)):
            return "✓ Connected"
        return f"✗ {entry.get('status_text', '')}"
    if isinstance(statuses, list):
        for status in statuses:
            if isinstance(status, Mapping):
                if status.get("name") == server_name:
                    if bool(status.get("ok", False)):
                        return "✓ Connected"
                    return f"✗ {status.get('status_text', '')}"
            elif getattr(status, "name", None) == server_name:
                if getattr(status, "ok", False):
                    return "✓ Connected"
                return f"✗ {getattr(status, 'status_text', '')}"
    return ""


def _normalise_mcp_servers(servers: object) -> list[tuple[str, str]]:
    """Normalize the ``mcp_servers`` field to ``[(name, version), ...]``.

    Accepts a list of ``MCPServerInfo`` (live), a list of
    ``{"name": ..., "version": ...}`` dicts, or a mapping of
    name → version (session_start replay).

    Returns:
        ``[(name, version), ...]`` pairs; empty for ``None`` or unknown shapes.
    """
    if servers is None:
        return []
    if isinstance(servers, Mapping):
        return [(str(name), str(version)) for name, version in servers.items()]
    if isinstance(servers, list):
        result: list[tuple[str, str]] = []
        for entry in servers:
            if isinstance(entry, Mapping):
                result.append(
                    (str(entry.get("name", "")), str(entry.get("version", "")))
                )
            else:
                result.append(
                    (
                        str(getattr(entry, "name", "")),
                        str(getattr(entry, "version", "")),
                    )
                )
        return result
    return []


def format_runtime_banner(data: Mapping[str, object]) -> list[str]:
    """Build the dim banner lines shown at startup and during replay.

    Accepts either a ``RuntimeInfo``-shaped mapping (live) or a
    ``session_start`` event payload (replay). Both contain
    ``mcp_coder_version``, ``tool_env``/``tool_env_path``,
    ``project_venv``/``project_venv_path``, ``project_dir``,
    ``mcp_servers``, and ``mcp_connection_status``. Missing keys are
    handled gracefully.

    Returns:
        Banner lines ready to be joined and rendered with the dim style.
    """
    lines: list[str] = [f"mcp-coder {data.get('mcp_coder_version', 'unknown')}"]

    utils_ver = data.get("mcp_coder_utils_version")
    if utils_ver:
        lines.append(f"mcp-coder-utils {utils_ver}")

    statuses = data.get("mcp_connection_status")
    for name, version in _normalise_mcp_servers(data.get("mcp_servers")):
        suffix = _connection_status_suffix(name, statuses)
        lines.append(f"{name} {version}  {suffix}".rstrip())

    tool_env = data.get("tool_env_path") or data.get("tool_env")
    if tool_env:
        lines.append(f"Tool env:    {tool_env}")

    venv = data.get("project_venv_path") or data.get("project_venv")
    if venv:
        lines.append(f"Project env: {venv}")

    project_dir = data.get("project_dir")
    if project_dir:
        lines.append(f"Project dir: {project_dir}")

    return lines


def format_runtime_info(info: RuntimeInfo) -> list[str]:
    """Build banner lines from a live ``RuntimeInfo`` object.

    Returns:
        Banner lines ready to be joined and rendered with the dim style.
    """
    return format_runtime_banner(
        {
            "mcp_coder_version": info.mcp_coder_version,
            "mcp_coder_utils_version": info.mcp_coder_utils_version,
            "tool_env_path": info.tool_env_path,
            "project_venv_path": info.project_venv_path,
            "project_dir": info.project_dir,
            "mcp_servers": info.mcp_servers,
            "mcp_connection_status": info.mcp_connection_status,
        }
    )
