"""Verify command for the MCP Coder CLI.

Orchestrates three domain verification functions (Claude CLI, LangChain,
MLflow) and formats their output for the terminal.
"""

import argparse
import datetime
import logging
import textwrap
from pathlib import Path
from typing import Any

from ...llm.interface import prompt_llm
from ...llm.mlflow_logger import verify_mlflow
from ...llm.providers.claude.claude_cli_verification import verify_claude
from ...llm.providers.claude.claude_executable_finder import find_claude_executable
from ...llm.providers.langchain.verification import verify_langchain, verify_mcp_servers
from ...utils.user_config import verify_config
from ..utils import _get_status_symbols, resolve_llm_method, resolve_mcp_config_path
from .prompt import log_to_mlflow

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
        if ok is False and "install_hint" in entry:
            lines.append(f"                           \u2192 {entry['install_hint']}")
    return "\n".join(lines)


def _format_mcp_section(mcp_results: dict[str, Any], symbols: dict[str, str]) -> str:
    """Format MCP server health check results.

    Args:
        mcp_results: Dict containing server health check results.
        symbols: Dict with 'success', 'failure', 'warning' keys.

    Returns:
        Formatted multi-line string for the MCP servers section.
    """
    lines: list[str] = ["\n=== MCP SERVERS ==="]
    for name, entry in mcp_results["servers"].items():
        ok = entry.get("ok")
        value = entry.get("value", "")
        symbol = symbols["success"] if ok else symbols["failure"]
        tool_names = entry.get("tool_names")
        if tool_names:
            prefix = f"  {name:<20s} {symbol} "
            tools_text = f"{len(tool_names)} tools: {', '.join(tool_names)}"
            wrapped = textwrap.wrap(
                tools_text,
                width=80,
                initial_indent=prefix,
                subsequent_indent=" " * len(prefix),
            )
            lines.extend(wrapped)
        else:
            lines.append(f"  {name:<20s} {symbol} {value}")
    return "\n".join(lines)


def _run_mcp_edit_smoke_test(
    project_dir: Path,
    provider: str,
    mcp_config: str,
    execution_dir: str,
    symbols: dict[str, str],
) -> str:
    """Run MCP edit smoke test.

    Args:
        project_dir: Path to the project directory.
        provider: The active LLM provider name.
        mcp_config: Path to the MCP config file.
        execution_dir: Execution directory path.
        symbols: Dict with 'success', 'failure', 'warning' keys.

    Returns:
        Formatted output line for the smoke test result.
    """
    label = "MCP edit smoke test"
    test_file = project_dir / ".mcp_coder_verify.md"
    try:
        test_file.write_text("A\n\nC\n", encoding="utf-8")
        prompt_llm(
            "Edit the file .mcp_coder_verify.md to insert a line 'B' between 'A' and 'C'",
            provider=provider,
            timeout=60,
            mcp_config=mcp_config,
            execution_dir=execution_dir,
        )
        content = test_file.read_text(encoding="utf-8")
        pos_a, pos_b, pos_c = content.find("A"), content.find("B"), content.find("C")
        if pos_a < pos_b < pos_c:
            return f"  {label:<20s} {symbols['success']} edit verified"
        return (
            f"  {label:<20s} {symbols['warning']}"
            " edit not verified (B not found between A and C)"
        )
    except Exception as exc:  # pylint: disable=broad-except
        return f"  {label:<20s} {symbols['warning']} edit not verified ({exc})"
    finally:
        test_file.unlink(missing_ok=True)


def _compute_exit_code(
    active_provider: str,
    claude_result: dict[str, Any],
    langchain_result: dict[str, Any] | None,
    mlflow_result: dict[str, Any],
    test_prompt_ok: bool = True,
    mcp_result: dict[str, Any] | None = None,
    config_has_error: bool = False,
) -> int:
    """Compute CLI exit code from verification results.

    Exit 1 when the config has errors, the active provider fails, when MLflow
    is enabled but broken, when the test prompt failed, or when MCP servers
    failed (langchain only).

    Args:
        active_provider: The active LLM provider name.
        claude_result: Claude verification result dict.
        langchain_result: LangChain verification result dict, or None.
        mlflow_result: MLflow verification result dict.
        test_prompt_ok: Whether the test prompt succeeded.
        mcp_result: MCP server health check result dict, or None.
        config_has_error: Whether config verification found errors (invalid TOML).

    Returns:
        Exit code (0 if all checks pass, 1 if any critical check failed).
    """
    # Config error (invalid TOML) always means exit 1
    if config_has_error:
        return 1

    # Test prompt failure always means exit 1
    if not test_prompt_ok:
        return 1

    # Active provider determines primary pass/fail
    if active_provider == "claude" and not claude_result.get("overall_ok"):
        return 1
    if active_provider == "langchain":
        if langchain_result is None or not langchain_result.get("overall_ok"):
            return 1

    # MCP server failures affect exit code when langchain is active
    if (
        active_provider == "langchain"
        and mcp_result
        and not mcp_result.get("overall_ok")
    ):
        return 1

    # MLflow: only fail if enabled AND broken
    mlflow_enabled = mlflow_result.get("enabled", {})
    if isinstance(mlflow_enabled, dict) and mlflow_enabled.get("ok") is True:
        if not mlflow_result.get("overall_ok"):
            return 1

    return 0


def _collect_install_hints(result: dict[str, Any]) -> list[str]:
    """Collect install_hint values from failed entries in a verification result.

    Returns:
        List of install hint strings from failed entries.
    """
    hints: list[str] = []
    for _key, entry in result.items():
        if isinstance(entry, dict) and not entry.get("ok") and "install_hint" in entry:
            hints.append(entry["install_hint"])
    return hints


def execute_verify(args: argparse.Namespace) -> int:
    """Execute verify command: orchestrate domain checks and format output.

    Args:
        args: Command line arguments (expects args.check_models: bool)

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    logger.info("Executing verify command")
    symbols = _get_status_symbols()

    # 0. Config verification (first section)
    config_result = verify_config()
    lines = ["\n=== CONFIG ==="]
    for entry in config_result["entries"]:
        status = entry["status"]
        symbol = {
            "ok": symbols["success"],
            "warning": symbols["warning"],
            "error": symbols["failure"],
        }.get(status, " ")
        lines.append(f"  {entry['label']:<20s} {symbol} {entry['value']}")
    print("\n".join(lines))

    # 1. Resolve active provider
    active_provider, source = resolve_llm_method(args.llm_method)

    # 2. Claude CLI verification (conditional on provider)
    if active_provider == "claude":
        claude_result = verify_claude()
        print(_format_section("BASIC VERIFICATION", claude_result, symbols))
    else:
        # Quick binary check only
        claude_path = find_claude_executable(return_none_if_not_found=True)
        if claude_path:
            print(f"\n  Claude CLI: available at {claude_path} (not active)")
        claude_result = {"overall_ok": True}  # neutral for exit code

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
        mcp_config_resolved = None
        print("  (uses Claude CLI — see Basic Verification above)")

    # 3a. MCP server health check
    mcp_result: dict[str, Any] | None = None
    if mcp_config_resolved:
        mcp_result = verify_mcp_servers(mcp_config_resolved)
        print(_format_mcp_section(mcp_result, symbols))

    # 3b. MCP edit smoke test (informational only)
    project_dir = Path(args.project_dir).resolve() if args.project_dir else Path.cwd()
    if mcp_config_resolved:
        smoke_line = _run_mcp_edit_smoke_test(
            project_dir,
            active_provider,
            mcp_config_resolved,
            str(project_dir),
            symbols,
        )
        print(smoke_line)

    # 3c. Unified test prompt (both providers)
    timestamp = datetime.datetime.now(datetime.timezone.utc)
    test_prompt_ok = True
    try:
        response = prompt_llm(
            "Reply with OK",
            provider=active_provider,
            timeout=30,
            mcp_config=mcp_config_resolved,
            execution_dir=str(project_dir),
        )
        print(f"  {'Test prompt':<20s} {symbols['success']} responded OK")
        # Log to MLflow (will be confirmed by verify_mlflow's since= check)
        log_to_mlflow(response, "Reply with OK", project_dir)
    except Exception as exc:  # pylint: disable=broad-except
        test_prompt_ok = False
        # Only classify connection-related exceptions
        if isinstance(exc, (OSError, ConnectionError)):
            try:
                from ...llm.providers.langchain._exceptions import (
                    classify_connection_error,
                    format_diagnostics,
                )

                category = classify_connection_error(exc)
                logger.debug("Connection diagnostics:\n%s", format_diagnostics(exc))
            except ImportError:
                category = "Connection error"
        else:
            category = f"{type(exc).__name__}: {exc}"
        print(f"  {'Test prompt':<20s} {symbols['failure']} FAILED ({category})")
        logger.debug("Test prompt failure details: %s", exc, exc_info=True)
        print("  Run with --debug for detailed diagnostics.")

    # 4. MLflow verification (now with since= to confirm logging)
    mlflow_result = verify_mlflow(since=timestamp)
    print(_format_section("MLFLOW", mlflow_result, symbols))

    # 5. Collect and display install hints
    all_hints: list[str] = []
    if langchain_result:
        all_hints.extend(_collect_install_hints(langchain_result))
    if active_provider == "claude":
        all_hints.extend(_collect_install_hints(claude_result))

    if all_hints:
        pip_packages = " ".join(
            h.replace("pip install ", "")
            for h in all_hints
            if h.startswith("pip install")
        )
        if pip_packages:
            print("\n=== INSTALL INSTRUCTIONS ===")
            print(f"  pip install {pip_packages}")

    # 6. Compute and return exit code
    exit_code = _compute_exit_code(
        active_provider,
        claude_result,
        langchain_result,
        mlflow_result,
        test_prompt_ok=test_prompt_ok,
        mcp_result=mcp_result,
        config_has_error=config_result["has_error"],
    )
    logger.info("Verify command completed with exit code %d", exit_code)
    return exit_code
