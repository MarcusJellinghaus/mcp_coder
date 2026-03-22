"""Verify command for the MCP Coder CLI.

Orchestrates three domain verification functions (Claude CLI, LangChain,
MLflow) and formats their output for the terminal.
"""

import argparse
import datetime
import logging
from typing import Any

from ...llm.interface import ask_llm
from ...llm.mlflow_logger import verify_mlflow
from ...llm.providers.claude.claude_cli_verification import verify_claude
from ...llm.providers.langchain.verification import verify_langchain
from ..utils import _get_status_symbols, resolve_llm_method, resolve_mcp_config_path

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
    "available_models": "Available models",
    # MCP adapter section
    "mcp_adapters": "MCP adapters",
    "langgraph": "LangGraph",
    "mcp_agent_test": "MCP agent test",
    # MLflow section
    "installed": "MLflow installed",
    "enabled": "MLflow enabled",
    "tracking_uri": "Tracking URI",
    "connection": "Connection",
    "experiment": "Experiment",
    "artifact_location": "Artifact location",
    "tracking_data": "Tracking data",
}


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
        line = f"  {label:<20s} {symbol} {value}"
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
    test_prompt_ok: bool = True,
) -> int:
    """Compute CLI exit code from verification results.

    Exit 1 when the active provider fails, when MLflow is enabled but broken,
    or when the test prompt failed.

    Args:
        active_provider: The active LLM provider name.
        claude_result: Claude verification result dict.
        langchain_result: LangChain verification result dict, or None.
        mlflow_result: MLflow verification result dict.
        test_prompt_ok: Whether the test prompt succeeded.

    Returns:
        Exit code (0 if all checks pass, 1 if any critical check failed).
    """
    # Test prompt failure always means exit 1
    if not test_prompt_ok:
        return 1

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
    active_provider, source = resolve_llm_method(args.llm_method)

    # 2. Claude CLI verification
    claude_result = verify_claude()
    print(_format_section("BASIC VERIFICATION", claude_result, symbols))

    # 3. LangChain verification (only when provider is langchain)
    langchain_result: dict[str, Any] | None = None
    print("\n=== LLM PROVIDER ===")
    print(
        f"  {'Active provider':<20s} {symbols['success']} {active_provider} (from {source})"
    )
    if active_provider == "langchain":
        check_models = getattr(args, "check_models", False)
        mcp_config_resolved = resolve_mcp_config_path(
            args.mcp_config, project_dir=args.project_dir
        )
        langchain_result = verify_langchain(
            check_models=check_models,
            mcp_config_path=mcp_config_resolved,
        )
        print(_format_section("LLM PROVIDER DETAILS", langchain_result, symbols))
    else:
        print("  (uses Claude CLI — see Basic Verification above)")

    # 3b. Unified test prompt (both providers)
    test_prompt_ok = True
    timestamp = datetime.datetime.now(datetime.timezone.utc)
    try:
        ask_llm("Reply with OK", provider=active_provider, timeout=30)
        print(f"  {'Test prompt':<20s} {symbols['success']} responded OK")
    except Exception as exc:  # pylint: disable=broad-except
        test_prompt_ok = False
        print(f"  {'Test prompt':<20s} {symbols['failure']} FAILED ({exc})")

    # 4. MLflow verification
    mlflow_result = verify_mlflow(since=timestamp)
    print(_format_section("MLFLOW", mlflow_result, symbols))

    # 5. Compute and return exit code
    exit_code = _compute_exit_code(
        active_provider,
        claude_result,
        langchain_result,
        mlflow_result,
        test_prompt_ok=test_prompt_ok,
    )
    logger.info("Verify command completed with exit code %d", exit_code)
    return exit_code
