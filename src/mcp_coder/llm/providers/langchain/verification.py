"""LangChain provider verification functionality.

Provides verify_langchain() which checks configuration, packages, API key,
and reports readiness. Returns a structured dict (no printing).
"""

from __future__ import annotations

import asyncio
import re
import shutil
from typing import Any

from . import _provider_checks
from ._config_source import _load_langchain_config
from ._mcp_tools import _load_mcp_server_config

# Rows that come after the MCP rows in verify_langchain()'s output.
_PROBE_KEYS = (
    "ollama_daemon",
    "ollama_tools_capability",
    "available_models",
    "model_check",
)


def _check_mcp_adapter_packages() -> dict[str, dict[str, Any]]:
    """Check if langchain-mcp-adapters and langgraph are importable.

    Returns:
        Dict with ``"mcp_adapters"`` and ``"langgraph"`` keys, each mapping
        to a dict containing ``"ok"`` (bool) and ``"value"`` (status message).
    """
    mcp_ok = _provider_checks._check_package_installed("langchain_mcp_adapters")
    lg_ok = _provider_checks._check_package_installed("langgraph")

    mcp_entry: dict[str, Any] = {
        "ok": mcp_ok,
        "value": (
            "langchain-mcp-adapters installed"
            if mcp_ok
            else "langchain-mcp-adapters not installed"
        ),
    }
    if not mcp_ok:
        mcp_entry["install_hint"] = "pip install langchain-mcp-adapters"

    lg_entry: dict[str, Any] = {
        "ok": lg_ok,
        "value": "langgraph installed" if lg_ok else "langgraph not installed",
    }
    if not lg_ok:
        lg_entry["install_hint"] = "pip install langgraph"

    return {
        "mcp_adapters": mcp_entry,
        "langgraph": lg_entry,
    }


def verify_langchain(
    check_models: bool = False,
    mcp_config_path: str | None = None,
) -> dict[str, Any]:
    """Verify LangChain provider configuration and connectivity.

    Returns a structured dict with verification results (no printing).
    The CLI layer handles all output formatting.

    Args:
        check_models: If True, also list available models for the backend.
        mcp_config_path: Unused, kept for API compatibility.

    Returns:
        Dict with keys: backend, model, api_key, langchain_core,
        backend_package, mcp_adapters, langgraph, overall_ok.
        If check_models=True, also includes available_models.
    """
    rows = _provider_checks.check_provider(
        _load_langchain_config(), check_models=check_models
    )
    provider_ok = rows.pop("overall_ok")
    # Runs after check_provider, so package-check side effects keep their order.
    mcp = _check_mcp_adapter_packages()

    # The MCP rows go before the first probe row, or last when there is none.
    result: dict[str, Any] = {}
    for key, row in rows.items():
        if key in _PROBE_KEYS and "mcp_adapters" not in result:
            result.update(mcp)
        result[key] = row
    if "mcp_adapters" not in result:
        result.update(mcp)

    # Not `mcp_ok and provider_ok`: a non-bool probe ok must still yield False.
    mcp_ok = mcp["mcp_adapters"]["ok"] and mcp["langgraph"]["ok"]
    result["overall_ok"] = provider_ok if mcp_ok else False

    return result


# ---------------------------------------------------------------------------
# MCP server health check
# ---------------------------------------------------------------------------

# Lazy import — only needed when verify_mcp_servers() is actually called.
_mcp_client_cache: dict[str, Any] = {}


def _import_mcp_client() -> Any:
    """Deferred import of MultiServerMCPClient.

    Returns:
        The MultiServerMCPClient class.
    """
    if "cls" not in _mcp_client_cache:
        from langchain_mcp_adapters.client import MultiServerMCPClient as _Client

        _mcp_client_cache["cls"] = _Client
    return _mcp_client_cache["cls"]


_PLACEHOLDER_RE = re.compile(r"\$\{[^}]+\}")


def _preflight_mcp_server(
    name: str,
    cfg: dict[str, object],
) -> tuple[bool, str | None]:
    """Pre-flight check for an MCP server configuration.

    Scans ``command``, ``args`` and ``env`` values for unresolved ``${VAR}``
    placeholders, then verifies the command resolves to an existing binary
    via :func:`shutil.which`.

    Args:
        name: Server name, used in the returned message.
        cfg: Server configuration dict.

    Returns:
        Tuple ``(ok, message)``.  ``(True, None)`` means proceed to the
        live launch.  ``(False, <message>)`` means short-circuit with an
        actionable message.
    """
    command = cfg.get("command")
    cmd_str = command if isinstance(command, str) else ""

    scan_items: list[tuple[str, str]] = []
    if cmd_str:
        scan_items.append(("command", cmd_str))

    args = cfg.get("args")
    if isinstance(args, list):
        for item in args:
            if isinstance(item, str):
                scan_items.append(("args", item))

    env = cfg.get("env")
    if isinstance(env, dict):
        for value in env.values():
            if isinstance(value, str):
                scan_items.append(("env", value))

    for field, value in scan_items:
        m = _PLACEHOLDER_RE.search(value)
        if m:
            return (
                False,
                f"unresolved placeholder {m.group(0)} in {name}.{field}",
            )

    if cmd_str and shutil.which(cmd_str) is None:
        return (False, f"binary not found at {cmd_str} (server {name})")

    return (True, None)


async def _check_servers(
    server_config: dict[str, dict[str, object]],
    timeout: int,
) -> dict[str, dict[str, Any]]:
    """Connect to each server and list tools (async internals).

    Args:
        server_config: Dict mapping server names to their configurations.
        timeout: Connection timeout in seconds per server.

    Returns:
        Dict mapping server names to result dicts with ok, value, and tools keys.
    """
    client_cls = _import_mcp_client()
    results: dict[str, dict[str, Any]] = {}

    for server_name in server_config:
        cfg = server_config[server_name]
        ok, msg = _preflight_mcp_server(server_name, cfg)
        if not ok:
            category = (
                "UnresolvedPlaceholder"
                if msg is not None and msg.startswith("unresolved placeholder")
                else "FileNotFoundError"
            )
            results[server_name] = {
                "ok": False,
                "value": msg,
                "error": category,
            }
            continue

        single_config = {server_name: cfg}
        client = client_cls(single_config)
        try:
            async with asyncio.timeout(timeout):
                async with client.session(server_name) as session:
                    tools = await session.list_tools()
                    tool_names = [(t.name, t.description or "") for t in tools.tools]
                    results[server_name] = {
                        "ok": True,
                        "value": f"{len(tools.tools)} tools available",
                        "tools": len(tools.tools),
                        "tool_names": tool_names,
                    }
        except Exception as exc:  # pylint: disable=broad-except
            if isinstance(exc, asyncio.TimeoutError):
                results[server_name] = {
                    "ok": False,
                    "value": (f"MCP server {server_name!r} timed out after {timeout}s"),
                    "error": "TimeoutError",
                }
            else:
                results[server_name] = {
                    "ok": False,
                    "value": (
                        f"MCP server {server_name!r} failed to launch: "
                        f"{cfg.get('command', '')} ({type(exc).__name__}: {exc})"
                    ),
                    "error": type(exc).__name__,
                }
    return results


def verify_mcp_servers(
    mcp_config_path: str,
    timeout: int = 15,
    env_vars: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Check each configured MCP server by connecting and listing tools.

    Args:
        mcp_config_path: Path to the .mcp.json configuration file.
        timeout: Connection timeout in seconds per server.
        env_vars: Optional extra environment variables for ``${VAR}``
            resolution in the MCP config.  When *None*, only ``os.environ``
            is used, which may lack variables like ``MCP_CODER_PROJECT_DIR``.

    Returns:
        Dict with per-server results and overall_ok.
        Keys: ``"servers"`` (dict of server_name → result),
        ``"overall_ok"`` (bool).
        Each server result: ``{"ok": bool, "value": str, "tools": int | None,
        "error": str | None}``.
    """
    server_config = _load_mcp_server_config(mcp_config_path, env_vars=env_vars)
    if not server_config:
        return {"servers": {}, "overall_ok": True, "value": "no servers configured"}

    results = asyncio.run(_check_servers(server_config, timeout))
    overall_ok = all(r["ok"] for r in results.values())
    return {"servers": results, "overall_ok": overall_ok}
