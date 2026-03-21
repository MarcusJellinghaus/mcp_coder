"""LangChain provider verification functionality.

Provides verify_langchain() which checks configuration, packages, API key,
and optionally sends a test prompt. Returns a structured dict (no printing).
"""

from __future__ import annotations

import importlib.util
import os
import time
from typing import Any

from . import _load_langchain_config, ask_langchain

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
    return {
        "mcp_adapters": {
            "ok": mcp_ok,
            "value": (
                "langchain-mcp-adapters installed"
                if mcp_ok
                else "langchain-mcp-adapters not installed"
            ),
        },
        "langgraph": {
            "ok": lg_ok,
            "value": "langgraph installed" if lg_ok else "langgraph not installed",
        },
    }


def verify_langchain(
    check_models: bool = False,
    mcp_config_path: str | None = None,
    env_vars: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Verify LangChain provider configuration and connectivity.

    Returns a structured dict with verification results (no printing).
    The CLI layer handles all output formatting.

    Args:
        check_models: If True, also list available models for the backend.
        mcp_config_path: Path to .mcp.json for MCP agent smoke test.
        env_vars: Optional environment variables for var substitution.

    Returns:
        Dict with keys: backend, model, api_key, langchain_core,
        backend_package, mcp_adapters, langgraph, test_prompt, overall_ok.
        If mcp_config_path is provided, also includes mcp_agent_test.
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
    else:
        result["backend_package"] = {
            "ok": False,
            "value": "no backend configured",
        }

    # MCP adapter packages check (always run)
    mcp_pkg_results = _check_mcp_adapter_packages()
    result["mcp_adapters"] = mcp_pkg_results["mcp_adapters"]
    result["langgraph"] = mcp_pkg_results["langgraph"]

    # Test prompt
    if api_key and backend:
        start = time.monotonic()
        try:
            ask_langchain("Reply with OK", timeout=15)
            elapsed = time.monotonic() - start
            result["test_prompt"] = {
                "ok": True,
                "value": f"responded in {elapsed:.1f}s",
                "error": None,
            }
        except Exception as exc:
            result["test_prompt"] = {
                "ok": False,
                "value": None,
                "error": str(exc),
            }
    else:
        result["test_prompt"] = {
            "ok": None,
            "value": "skipped (no API key)" if not api_key else "skipped (no backend)",
            "error": None,
        }

    # Check models (optional)
    if check_models and backend:
        result["available_models"] = _list_models_for_backend(
            backend, api_key, config.get("endpoint")
        )

    # End-to-end MCP agent test (only when mcp_config_path provided)
    if mcp_config_path:
        try:
            from ...interface import ask_llm  # lazy to avoid circular import

            ask_llm(
                "Reply with OK",
                provider="langchain",
                mcp_config=mcp_config_path,
                env_vars=env_vars,
                timeout=30,
            )
            result["mcp_agent_test"] = {"ok": True, "value": "agent responded"}
        except FileNotFoundError as exc:
            result["mcp_agent_test"] = {
                "ok": False,
                "value": None,
                "error": f"MCP config not found: {exc}",
            }
        except ImportError as exc:
            result["mcp_agent_test"] = {
                "ok": False,
                "value": None,
                "error": f"Missing dependency: {exc}",
            }
        except ConnectionError as exc:
            result["mcp_agent_test"] = {
                "ok": False,
                "value": None,
                "error": f"MCP server failed to start: {exc}",
            }
        except Exception as exc:  # pylint: disable=broad-except
            result["mcp_agent_test"] = {
                "ok": False,
                "value": None,
                "error": f"Agent test failed: {type(exc).__name__}: {exc}",
            }

    # overall_ok: True when backend configured AND backend package installed AND
    # MCP adapter packages installed AND
    # (test_prompt succeeded OR test_prompt was skipped due to no API key)
    test_prompt_ok = (
        result["test_prompt"]["ok"] is True or result["test_prompt"]["ok"] is None
    )
    result["overall_ok"] = bool(
        backend
        and result["backend_package"]["ok"]
        and result["mcp_adapters"]["ok"]
        and result["langgraph"]["ok"]
        and test_prompt_ok
    )

    return result


def _list_models_for_backend(
    backend: str, api_key: str | None, endpoint: str | None
) -> dict[str, Any]:
    """List models for the given backend using existing _models.py functions."""
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
    except Exception as exc:
        return {"ok": False, "value": [], "error": str(exc)}
