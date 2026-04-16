"""LangChain provider verification functionality.

Provides verify_langchain() which checks configuration, packages, API key,
and reports readiness. Returns a structured dict (no printing).
"""

from __future__ import annotations

import asyncio
import importlib.util
import logging
import os
import re
import shutil
from typing import Any

from . import _load_langchain_config
from ._exceptions import LLMAuthError, LLMConnectionError
from .agent import _load_mcp_server_config

logger = logging.getLogger(__name__)

_BACKEND_ENV_VARS: dict[str, str] = {
    "openai": "OPENAI_API_KEY",
    "gemini": "GEMINI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
}

_BACKEND_PACKAGES: dict[str, str] = {
    "openai": "langchain_openai",
    "gemini": "langchain_google_genai",
    "anthropic": "langchain_anthropic",
}


def _mask_api_key(key: str | None) -> str | None:
    """Mask an API key, showing first 4 and last 4 characters.

    Args:
        key: The API key to mask, or None.

    Returns:
        Masked key string (e.g. ``"sk-1...xyz9"``), ``"****"`` if the key is
        8 characters or fewer, or None if the key is None or empty.
    """
    if not key:
        return None
    if len(key) <= 8:
        return "****"
    return f"{key[:4]}...{key[-4:]}"


def _resolve_api_key(
    backend: str | None, config_key: str | None
) -> tuple[str | None, str | None]:
    """Resolve API key from environment variable or config.

    Args:
        backend: Backend name ("openai", "gemini", "anthropic", or None).
        config_key: API key from config.toml, or None.

    Returns:
        Tuple of ``(key, source)`` where *key* is the resolved API key string
        and *source* describes where it was found (e.g. ``"OPENAI_API_KEY env var"``
        or ``"config.toml"``).  Both elements are None if no key is available.
    """
    env_var = _BACKEND_ENV_VARS.get(backend or "")
    if env_var:
        env_value = os.environ.get(env_var)
        if env_value:
            return env_value, f"{env_var} env var"
    if config_key:
        return config_key, "config.toml"
    return None, None


def _check_package_installed(package_name: str) -> bool:
    """Check if a Python package is installed using importlib.

    Args:
        package_name: Dotted Python package name to check.

    Returns:
        True if the package is installed and importable, False otherwise.
    """
    try:
        return importlib.util.find_spec(package_name) is not None
    except (ValueError, ModuleNotFoundError):
        return False


def _check_mcp_adapter_packages() -> dict[str, dict[str, Any]]:
    """Check if langchain-mcp-adapters and langgraph are importable.

    Returns:
        Dict with ``"mcp_adapters"`` and ``"langgraph"`` keys, each mapping
        to a dict containing ``"ok"`` (bool) and ``"value"`` (status message).
    """
    mcp_ok = _check_package_installed("langchain_mcp_adapters")
    lg_ok = _check_package_installed("langgraph")

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
    config = _load_langchain_config()
    backend = config.get("backend")
    model = config.get("model")
    config_api_key = config.get("api_key")

    result: dict[str, Any] = {}

    # Backend check
    result["backend"] = {
        "ok": backend is not None,
        "value": backend,
    }

    # Model check
    result["model"] = {
        "ok": model is not None,
        "value": model,
    }

    # API key resolution
    api_key, key_source = _resolve_api_key(backend, config_api_key)
    result["api_key"] = {
        "ok": api_key is not None,
        "value": _mask_api_key(api_key),
        "source": key_source,
    }

    # langchain-core package check
    lc_core_installed = _check_package_installed("langchain_core")
    result["langchain_core"] = {
        "ok": lc_core_installed,
        "value": "installed" if lc_core_installed else "not installed",
    }
    if not lc_core_installed:
        result["langchain_core"]["install_hint"] = "pip install langchain-core"

    # Backend package check
    backend_pkg = _BACKEND_PACKAGES.get(backend or "")
    if backend_pkg:
        pkg_installed = _check_package_installed(backend_pkg)
        # Format package name with hyphens for display
        display_name = backend_pkg.replace("_", "-")
        result["backend_package"] = {
            "ok": pkg_installed,
            "value": (
                f"{display_name} installed"
                if pkg_installed
                else f"{display_name} not installed"
            ),
        }
        if not pkg_installed:
            result["backend_package"]["install_hint"] = f"pip install {display_name}"
    else:
        result["backend_package"] = {
            "ok": False,
            "value": "no backend configured",
        }

    # MCP adapter packages check (always run)
    mcp_pkg_results = _check_mcp_adapter_packages()
    result["mcp_adapters"] = mcp_pkg_results["mcp_adapters"]
    result["langgraph"] = mcp_pkg_results["langgraph"]

    # Check models (optional)
    if check_models and backend:
        result["available_models"] = _list_models_for_backend(
            backend, api_key, config.get("endpoint")
        )

    # overall_ok: True when backend configured AND all required packages installed
    result["overall_ok"] = bool(
        backend
        and result["backend_package"]["ok"]
        and result["mcp_adapters"]["ok"]
        and result["langgraph"]["ok"]
    )

    return result


def _list_models_for_backend(
    backend: str, api_key: str | None, endpoint: str | None
) -> dict[str, Any]:
    """List models for the given backend using existing _models.py functions.

    Args:
        backend: Backend name ("openai", "gemini", or "anthropic").
        api_key: API key for the backend, or None.
        endpoint: Optional custom endpoint URL (used by OpenAI backend).

    Returns:
        Dict with 'ok' (bool), 'value' (list of model names), and optionally 'error'.
    """
    try:
        from . import _models

        if backend == "openai":
            models = _models.list_openai_models(api_key, endpoint)
        elif backend == "gemini":
            models = _models.list_gemini_models(api_key)
        elif backend == "anthropic":
            models = _models.list_anthropic_models(api_key)
        else:
            return {"ok": False, "value": [], "error": f"Unknown backend: {backend}"}
        return {"ok": True, "value": models}
    except LLMConnectionError as exc:
        return {"ok": False, "value": [], "error": str(exc), "error_type": "connection"}
    except LLMAuthError as exc:
        return {"ok": False, "value": [], "error": str(exc), "error_type": "auth"}
    except Exception as exc:  # pylint: disable=broad-exception-caught
        return {"ok": False, "value": [], "error": str(exc), "error_type": "unknown"}


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
