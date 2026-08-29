"""Verify command for the MCP Coder CLI.

Orchestrates four domain verification functions (Claude CLI, LangChain,
MLflow, GitHub) and formats their output for the terminal.
"""

import argparse
import datetime
import logging
import os
from pathlib import Path
from typing import Any, cast

from mcp_coder.cli.commands import verify_exit_code

from ...llm.env import prepare_llm_environment
from ...llm.interface import prompt_llm
from ...llm.mlflow_verify import verify_mlflow
from ...llm.providers.claude.claude_cli_verification import verify_claude
from ...llm.providers.claude.claude_executable_finder import find_claude_executable
from ...mcp_workspace_git import verify_git
from ...mcp_workspace_github import verify_github
from ...prompts.prompt_loader import (
    get_project_prompt_path,
    is_claude_md,
    is_prompt_configured_but_missing,
    load_prompts,
)
from ...utils.mcp_verification import ClaudeMCPStatus, parse_claude_mcp_list
from ...utils.user_config import verify_config
from ..utils import (
    find_context_claude_md,
    is_outside_project_dir,
    resolve_claude_settings_path,
    resolve_llm_method,
    resolve_mcp_config_path,
)
from .verify_formatting import (
    _LABEL_WIDTH,
    STATUS_SYMBOLS,
    _format_claude_mcp_section,
    _format_mcp_section,
    _format_row,
    _format_section,
    _format_tools_exposed_section,
    _looks_like_key,
    _pad,
)
from .verify_jenkins import verify_jenkins

# Bound as module globals on purpose: ``execute_verify`` resolves these names
# here, so tests keep patching them at ``mcp_coder.cli.commands.verify.<name>``
# even though they are defined in ``verify_sections``.
from .verify_sections import (
    _PROVIDER_ENV_SOURCE,
    _PROVIDER_ENV_VAR,
    _DropUnexpandedWarnings,
    _print_environment_section,
    _print_langchain_readiness_warning,
    _print_project_section,
    _print_retired_env_var_warning,
    _prompt_source,
    _validate_mcp_config,
)

logger = logging.getLogger(__name__)


def _run_mcp_edit_smoke_test(
    project_dir: Path,
    provider: str,
    mcp_config: str,
    symbols: dict[str, str],
    env_vars: dict[str, str] | None = None,
    settings_file: str | None = None,
) -> str:
    """Run MCP edit smoke test.

    Args:
        project_dir: Path to the project directory.
        provider: The active LLM provider name.
        mcp_config: Path to the MCP config file.
        symbols: Dict with 'success', 'failure', 'warning' keys.
        env_vars: Environment variables passed to the LLM subprocess so
            ``${MCP_CODER_*}`` placeholders in ``.mcp.json`` resolve.
        settings_file: Optional path to .claude/settings.local.json; forwarded to prompt_llm.

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
            settings_file=settings_file,
            project_dir=project_dir,
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

    # 0a. Retired env vars — unconditional (outside both provider gates), since
    # a retired variable is ignored whatever the active provider is.
    _print_retired_env_var_warning(symbols)

    # 0b. Prompt configuration section
    project_dir = Path(args.project_dir).resolve() if args.project_dir else Path.cwd()
    sys_prompt, proj_prompt, prompt_config = load_prompts(project_dir)
    active_provider, source = resolve_llm_method(args.llm_method)

    prompt_lines = [_pad("PROMPTS")]
    # Lengths come from the content load_prompts already resolved — no re-read.
    # A configured path that did not resolve is an error, not an [OK] row
    # showing a path the run never actually used.
    prompts_ok = True
    for label, configured, content in (
        ("System prompt", prompt_config.system_prompt, sys_prompt),
        ("Project prompt", prompt_config.project_prompt, proj_prompt),
    ):
        if is_prompt_configured_but_missing(configured, project_dir):
            prompts_ok = False
            marker, value = symbols["failure"], (
                f"{configured} — configured but not found; "
                "shipped default used instead"
            )
        else:
            source_label = _prompt_source(configured, "shipped default")
            marker, value = symbols["success"], f"{source_label} ({len(content)} chars)"
        prompt_lines.append(_format_row(label, marker, value, indent=2))
    mode = prompt_config.claude_system_prompt_mode
    prompt_lines.append(_format_row("Claude mode", symbols["success"], mode, indent=2))
    # Reporting only - the rows below must never feed verify_exit_code.
    # Walk from project_dir: that is where verify runs Claude, at both of its
    # LLM call sites.
    prompt_lines.append(
        _format_row("Claude cwd", symbols["success"], str(project_dir), indent=2)
    )
    context_hits = find_context_claude_md(project_dir)
    if not context_hits:
        # A project may legitimately have none - state the fact, do not warn.
        prompt_lines.append(
            _format_row(
                "Project instructions", symbols["success"], "none found", indent=2
            )
        )
    else:
        # Per-row annotation, not a verdict: an ancestor file is outside
        # project_dir by definition. The run-time report warns only when no
        # file at all lies inside it.
        for index, hit in enumerate(context_hits):
            outside = is_outside_project_dir(hit, project_dir)
            prompt_lines.append(
                _format_row(
                    # Continuation rows carry an empty label; _format_row pads
                    # it so the value column stays aligned.
                    "Project instructions" if index == 0 else "",
                    symbols["warning"] if outside else symbols["success"],
                    f"{hit} (outside project directory)" if outside else str(hit),
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

    # 0f. Jenkins verification sections (both empty when [jenkins] is unset)
    jenkins_result, jenkins_jobs_result = verify_jenkins()
    if jenkins_result:
        print(_format_section("JENKINS", jenkins_result, symbols))
    if jenkins_jobs_result:
        print(_format_section("JENKINS JOBS", jenkins_jobs_result, symbols))
    # None keeps an unconfigured [jenkins] exit-neutral; CONFIG already reports
    # a missing required field.
    jenkins_ok: bool | None = None
    if jenkins_result:
        jenkins_ok = bool(jenkins_result.get("overall_ok")) and bool(
            jenkins_jobs_result.get("overall_ok", True)
        )

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
    # The env var no longer silently wins over --llm-method, so an exported but
    # overridden value would otherwise leave no trace at all. When it IS the
    # source the row above already says so — add nothing. Exit-neutral.
    env_provider = os.environ.get(_PROVIDER_ENV_VAR)
    if env_provider and source != _PROVIDER_ENV_SOURCE:
        print(
            _format_row(
                _PROVIDER_ENV_VAR,
                symbols["warning"],
                f"set to '{env_provider}' but overridden by {source} "
                f"— using '{active_provider}'",
                indent=2,
                label_width=max(_LABEL_WIDTH, len(_PROVIDER_ENV_VAR)),
            )
        )
    # 2a. Resolve MCP config for ALL providers (before provider branch)
    mcp_config_resolved = resolve_mcp_config_path(
        args.mcp_config, project_dir=args.project_dir
    )
    settings_file = resolve_claude_settings_path(
        args.settings, project_dir=args.project_dir
    )

    if active_provider == "langchain":
        check_models = getattr(args, "check_models", False)
        from ...llm.providers.langchain.verification import verify_langchain

        langchain_result = verify_langchain(
            check_models=check_models,
            mcp_config_path=mcp_config_resolved,
        )
        # Printing only: the rows are already built and their sources already
        # resolved, so this layer needs no access to the private llm helpers.
        # The empty marker is what renders the block without status symbols.
        effective_config = langchain_result.get("effective_config")
        if effective_config:
            print(_pad("EFFECTIVE CONFIG"))
            for label, value in effective_config:
                print(_format_row(label, "", value, indent=2))
        print(_format_section("LLM PROVIDER DETAILS", langchain_result, symbols))
    else:
        print("  (uses Claude CLI — see Basic Verification above)")
        _print_langchain_readiness_warning(symbols)

    # 3a. MCP server health checks (provider-aware ordering)
    mcp_result: dict[str, Any] | None = None
    claude_mcp: list[ClaudeMCPStatus] | None = None
    # Compute MCP_CODER_* env vars once: needed by the Claude/LangChain MCP
    # health checks AND by the smoke test / test prompt below so .mcp.json
    # placeholders like ${MCP_CODER_VENV_PATH} resolve in the subprocess.
    env_vars = prepare_llm_environment(project_dir)

    # 2b. Validate .mcp.json itself (single parse; reused by 3a-bis warnings).
    # The validity row prints FIRST as the earliest, clearest upstream signal.
    # A hard-fail (mcp_config_ok is False) short-circuits the downstream MCP
    # health/smoke/prompt checks below so they don't emit confusing indirect
    # errors on top of a malformed config.
    mcp_config_ok: bool | None = None
    mcp_warnings: list[tuple[str, str]] = []
    if mcp_config_resolved:
        _ok, _msg, mcp_warnings = _validate_mcp_config(mcp_config_resolved)
        marker = {
            True: symbols["success"],
            None: symbols["warning"],
            False: symbols["failure"],
        }[_ok]
        print(_pad("MCP CONFIG"))
        print(_format_row(".mcp.json", marker, _msg, indent=2))
        mcp_config_ok = _ok is not False

    if mcp_config_resolved and mcp_config_ok is not False:
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
        warnings = mcp_warnings
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
    if mcp_config_resolved and mcp_config_ok is not False:
        smoke_line = _run_mcp_edit_smoke_test(
            project_dir,
            active_provider,
            mcp_config_resolved,
            symbols,
            env_vars=env_vars,
            settings_file=settings_file,
        )
        print(smoke_line)

    # 3c. Unified test prompt (both providers)
    # Skipped on a malformed .mcp.json (mcp_config_ok is False): the MCP CONFIG
    # validity row above is the single upstream diagnostic, so the prompt (which
    # would fail indirectly) is short-circuited.
    # inject_prompts=True is what makes prompt_llm load the prompts, so the request
    # carries the same merged system + project prompt a real run sends.
    timestamp = datetime.datetime.now(datetime.timezone.utc)
    test_prompt_ok = True
    tools_exposed_ok: bool | None = None
    if mcp_config_ok is not False:
        try:
            response = prompt_llm(
                "Reply with OK",
                provider=active_provider,
                timeout=30,
                mcp_config=mcp_config_resolved,
                settings_file=settings_file,
                env_vars=env_vars,
                project_dir=str(project_dir),
                inject_prompts=True,
            )
            print(
                _format_row("Test prompt", symbols["success"], "responded OK", indent=2)
            )
            if active_provider == "claude":
                raw_response = cast(dict[str, Any], response.get("raw_response", {}))
                system_message = raw_response.get("system")
                tools_lines, tools_exposed_ok = _format_tools_exposed_section(
                    system_message, symbols
                )
                print("\n".join(tools_lines))
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
    all_hints.extend(verify_exit_code._collect_install_hints(github_result))
    if langchain_result:
        all_hints.extend(verify_exit_code._collect_install_hints(langchain_result))
    if active_provider == "claude":
        all_hints.extend(verify_exit_code._collect_install_hints(claude_result))

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
    exit_code = verify_exit_code._compute_exit_code(
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
        tools_exposed_ok=tools_exposed_ok,
        mcp_config_ok=mcp_config_ok,
        jenkins_ok=jenkins_ok,
        prompts_ok=prompts_ok,
    )
    logger.info("Verify command completed with exit code %d", exit_code)
    return exit_code
