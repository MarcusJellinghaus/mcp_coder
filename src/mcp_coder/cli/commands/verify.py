"""Verify command for the MCP Coder CLI.

Orchestrates three domain verification functions (Claude CLI, LangChain,
MLflow) and formats their output for the terminal.
"""

import argparse
import logging
import os
from typing import Any

from ...llm.mlflow_logger import verify_mlflow
from ...llm.providers.claude.claude_cli_verification import verify_claude
from ...llm.providers.langchain.verification import verify_langchain
from ...utils.user_config import get_config_values
from ..utils import _get_status_symbols

logger = logging.getLogger(__name__)

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
    "test_prompt": "Test prompt",
    "available_models": "Available models",
    # MLflow section
    "installed": "MLflow installed",
    "enabled": "MLflow enabled",
    "tracking_uri": "Tracking URI",
    "connection": "Connection",
    "experiment": "Experiment",
    "artifact_location": "Artifact location",
}


_VALID_PROVIDERS = {"claude", "langchain"}


def _resolve_active_provider() -> tuple[str, str]:
    """Resolve the active LLM provider from env var, config, or default.

    Returns (provider_name, source_description).
    Deliberately separate from resolve_llm_method() — different return types,
    different env vars, different purposes (Decision 5).

    Raises:
        ValueError: If the resolved provider is not a known value.
    """
    env_val = os.environ.get("MCP_CODER_LLM_PROVIDER")
    if env_val:
        if env_val not in _VALID_PROVIDERS:
            raise ValueError(
                f"Unknown LLM provider '{env_val}' from MCP_CODER_LLM_PROVIDER env var. "
                f"Valid providers: {', '.join(sorted(_VALID_PROVIDERS))}"
            )
        return env_val, "MCP_CODER_LLM_PROVIDER env var"

    config = get_config_values([("llm", "provider", None)])
    provider = config[("llm", "provider")]
    if provider:
        if provider not in _VALID_PROVIDERS:
            raise ValueError(
                f"Unknown LLM provider '{provider}' in config.toml. "
                f"Valid providers: {', '.join(sorted(_VALID_PROVIDERS))}"
            )
        return provider, "config.toml"

    return "claude", "default"


def _format_section(title: str, result: dict[str, Any], symbols: dict[str, str]) -> str:
    """Format a verification section for terminal output.

    Args:
        title: Section title (e.g. "BASIC VERIFICATION")
        result: Dict from a domain verify function
        symbols: Dict with 'success', 'failure', 'warning' keys

    Returns:
        Formatted multi-line string for the section.
    """
    lines: list[str] = [f"\n=== {title} ==="]
    for key, entry in result.items():
        if key == "overall_ok":
            continue
        if not isinstance(entry, dict):
            continue
        label = _LABEL_MAP.get(key, key)
        ok = entry.get("ok")
        value = entry.get("value", "")
        if ok is True:
            symbol = symbols["success"]
        elif ok is False:
            symbol = symbols["failure"]
        else:
            symbol = symbols["warning"]
        line = f"  {label}:   {symbol} {value}"
        error = entry.get("error")
        if error and ok is False:
            line += f" ({error})"
        lines.append(line)
    return "\n".join(lines)


def _compute_exit_code(
    active_provider: str,
    claude_result: dict[str, Any],
    langchain_result: dict[str, Any] | None,
    mlflow_result: dict[str, Any],
) -> int:
    """Compute CLI exit code from verification results.

    Exit 1 when the active provider fails or when MLflow is enabled but broken.
    """
    # Active provider determines primary pass/fail
    if active_provider == "claude" and not claude_result.get("overall_ok"):
        return 1
    if active_provider == "langchain":
        if langchain_result is None or not langchain_result.get("overall_ok"):
            return 1

    # MLflow: only fail if enabled AND broken
    mlflow_enabled = mlflow_result.get("enabled", {})
    if isinstance(mlflow_enabled, dict) and mlflow_enabled.get("ok") is True:
        if not mlflow_result.get("overall_ok"):
            return 1

    return 0


def execute_verify(args: argparse.Namespace) -> int:
    """Execute verify command: orchestrate domain checks and format output.

    Args:
        args: Command line arguments (expects args.check_models: bool)

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    logger.info("Executing verify command")
    symbols = _get_status_symbols()

    # 1. Resolve active provider
    active_provider, source = _resolve_active_provider()

    # 2. Claude CLI verification
    claude_result = verify_claude()
    print(_format_section("BASIC VERIFICATION", claude_result, symbols))

    # 3. LangChain verification (only when provider is langchain)
    langchain_result: dict[str, Any] | None = None
    print(f"\n=== LLM PROVIDER ===")
    print(
        f"  Active provider:   {symbols['success']} {active_provider} (from {source})"
    )
    if active_provider == "langchain":
        check_models = getattr(args, "check_models", False)
        langchain_result = verify_langchain(check_models=check_models)
        print(_format_section("LLM PROVIDER DETAILS", langchain_result, symbols))
    else:
        print("  (uses Claude CLI — see Basic Verification above)")

    # 4. MLflow verification
    mlflow_result = verify_mlflow()
    print(_format_section("MLFLOW", mlflow_result, symbols))

    # 5. Compute and return exit code
    exit_code = _compute_exit_code(
        active_provider, claude_result, langchain_result, mlflow_result
    )
    logger.info("Verify command completed with exit code %d", exit_code)
    return exit_code
