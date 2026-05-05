"""Verify command for the MCP Coder CLI.

Orchestrates four domain verification functions (Claude CLI, LangChain,
MLflow, GitHub) and formats their output for the terminal.
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
from ...mcp_workspace_git import verify_git
from ...mcp_workspace_github import verify_github
from ...prompts.prompt_loader import get_project_prompt_path, is_claude_md, load_prompts
from ...utils.mcp_verification import ClaudeMCPStatus, parse_claude_mcp_list
from ...utils.pyproject_config import get_implement_config
from ...utils.user_config import verify_config
from ..utils import resolve_llm_method, resolve_mcp_config_path

logger = logging.getLogger(__name__)

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


def _collect_mcp_warnings(mcp_json_path: str | None) -> list[tuple[str, str]]:
    """Parse ``.mcp.json`` for unresolved ``${...}`` placeholders in env values.

    Args:
        mcp_json_path: Path to ``.mcp.json`` (or None).

    Returns:
        List of ``(label, value)`` pairs where ``label`` has the form
        ``"<server> / <env_var>"`` and ``value`` is the unresolved template.
        Empty if there are no findings or the file is missing/invalid.
    """
    if mcp_json_path is None:
        return []
    try:
        data = json.loads(Path(mcp_json_path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    findings: list[tuple[str, str]] = []
    for server_name, server in data.get("mcpServers", {}).items():
        for env_var, value in server.get("env", {}).items():
            if isinstance(value, str) and re.search(r"\$\{[^}]+\}", value):
                findings.append((f"{server_name} / {env_var}", value))
    return findings


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
    print(_format_row("Python version", "", python_version, indent=2))
    print(_format_row("Executable", "", sys.executable, indent=2))
    virtualenv = sys.prefix if sys.prefix != sys.base_prefix else "(none)"
    print(_format_row("Virtualenv", "", virtualenv, indent=2))
    pythonpath = os.environ.get("PYTHONPATH") or "(not set)"
    print(_format_row("PYTHONPATH", "", pythonpath, indent=2))
    print()
    for pkg in _ENVIRONMENT_PACKAGES:
        try:
            value = version(pkg)
            print(_format_row(pkg, "", value, indent=2))
        except PackageNotFoundError:
            print(
                _format_row(pkg, STATUS_SYMBOLS["failure"], "not installed", indent=2)
            )


def _print_project_section(project_dir: Path, symbols: dict[str, str]) -> None:
    """Print the PROJECT section showing language detection and tool config.

    Args:
        project_dir: Path to the project directory.
        symbols: Dict with 'success', 'failure', 'warning' keys.
    """
    print(_pad("PROJECT"))
    pyproject_exists = (project_dir / "pyproject.toml").exists()
    if pyproject_exists:
        print(_format_row("pyproject.toml", symbols["success"], "found", indent=2))
        print(
            _format_row("Language", symbols["success"], "Python (detected)", indent=2)
        )
        config = get_implement_config(project_dir)
        print()
        print("  [Python]")
        if config.format_code:
            print(_format_row("format_code", symbols["success"], "enabled", indent=4))
        else:
            print(
                _format_row(
                    "format_code",
                    symbols["warning"],
                    "not configured (default: disabled)",
                    indent=4,
                )
            )
        if config.check_type_hints:
            print(
                _format_row("check_type_hints", symbols["success"], "enabled", indent=4)
            )
        else:
            print(
                _format_row(
                    "check_type_hints",
                    symbols["warning"],
                    "not configured (default: disabled)",
                    indent=4,
                )
            )
    else:
        print(_format_row("pyproject.toml", symbols["warning"], "not found", indent=2))
        print(_format_row("Language", symbols["success"], "(none detected)", indent=2))


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
    # GitHub section
    "api_base_url": "API base URL",
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
    title_suffix = " \u2014 for completeness" if for_completeness else ""
    lines: list[str] = [_pad(f"MCP SERVERS (via Claude Code{title_suffix})")]
    for status in statuses:
        symbol = symbols["success"] if status.ok else symbols["failure"]
        lines.append(_format_row(status.name, symbol, status.status_text, indent=2))
    return "\n".join(lines)


def _run_mcp_edit_smoke_test(
    project_dir: Path,
    provider: str,
    mcp_config: str,
    execution_dir: str,
    symbols: dict[str, str],
    env_vars: dict[str, str] | None = None,
) -> str:
    """Run MCP edit smoke test.

    Args:
        project_dir: Path to the project directory.
        provider: The active LLM provider name.
        mcp_config: Path to the MCP config file.
        execution_dir: Execution directory path.
        symbols: Dict with 'success', 'failure', 'warning' keys.
        env_vars: Environment variables passed to the LLM subprocess so
            ``${MCP_CODER_*}`` placeholders in ``.mcp.json`` resolve.

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
            env_vars=env_vars,
        )
        content = test_file.read_text(encoding="utf-8")
        pos_a, pos_b, pos_c = content.find("A"), content.find("B"), content.find("C")
        if pos_a < pos_b < pos_c:
            return _format_row(label, symbols["success"], "edit verified", indent=2)
        return _format_row(
            label,
            symbols["warning"],
            "edit not verified (B not found between A and C)",
            indent=2,
        )
    except Exception as exc:  # pylint: disable=broad-except
        return _format_row(
            label,
            symbols["warning"],
            f"edit not verified ({exc})",
            indent=2,
        )
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
    github_result: dict[str, Any] | None = None,
    git_result: dict[str, Any] | None = None,
) -> int:
    """Compute CLI exit code from verification results.

    Exit 1 when the config has errors, the active provider fails, when MLflow
    is enabled but broken, when the test prompt failed, when GitHub verification
    failed, when git verification failed, when MCP servers failed (langchain
    only), or when Claude MCP servers failed (claude only).

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
        github_result: GitHub verification result dict, or None.
        git_result: Git verification result dict, or None.

    Returns:
        Exit code (0 if all checks pass, 1 if any critical check failed).
    """
    # Config error (invalid TOML) always means exit 1
    if config_has_error:
        return 1

    # Test prompt failure always means exit 1
    if not test_prompt_ok:
        return 1

    # GitHub failure always means exit 1 (provider-independent)
    if github_result is not None and not github_result.get("overall_ok"):
        return 1

    # Git failure always means exit 1 (provider-independent)
    if git_result is not None and not git_result.get("overall_ok"):
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

    Args:
        result: Verification result dict from a domain verify function.

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

    Args:
        configured: Configured prompt path, or None if not set.
        default_label: Label shown in parentheses when ``configured`` is None.

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
                print(_format_row(first, symbol, rest, indent=4))
            elif symbol.strip():
                print(_format_row("", symbol, value, indent=4))
            else:
                print(_format_row("", "", value, indent=4))
        else:
            # Top-level rows (Config file, Expected path, Hint, Parse error)
            print(_format_row(label, symbol, value, indent=2))

    # 0b. Prompt configuration section
    project_dir = Path(args.project_dir).resolve() if args.project_dir else Path.cwd()
    _sys_prompt, _proj_prompt, prompt_config = load_prompts(project_dir)
    active_provider, source = resolve_llm_method(args.llm_method)

    prompt_lines = [_pad("PROMPTS")]
    prompt_lines.append(
        _format_row(
            "System prompt",
            symbols["success"],
            _prompt_source(prompt_config.system_prompt, "shipped default"),
            indent=2,
        )
    )
    prompt_lines.append(
        _format_row(
            "Project prompt",
            symbols["success"],
            _prompt_source(prompt_config.project_prompt, "shipped default"),
            indent=2,
        )
    )
    prompt_lines.append(
        _format_row(
            "Claude mode",
            symbols["success"],
            prompt_config.claude_system_prompt_mode,
            indent=2,
        )
    )
    if active_provider == "claude" and prompt_config.project_prompt:
        prompt_path = get_project_prompt_path(project_dir)
        if is_claude_md(prompt_path, str(project_dir)):
            prompt_lines.append(
                _format_row(
                    "Redundancy",
                    symbols["warning"],
                    "project prompt is CLAUDE.md (will skip for Claude)",
                    indent=2,
                )
            )
    print("\n".join(prompt_lines))

    # 0c. Project configuration section
    _print_project_section(project_dir, symbols)

    # 0d. Git verification section
    git_result = verify_git(project_dir, actually_sign=True)
    print(_format_section("GIT", git_result, symbols))

    # 0e. GitHub verification section
    github_result = verify_github(project_dir)
    print(_format_section("GITHUB", github_result, symbols))

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
        _format_row(
            "Active provider",
            symbols["success"],
            f"{active_provider} (from {source})",
            indent=2,
        )
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
    # Compute MCP_CODER_* env vars once: needed by the Claude/LangChain MCP
    # health checks AND by the smoke test / test prompt below so .mcp.json
    # placeholders like ${MCP_CODER_VENV_PATH} resolve in the subprocess.
    env_vars = prepare_llm_environment(project_dir)

    if mcp_config_resolved:
        # Run Claude MCP list
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
                    _format_row(
                        "",
                        symbols["warning"],
                        "server health check skipped"
                        " (langchain-mcp-adapters not installed)",
                        indent=2,
                    )
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
                    _format_row(
                        "",
                        symbols["warning"],
                        "server health check skipped"
                        " (langchain-mcp-adapters not installed)",
                        indent=2,
                    )
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
            section_label_width = max(
                _LABEL_WIDTH, max(len(label) for label, _ in warnings)
            )
            for label, value in warnings:
                print(
                    _format_row(
                        label,
                        symbols["warning"],
                        value,
                        indent=2,
                        label_width=section_label_width,
                    )
                )

    # 3b. MCP edit smoke test (informational only)
    if mcp_config_resolved:
        smoke_line = _run_mcp_edit_smoke_test(
            project_dir,
            active_provider,
            mcp_config_resolved,
            str(project_dir),
            symbols,
            env_vars=env_vars,
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
            env_vars=env_vars,
        )
        print(_format_row("Test prompt", symbols["success"], "responded OK", indent=2))
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
        print(
            _format_row(
                "Test prompt",
                symbols["failure"],
                f"FAILED ({category})",
                indent=2,
            )
        )
        logger.debug("Test prompt failure details: %s", exc, exc_info=True)
        print("  Run with --debug for detailed diagnostics.")

    # 4. MLflow verification (now with since= to confirm logging)
    mlflow_result = verify_mlflow(since=timestamp)
    print(_format_section("MLFLOW", mlflow_result, symbols))

    # 5. Collect and display install hints
    all_hints: list[str] = []
    all_hints.extend(_collect_install_hints(github_result))
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
        github_result=github_result,
        git_result=git_result,
    )
    logger.info("Verify command completed with exit code %d", exit_code)
    return exit_code
