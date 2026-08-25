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
from urllib.parse import urlparse

from . import _load_langchain_config
from ._config_diagnostics import (
    _API_KEY_ENV,
    _KEYLESS_ENV,
    _UNSET_TARGET,
    ResolvedTarget,
    _targets_match,
    describe_effective_config,
    mode_of,
    redirect_env_in_effect,
    resolve_target,
)
from ._exceptions import LLMAuthError, LLMConnectionError
from .agent import _load_mcp_server_config

logger = logging.getLogger(__name__)

_BACKEND_PACKAGES: dict[str, str] = {
    "openai": "langchain_openai",
    "gemini": "langchain_google_genai",
    "anthropic": "langchain_anthropic",
    "ollama": "langchain_ollama",
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
    mode: str | None, config_key: str | None
) -> tuple[str | None, str | None, bool]:
    """Resolve the API key the client will use, and say where it came from.

    Keyed by *mode*, not backend, so an Azure setup whose key lives in
    ``AZURE_OPENAI_API_KEY`` is named rather than reported as unset.

    Resolution follows the order the *client* resolves, which is not the
    table's order. Only ``_API_KEY_ENV[mode][0]`` is read by our own
    ``create_*_model`` (``os.getenv(X) or api_key``), and it genuinely beats
    config; the remaining entries are SDK fallbacks that apply only when no
    key is passed at all, so a configured key beats them.

    Args:
        mode: Contract mode from ``mode_of()``, or None.
        config_key: API key from config.toml, or None.

    Returns:
        Tuple of ``(key, source, overridden)``. *source* may be set while
        *key* is None — gemini's keyless Vertex carve-out satisfies the
        credential without exposing a readable value. *overridden* is True
        only when the primary env var beat a configured ``api_key``.
    """
    env_vars = _API_KEY_ENV.get(mode or "", ())
    primary = env_vars[0] if env_vars else None
    if primary:
        env_value = os.environ.get(primary)
        if env_value:
            return env_value, f"{primary} env var", bool(config_key)
    if config_key:
        return config_key, "config.toml", False
    for var in env_vars[1:]:
        env_value = os.environ.get(var)
        if env_value:
            return env_value, f"{var} env var", False
    keyless = _KEYLESS_ENV.get(mode or "")
    if keyless and os.environ.get(keyless):
        return None, f"{keyless} env var", False
    return None, None, False


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


def _check_base_url_shape(
    target: ResolvedTarget, api_version: str | None
) -> dict[str, Any] | None:
    """Pure string heuristic against the URL the client will actually dial.

    Flags a base URL that is provably wrong (contains ``/completions``),
    malformed (missing scheme or host), or missing the conventional ``/v1``
    suffix. WARN-level findings use ``ok=None`` with the guidance carried
    inside ``value``; INFO and healthy findings use ``ok=True``. Every value
    names the provenance of the URL, which may well be an env var rather than
    config — that redirect case is precisely what a config-string check missed.

    Args:
        target: The resolved target from :func:`resolve_target`.
        api_version: Azure API version from config, or None. When set the
            backend routes to AzureChatOpenAI, whose dialed URL ends in
            ``openai/deployments/<name>/``, so the ``/v1`` rule would fire on
            a *correct* config and the heuristic is skipped.

    Returns:
        A verify-style dict with ``ok`` (``None`` | ``True``) and ``value``
        (str), or None when the check does not apply (Azure, or a sentinel
        target that is not a URL at all).
    """
    if api_version or target.url in ("n/a", _UNSET_TARGET):
        return None
    url = target.url
    src = f"(source: {target.source})"
    if "/completions" in url:
        return {
            "ok": None,
            "value": (
                f"{url} — contains '/completions'; use the base URL only "
                f"e.g. https://host/v1 (mcp-coder appends /chat/completions) {src}"
            ),
        }
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        return {
            "ok": None,
            "value": f"{url} — malformed URL; use e.g. https://host/v1 {src}",
        }
    if not url.rstrip("/").endswith("/v1"):
        return {
            "ok": True,
            "value": f"{url} — most relays use .../v1 {src}",
        }
    return {"ok": True, "value": f"{url} {src}"}


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
    api_key, key_source, key_overridden = _resolve_api_key(
        mode_of(config), config_api_key
    )
    if backend == "ollama" and api_key is None:
        # Ollama runs unauthenticated on plain localhost — treat missing key
        # as optional rather than a failure.
        result["api_key"] = {
            "ok": True,
            "value": "not set (optional)",
            "source": None,
        }
    else:
        result["api_key"] = {
            "ok": api_key is not None,
            "value": _mask_api_key(api_key),
            "source": key_source,
        }

    # Effective-config echo. This is the single resolve_target() call of the
    # run; the ResolvedTarget it returns is shared by every consumer below, so
    # nothing constructs a chat model twice. The rows are stored as a *list*,
    # which _format_section, _collect_install_hints and _compute_exit_code all
    # skip, so the echo is structurally symbol-free and exit-neutral.
    target = resolve_target(config)
    result["effective_config"] = describe_effective_config(
        config,
        target,
        api_key_masked=_mask_api_key(api_key),
        api_key_source=key_source,
        api_key_overridden=key_overridden,
    )

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

    # Base-URL-shape heuristic over the *resolved* target, reusing the probe
    # above — advisory only, never contributes to overall_ok. The gate stays at
    # openai: /v1 is an OpenAI/relay convention, and a correct ollama host has
    # no /v1 at all. An OLLAMA_HOST redirect is surfaced by the row below.
    if backend == "openai":
        shape = _check_base_url_shape(target, config.get("api_version"))
        if shape is not None:
            result["base_url_shape"] = shape

    # Exit-neutral flags: something outside config.toml won. The redirect row
    # is keyed on the variable that actually *produced* the dialed URL, not on
    # "some redirect variable is exported", and is suppressed when config
    # already implied that URL — nothing was redirected in that case.
    cfg_base = config.get("base_url")
    env_var = redirect_env_in_effect(config, target.url)
    if env_var and not (cfg_base and _targets_match(cfg_base, target.url)):
        result["base_url_redirect"] = {
            "ok": None,
            "value": (f"{env_var} overrides config.toml — requests go to {target.url}"),
        }
    # Built from the api-key resolution, never from env_var above: that is a
    # base-URL variable and is None in most runs.
    if key_overridden:
        result["api_key_override"] = {
            "ok": None,
            "value": f"{key_source} overrides [llm.langchain] api_key in config.toml",
        }

    # MCP adapter packages check (always run)
    mcp_pkg_results = _check_mcp_adapter_packages()
    result["mcp_adapters"] = mcp_pkg_results["mcp_adapters"]
    result["langgraph"] = mcp_pkg_results["langgraph"]

    # Ollama-specific daemon reachability probe
    if backend == "ollama":
        from . import _models

        result["ollama_daemon"] = _models._check_ollama_daemon(
            api_key, config.get("base_url")
        )
        if model:
            result["ollama_tools_capability"] = _models.check_ollama_tool_capability(
                model, api_key, config.get("base_url")
            )

    # Check models (optional)
    if check_models and backend:
        result["available_models"] = _list_models_for_backend(
            backend, api_key, config.get("base_url")
        )

    # overall_ok: True when backend configured AND all required packages installed
    overall_ok = bool(
        backend
        and result["backend_package"]["ok"]
        and result["mcp_adapters"]["ok"]
        and result["langgraph"]["ok"]
    )
    if backend == "ollama":
        overall_ok = overall_ok and result["ollama_daemon"]["ok"]
        if "ollama_tools_capability" in result:
            overall_ok = overall_ok and result["ollama_tools_capability"]["ok"]
    result["overall_ok"] = overall_ok

    return result


def _list_models_for_backend(
    backend: str, api_key: str | None, base_url: str | None
) -> dict[str, Any]:
    """List models for the given backend using existing _models.py functions.

    Args:
        backend: Backend name ("openai", "gemini", "anthropic", or "ollama").
        api_key: API key for the backend, or None.
        base_url: Optional custom base URL (used by OpenAI and Ollama backends).

    Returns:
        Dict with 'ok' (bool), 'value' (list of model names), and optionally 'error'.
    """
    try:
        from . import _models

        if backend == "openai":
            models = _models.list_openai_models(api_key, base_url)
        elif backend == "gemini":
            models = _models.list_gemini_models(api_key)
        elif backend == "anthropic":
            models = _models.list_anthropic_models(api_key)
        elif backend == "ollama":
            models = _models.list_ollama_models(api_key, base_url)
        else:
            return {"ok": False, "value": [], "error": f"Unknown backend: {backend}"}
        return {"ok": True, "value": models}
    except LLMConnectionError as exc:
        return {"ok": False, "value": [], "error": str(exc), "error_type": "connection"}
    except LLMAuthError as exc:
        return {"ok": False, "value": [], "error": str(exc), "error_type": "auth"}
    except Exception as exc:  # pylint: disable=broad-exception-caught
        msg = str(exc)
        low = msg.lower()
        if base_url and ("404" in low or "not found" in low or "not_found" in low):
            return {
                "ok": False,
                "value": [],
                "error": (
                    f"{msg} — base_url likely wrong; use the base URL "
                    "e.g. …/v1 (mcp-coder appends /chat/completions)"
                ),
                "error_type": "base_url",
            }
        return {"ok": False, "value": [], "error": msg, "error_type": "unknown"}


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
