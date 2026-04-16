"""Verify command for the MCP Coder CLI.

Orchestrates three domain verification functions (Claude CLI, LangChain,
MLflow) and formats their output for the terminal.
"""

import argparse
import datetime
import json
import keyword
import logging
import os
import re
import sys
import textwrap
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any

from ...llm.env import prepare_llm_environment
from ...llm.interface import prompt_llm
from ...llm.mlflow_logger import verify_mlflow
from ...llm.providers.claude.claude_cli_verification import verify_claude
from ...llm.providers.claude.claude_executable_finder import find_claude_executable
from ...prompts.prompt_loader import get_project_prompt_path, is_claude_md, load_prompts
from ...utils.mcp_verification import ClaudeMCPStatus, parse_claude_mcp_list
from ...utils.user_config import verify_config
from ..utils import resolve_llm_method, resolve_mcp_config_path

logger = logging.getLogger(__name__)

STATUS_SYMBOLS: dict[str, str] = {
    "success": "[OK]",
    "failure": "[ERR]",
    "warning": "[WARN]",
}

_ENVIRONMENT_PACKAGES: tuple[str, ...] = (
    "mcp-coder",
    "mcp-coder-utils",
    "mcp-tools-py",
    "mcp-workspace",
)


class _DropUnexpandedWarnings(logging.Filter):
    """Scoped filter that drops langchain-mcp-adapters unresolved-var warnings."""

    def filter(self, record: logging.LogRecord) -> bool:
        return "unexpanded variable" not in record.getMessage()


def _collect_mcp_warnings(mcp_json_path: str | None) -> list[str]:
    """Parse ``.mcp.json`` for unresolved ``${...}`` placeholders in env values.

    Args:
        mcp_json_path: Path to ``.mcp.json`` (or None).

    Returns:
        Pre-formatted lines ``"server / env_var  unresolved_template"``; empty
        if there are no findings or the file is missing/invalid.
    """
    if mcp_json_path is None:
        return []
    try:
        data = json.loads(Path(mcp_json_path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    lines: list[str] = []
    for server_name, server in data.get("mcpServers", {}).items():
        for env_var, value in server.get("env", {}).items():
            if isinstance(value, str) and re.search(r"\$\{[^}]+\}", value):
                lines.append(f"{server_name} / {env_var}  {value}")
    return lines


def _print_environment_section() -> None:
    """Print the ENVIRONMENT section (Python info + 4 package versions).

    Uses ``sys``, ``os.environ``, ``importlib.metadata``. Writes directly to
    stdout via ``print`` to match the style of inline sections in
    ``execute_verify``.
    """
    print(_pad("ENVIRONMENT"))
    python_version = (
        f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    )
    print(f"  {'Python version':<20s} {python_version}")
    print(f"  {'Executable':<20s} {sys.executable}")
    virtualenv = sys.prefix if sys.prefix != sys.base_prefix else "(none)"
    print(f"  {'Virtualenv':<20s} {virtualenv}")
    pythonpath = os.environ.get("PYTHONPATH") or "(not set)"
    print(f"  {'PYTHONPATH':<20s} {pythonpath}")
    print()
    for pkg in _ENVIRONMENT_PACKAGES:
        try:
            value = version(pkg)
        except PackageNotFoundError:
            value = "[ERR] not installed"
        print(f"  {pkg:<20s} {value}")


def _pad(title: str) -> str:
    """Return a section header line padded to 60 chars with '=' (never truncated).

    Args:
        title: Section title (without surrounding '===').

    Returns:
        Header line prefixed with '\\n' for the required blank line above.
    """
    prefix = f"=== {title} "
    return "\n" + prefix + "=" * max(0, 60 - len(prefix))


_KEY_REGEX = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _looks_like_key(token: str) -> bool:
    """Return True if ``token`` looks like a Python-identifier key.

    The token must match ``^[A-Za-z_][A-Za-z0-9_]*$`` and must not be a
    reserved Python keyword (which would make rendering it as a key column
    misleading, e.g. ``not configured``).
    """
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
    lines: list[str] = [_pad(title)]
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
            lines.append(f"                           -> {entry['install_hint']}")
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
    title_suffix = " \u2014 for completeness" if for_completeness else ""
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
                    f"  {name:<20s} {symbol} {len(tool_names)} tools available"
                )
                for tool_name, desc in tool_names:
                    if desc:
                        lines.append(f"    {tool_name:<{max_name + 2}s} {desc}")
                    else:
                        lines.append(f"    {tool_name}")
            else:
                lines.append(f"  {name:<20s} {symbol} {value}")
    else:
        for name, entry in servers.items():
            ok = entry.get("ok")
            value = entry.get("value", "")
            symbol = symbols["success"] if ok else symbols["failure"]
            tool_names = entry.get("tool_names")
            if tool_names:
                prefix = f"  {name:<20s} {symbol} "
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
                lines.append(f"  {name:<20s} {symbol} {value}")
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
    title_suffix = " \u2014 for completeness" if for_completeness else ""
    lines: list[str] = [_pad(f"MCP SERVERS (via Claude Code{title_suffix})")]
    for status in statuses:
        symbol = symbols["success"] if status.ok else symbols["failure"]
        lines.append(f"  {status.name:<20s} {symbol} {status.status_text}")
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
    claude_mcp_ok: bool | None = None,
) -> int:
    """Compute CLI exit code from verification results.

    Exit 1 when the config has errors, the active provider fails, when MLflow
    is enabled but broken, when the test prompt failed, or when MCP servers
    failed (langchain only), or when Claude MCP servers failed (claude only).

    Args:
        active_provider: The active LLM provider name.
        claude_result: Claude verification result dict.
        langchain_result: LangChain verification result dict, or None.
        mlflow_result: MLflow verification result dict.
        test_prompt_ok: Whether the test prompt succeeded.
        mcp_result: MCP server health check result dict, or None.
        config_has_error: Whether config verification found errors (invalid TOML).
        claude_mcp_ok: Claude MCP server status. None=not checked (no effect),
            True=all ok, False=failure (exit 1 when claude active).

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

    # Claude MCP failures affect exit code when claude is active
    if active_provider == "claude" and claude_mcp_ok is False:
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


def _prompt_source(configured: str | None, default_label: str) -> str:
    """Format a prompt source for display.

    Returns:
        The configured path, or the default_label in parentheses.
    """
    return configured if configured else f"({default_label})"


def execute_verify(args: argparse.Namespace) -> int:
    """Execute verify command: orchestrate domain checks and format output.

    Args:
        args: Command line arguments (expects args.check_models: bool)

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    logger.info("Executing verify command")
    symbols = STATUS_SYMBOLS
    _print_environment_section()

    # 0. Config verification (first section) with TOML-style grouping
    config_result = verify_config()
    print(_pad("CONFIG"))
    status_symbol_map = {
        "ok": symbols["success"],
        "warning": symbols["warning"],
        "error": symbols["failure"],
    }
    last_label: str | None = None
    for entry in config_result["entries"]:
        label = entry["label"]
        status = entry["status"]
        symbol = status_symbol_map.get(status, "")
        value = entry["value"]
        if label.startswith("["):
            if label != last_label:
                if last_label is not None:
                    print()  # blank line between groups
                print(f"  {label}")
                last_label = label
            first, _sep, rest = value.partition(" ")
            if _looks_like_key(first) and rest:
                print(f"    {first:<18s} {symbol} {rest}")
            elif symbol.strip():
                print(f"    {symbol} {value}")
            else:
                print(f"    {value}")
        else:
            # Top-level rows (Config file, Expected path, Hint, Parse error)
            print(f"  {label:<20s} {symbol} {value}")

    # 0b. Prompt configuration section
    project_dir = Path(args.project_dir).resolve() if args.project_dir else Path.cwd()
    _sys_prompt, _proj_prompt, prompt_config = load_prompts(project_dir)
    active_provider, source = resolve_llm_method(args.llm_method)

    prompt_lines = [_pad("PROMPTS")]
    prompt_lines.append(
        f"  {'System prompt':<20s} {symbols['success']}"
        f" {_prompt_source(prompt_config.system_prompt, 'shipped default')}"
    )
    prompt_lines.append(
        f"  {'Project prompt':<20s} {symbols['success']}"
        f" {_prompt_source(prompt_config.project_prompt, 'shipped default')}"
    )
    prompt_lines.append(
        f"  {'Claude mode':<20s} {symbols['success']}"
        f" {prompt_config.claude_system_prompt_mode}"
    )
    if active_provider == "claude" and prompt_config.project_prompt:
        prompt_path = get_project_prompt_path(project_dir)
        if is_claude_md(prompt_path, str(project_dir)):
            prompt_lines.append(
                f"  {'Redundancy':<20s} {symbols['warning']}"
                " project prompt is CLAUDE.md (will skip for Claude)"
            )
    print("\n".join(prompt_lines))

    # 1. Resolve active provider (already done above)

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
    print(_pad("LLM PROVIDER"))
    print(
        f"  {'Active provider':<20s} {symbols['success']} {active_provider} (from {source})"
    )
    # 2a. Resolve MCP config for ALL providers (before provider branch)
    mcp_config_resolved = resolve_mcp_config_path(
        args.mcp_config, project_dir=args.project_dir
    )

    if active_provider == "langchain":
        check_models = getattr(args, "check_models", False)
        from ...llm.providers.langchain.verification import verify_langchain

        langchain_result = verify_langchain(
            check_models=check_models,
            mcp_config_path=mcp_config_resolved,
        )
        print(_format_section("LLM PROVIDER DETAILS", langchain_result, symbols))
    else:
        print("  (uses Claude CLI — see Basic Verification above)")

    # 3a. MCP server health checks (provider-aware ordering)
    mcp_result: dict[str, Any] | None = None
    claude_mcp: list[ClaudeMCPStatus] | None = None

    if mcp_config_resolved:
        # Run Claude MCP list
        env_vars = prepare_llm_environment(project_dir)
        claude_exe = find_claude_executable(return_none_if_not_found=True)
        claude_mcp = parse_claude_mcp_list(env_vars, claude_executable=claude_exe)

        # Run LangChain MCP health check
        try:
            from ...llm.providers.langchain.verification import verify_mcp_servers

            lc_logger = logging.getLogger("langchain_mcp_adapters")
            log_filter = _DropUnexpandedWarnings()
            lc_logger.addFilter(log_filter)
            try:
                mcp_result = verify_mcp_servers(mcp_config_resolved, env_vars=env_vars)
            finally:
                lc_logger.removeFilter(log_filter)
        except ImportError:
            mcp_result = None

        list_mcp_tools = getattr(args, "list_mcp_tools", False)
        lc_for_completeness = active_provider == "claude"
        claude_for_completeness = active_provider != "claude"

        if active_provider == "claude":
            # Claude MCP section first (primary)
            if claude_mcp is not None:
                print(
                    _format_claude_mcp_section(
                        claude_mcp, symbols, for_completeness=False
                    )
                )
            # LangChain MCP section second (for completeness)
            if mcp_result is not None:
                print(
                    _format_mcp_section(
                        mcp_result,
                        symbols,
                        list_mcp_tools=list_mcp_tools,
                        for_completeness=lc_for_completeness,
                    )
                )
            else:
                print(_pad("MCP SERVERS (via langchain-mcp-adapters)"))
                print(
                    f"  {symbols['warning']} server health check skipped"
                    " (langchain-mcp-adapters not installed)"
                )
        else:
            # LangChain MCP section first (primary)
            if mcp_result is not None:
                print(
                    _format_mcp_section(
                        mcp_result,
                        symbols,
                        list_mcp_tools=list_mcp_tools,
                        for_completeness=False,
                    )
                )
            else:
                print(_pad("MCP SERVERS (via langchain-mcp-adapters)"))
                print(
                    f"  {symbols['warning']} server health check skipped"
                    " (langchain-mcp-adapters not installed)"
                )
            # Claude MCP section second (for completeness)
            if claude_mcp is not None:
                print(
                    _format_claude_mcp_section(
                        claude_mcp, symbols, for_completeness=claude_for_completeness
                    )
                )

    # Compute claude_mcp_ok for exit code
    claude_mcp_ok: bool | None = None
    if active_provider == "claude" and mcp_config_resolved:
        if claude_mcp is None:
            claude_mcp_ok = False  # parser failure = hard failure per Decision 12
        elif all(s.ok for s in claude_mcp):
            claude_mcp_ok = True
        else:
            claude_mcp_ok = False

    # 3a-bis. MCP config warnings (unresolved ${...} placeholders)
    if mcp_config_resolved:
        warnings = _collect_mcp_warnings(mcp_config_resolved)
        if warnings:
            print(_pad("MCP CONFIG WARNINGS"))
            for warning_line in warnings:
                print(f"  {warning_line}")

    # 3b. MCP edit smoke test (informational only)
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
        prompt_llm(
            "Reply with OK",
            provider=active_provider,
            timeout=30,
            mcp_config=mcp_config_resolved,
            execution_dir=str(project_dir),
        )
        print(f"  {'Test prompt':<20s} {symbols['success']} responded OK")
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
            print(_pad("INSTALL INSTRUCTIONS"))
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
        claude_mcp_ok=claude_mcp_ok,
    )
    logger.info("Verify command completed with exit code %d", exit_code)
    return exit_code
