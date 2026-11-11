"""Verify command for the MCP Coder CLI.

Orchestrates four domain verification functions (Claude CLI, LangChain,
MLflow, GitHub) and formats their output for the terminal.
"""

import argparse
import contextlib
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
from ...mcp_workspace import is_path_gitignored
from ...mcp_workspace_git import verify_git
from ...mcp_workspace_github import verify_github
from ...prompts.prompt_loader import (
    get_project_prompt_path,
    is_claude_md,
    is_prompt_configured_but_missing,
    load_prompts,
)
from ...utils.mcp_verification import ClaudeMCPStatus, parse_claude_mcp_list
from ...utils.text_io import write_lf_text
from ...utils.user_config import verify_config
from ..utils import (
    find_context_claude_md,
    is_outside_project_dir,
    resolve_claude_settings_path,
    resolve_llm_method,
    resolve_mcp_config_path,
)
from .verify_formatting import (
    STATUS_SYMBOLS,
    Line,
    Row,
    _format_claude_mcp_section,
    _format_mcp_section,
    _format_section,
    _format_tools_exposed_section,
    _looks_like_key,
)
from .verify_jenkins import verify_jenkins
from .verify_render import SectionBuilder

# Bound as module globals on purpose: ``execute_verify`` resolves these names
# here, so tests keep patching them at ``mcp_coder.cli.commands.verify.<name>``
# even though they are defined in ``verify_sections``.
from .verify_sections import (
    _PROVIDER_ENV_SOURCE,
    _PROVIDER_ENV_VAR,
    _DropUnexpandedWarnings,
    _print_environment_section,
    _print_github_security_section,
    _print_langchain_readiness_warning,
    _print_project_section,
    _print_retired_env_var_warning,
    _prompt_source,
    _validate_mcp_config,
)

logger = logging.getLogger(__name__)

# POSIX spelling on all platforms: used in the LLM prompt and the gitignore check
_SMOKE_TEST_FILE = ".scratch/mcp_coder_verify.md"


def _run_mcp_edit_smoke_test(
    project_dir: Path,
    provider: str,
    mcp_config: str,
    symbols: dict[str, str],
    env_vars: dict[str, str] | None = None,
    settings_file: str | None = None,
) -> Row:
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
        The smoke-test row.
    """
    label = "MCP edit smoke test"
    scratch_dir = project_dir / ".scratch"
    test_file = project_dir / _SMOKE_TEST_FILE
    created_scratch = not scratch_dir.exists()
    try:
        # mcp-workspace refuses gitignored paths, so the edit could never succeed
        if is_path_gitignored(_SMOKE_TEST_FILE, project_dir):
            return Row(
                label,
                symbols["warning"],
                f"skipped: {_SMOKE_TEST_FILE} is gitignored",
            )
        scratch_dir.mkdir(exist_ok=True)
        write_lf_text(test_file, "A\n\nC\n")
        prompt_llm(
            f"Edit the file {_SMOKE_TEST_FILE} to insert a line 'B' between 'A' and 'C'",
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
            return Row(label, symbols["success"], "edit verified")
        return Row(
            label,
            symbols["warning"],
            "edit not verified (B not found between A and C)",
        )
    except Exception as exc:  # pylint: disable=broad-except
        return Row(label, symbols["warning"], f"edit not verified ({exc})")
    finally:
        test_file.unlink(missing_ok=True)
        if created_scratch:
            # rmdir fails on a non-empty directory, which keeps other files
            with contextlib.suppress(OSError):
                scratch_dir.rmdir()


def execute_verify(args: argparse.Namespace) -> int:
    """Execute verify command: orchestrate domain checks and format output.

    Args:
        args: Command line arguments (expects args.check_models: bool)

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    with SectionBuilder() as out:
        return _run_verify(args, out)


def _run_verify(args: argparse.Namespace, out: SectionBuilder) -> int:
    """Body of execute_verify; writes sections through *out*.

    Args:
        args: Command line arguments, as for ``execute_verify``.
        out: Builder every migrated section is written through.

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    logger.info("Executing verify command")
    symbols = STATUS_SYMBOLS
    _print_environment_section(out)

    # 0. Config verification (first section) with TOML-style grouping
    config_result = verify_config()
    out.open("CONFIG")
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
                    out.add("")  # blank line between groups
                out.add(f"  {label}")
                last_label = label
            first, _sep, rest = value.partition(" ")
            if _looks_like_key(first) and rest:
                out.add(Row(first, symbol, rest, 4))
            elif symbol.strip():
                out.add(Row("", symbol, value, 4))
            else:
                out.add(Row("", "", value, 4))
        else:
            # Top-level rows (Config file, Expected path, Hint, Parse error)
            out.add(Row(label, symbol, value))

    # 0a. Retired env vars — unconditional (outside both provider gates), since
    # a retired variable is ignored whatever the active provider is.
    _print_retired_env_var_warning(symbols, out)
    out.close()

    # 0b. Prompt configuration section
    project_dir = Path(args.project_dir).resolve() if args.project_dir else Path.cwd()
    sys_prompt, proj_prompt, prompt_config = load_prompts(project_dir)
    active_provider, source = resolve_llm_method(args.llm_method)

    prompt_lines: list[Line] = []
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
            marker, value = (
                symbols["failure"],
                (
                    f"{configured} — configured but not found; "
                    "shipped default used instead"
                ),
            )
        else:
            source_label = _prompt_source(configured, "shipped default")
            marker, value = symbols["success"], f"{source_label} ({len(content)} chars)"
        prompt_lines.append(Row(label, marker, value))
    mode = prompt_config.claude_system_prompt_mode
    prompt_lines.append(Row("Claude mode", symbols["success"], mode))
    # Reporting only - the rows below must never feed verify_exit_code.
    # Walk from project_dir: that is where verify runs Claude, at both of its
    # LLM call sites.
    prompt_lines.append(Row("Claude cwd", symbols["success"], str(project_dir)))
    context_hits = find_context_claude_md(project_dir)
    if not context_hits:
        # A project may legitimately have none - state the fact, do not warn.
        prompt_lines.append(
            Row("Project instructions", symbols["success"], "none found")
        )
    else:
        # Per-row annotation, not a verdict: an ancestor file is outside
        # project_dir by definition. The run-time report warns only when no
        # file at all lies inside it.
        for index, hit in enumerate(context_hits):
            outside = is_outside_project_dir(hit, project_dir)
            prompt_lines.append(
                Row(
                    # Continuation rows carry an empty label; the renderer pads
                    # it so the value column stays aligned.
                    "Project instructions" if index == 0 else "",
                    symbols["warning"] if outside else symbols["success"],
                    f"{hit} (outside project directory)" if outside else str(hit),
                )
            )
    if active_provider == "claude" and prompt_config.project_prompt:
        prompt_path = get_project_prompt_path(project_dir)
        if is_claude_md(prompt_path, str(project_dir)):
            prompt_lines.append(
                Row(
                    "Redundancy",
                    symbols["warning"],
                    "project prompt is CLAUDE.md (will skip for Claude)",
                )
            )
    out.section("PROMPTS", prompt_lines)

    # 0c. Project configuration section
    project_ok = _print_project_section(project_dir, symbols, out)

    # 0d. Git verification section
    git_result = verify_git(project_dir, actually_sign=True)
    out.section("GIT", _format_section(git_result, symbols))

    # 0e. GitHub verification section
    github_result = verify_github(project_dir)
    out.section("GITHUB", _format_section(github_result, symbols))
    _print_github_security_section(project_dir, symbols, out)

    # 0f. Jenkins verification sections (both empty when [jenkins] is unset)
    jenkins_result, jenkins_jobs_result = verify_jenkins()
    if jenkins_result:
        out.section("JENKINS", _format_section(jenkins_result, symbols))
    if jenkins_jobs_result:
        out.section("JENKINS JOBS", _format_section(jenkins_jobs_result, symbols))
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
        out.section("BASIC VERIFICATION", _format_section(claude_result, symbols))
    else:
        # Quick binary check only
        claude_path = find_claude_executable(return_none_if_not_found=True)
        if claude_path:
            out.add(f"\n  Claude CLI: available at {claude_path} (not active)")
        claude_result = {"overall_ok": True}  # neutral for exit code

    # 3. LangChain verification (only when provider is langchain)
    langchain_result: dict[str, Any] | None = None
    out.open("LLM PROVIDER")
    out.add(
        Row("Active provider", symbols["success"], f"{active_provider} (from {source})")
    )
    # The env var no longer silently wins over --llm-method, so an exported but
    # overridden value would otherwise leave no trace at all. When it IS the
    # source the row above already says so — add nothing. Exit-neutral.
    env_provider = os.environ.get(_PROVIDER_ENV_VAR)
    if env_provider and source != _PROVIDER_ENV_SOURCE:
        out.add(
            Row(
                _PROVIDER_ENV_VAR,
                symbols["warning"],
                f"set to '{env_provider}' but overridden by {source} "
                f"— using '{active_provider}'",
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
        # Close before the slow verify_langchain call so the section streams.
        out.close()
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
            out.section(
                "EFFECTIVE CONFIG",
                [Row(label, "", value) for label, value in effective_config],
            )
        out.section("LLM PROVIDER DETAILS", _format_section(langchain_result, symbols))
    else:
        out.add("  (uses Claude CLI — see Basic Verification above)")
        _print_langchain_readiness_warning(symbols, out)
        out.close()

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
        _ok, _msg, mcp_warnings = _validate_mcp_config(
            mcp_config_resolved, env_vars=env_vars
        )
        marker = {
            True: symbols["success"],
            None: symbols["warning"],
            False: symbols["failure"],
        }[_ok]
        out.section("MCP CONFIG", [Row(".mcp.json", marker, _msg)])
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
                out.section(
                    *_format_claude_mcp_section(
                        claude_mcp, symbols, for_completeness=False
                    )
                )
            # LangChain MCP section second (for completeness)
            if mcp_result is not None:
                out.section(
                    *_format_mcp_section(
                        mcp_result,
                        symbols,
                        list_mcp_tools=list_mcp_tools,
                        for_completeness=lc_for_completeness,
                    )
                )
            else:
                out.section(
                    "MCP SERVERS (via langchain-mcp-adapters)",
                    [
                        Row(
                            "",
                            symbols["warning"],
                            "server health check skipped"
                            " (langchain-mcp-adapters not installed)",
                        )
                    ],
                )
        else:
            # LangChain MCP section first (primary)
            if mcp_result is not None:
                out.section(
                    *_format_mcp_section(
                        mcp_result,
                        symbols,
                        list_mcp_tools=list_mcp_tools,
                        for_completeness=False,
                    )
                )
            else:
                out.section(
                    "MCP SERVERS (via langchain-mcp-adapters)",
                    [
                        Row(
                            "",
                            symbols["warning"],
                            "server health check skipped"
                            " (langchain-mcp-adapters not installed)",
                        )
                    ],
                )
            # Claude MCP section second (for completeness)
            if claude_mcp is not None:
                out.section(
                    *_format_claude_mcp_section(
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
            out.section(
                "MCP CONFIG WARNINGS",
                [Row(label, symbols["warning"], value) for label, value in warnings],
            )

    # LLM TEST holds the smoke test and the test prompt; it opens before either
    # runs so its header streams while they execute.
    if mcp_config_ok is not False:
        out.open("LLM TEST")

    # 3b. MCP edit smoke test (informational only)
    if mcp_config_resolved and mcp_config_ok is not False:
        out.add(
            _run_mcp_edit_smoke_test(
                project_dir,
                active_provider,
                mcp_config_resolved,
                symbols,
                env_vars=env_vars,
                settings_file=settings_file,
            )
        )

    # 3c. Unified test prompt (both providers)
    # Skipped on a malformed .mcp.json (mcp_config_ok is False): the MCP CONFIG
    # validity row above is the single upstream diagnostic, so the prompt (which
    # would fail indirectly) is short-circuited.
    # inject_prompts=True is what makes prompt_llm load the prompts, so the request
    # carries the same merged system + project prompt a real run sends.
    timestamp = datetime.datetime.now(datetime.UTC)
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
            out.add(Row("Test prompt", symbols["success"], "responded OK"))
            if active_provider == "claude":
                raw_response = cast(dict[str, Any], response.get("raw_response", {}))
                system_message = raw_response.get("system")
                tools_rows, tools_exposed_ok = _format_tools_exposed_section(
                    system_message, symbols
                )
                out.add(*tools_rows)
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
            out.add(Row("Test prompt", symbols["failure"], f"FAILED ({category})"))
            logger.debug("Test prompt failure details: %s", exc, exc_info=True)
            out.add("  Run with --debug for detailed diagnostics.")
    out.close()

    # 4. MLflow verification (now with since= to confirm logging)
    mlflow_result = verify_mlflow(since=timestamp)
    out.section("MLFLOW", _format_section(mlflow_result, symbols))

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
            out.section("INSTALL INSTRUCTIONS", [f"  pip install {pip_packages}"])

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
        project_ok=project_ok,
    )
    logger.info("Verify command completed with exit code %d", exit_code)
    return exit_code
