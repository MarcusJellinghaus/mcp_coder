"""iCoder TUI command for the MCP Coder CLI."""

import argparse
import logging
from importlib.metadata import PackageNotFoundError
from pathlib import Path

from ...icoder.core.event_log import emit_session_start, read_session_id_from_log
from ...icoder.core.log_inventory import list_icoder_logs
from ...icoder.env_setup import setup_icoder_environment
from ...icoder.ui.widgets.session_picker import run_startup_picker
from ...llm.providers.langchain.agent import (  # noqa: PLC2701
    _load_mcp_server_config,
)
from ...llm.providers.langchain.mcp_manager import MCPManager
from ...utils.log_utils import OUTPUT
from ...utils.tui_preparation import TuiChecker, TuiPreflightAbort
from ..utils import (
    parse_llm_method_from_args,
    resolve_claude_settings_path,
    resolve_execution_dir,
    resolve_llm_method,
    resolve_mcp_config_path,
)

logger = logging.getLogger(__name__)


def execute_icoder(args: argparse.Namespace) -> int:
    """Execute the iCoder interactive TUI.

    Resolves CLI parameters, creates core components, launches Textual app.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    logger.log(OUTPUT, "Starting iCoder...")
    try:
        # Resolve execution directory
        try:
            execution_dir = resolve_execution_dir(getattr(args, "execution_dir", None))
        except ValueError as e:
            logger.error(f"Invalid execution directory: {e}")
            return 1

        # Resolve project directory
        project_dir_arg = getattr(args, "project_dir", None)
        if project_dir_arg:
            project_dir = Path(project_dir_arg).resolve()
            if not project_dir.exists():
                logger.error("Project directory does not exist: %s", project_dir)
                return 1
            if not project_dir.is_dir():
                logger.error("Project path is not a directory: %s", project_dir)
                return 1
        else:
            project_dir = Path.cwd()

        # Pre-flight terminal checks (fail fast before slow env setup)
        TuiChecker().run_all_checks()

        # Resolve LLM method + MCP config before env setup so the startup
        # probe can report the tools actually exposed to the model.
        llm_method, _ = resolve_llm_method(getattr(args, "llm_method", None))
        provider = parse_llm_method_from_args(llm_method)

        mcp_config = resolve_mcp_config_path(
            args.mcp_config, project_dir=args.project_dir
        )
        settings_file = resolve_claude_settings_path(
            args.settings, project_dir=args.project_dir
        )

        # Set up iCoder environment (paths, env vars, MCP verification)
        try:
            runtime_info = setup_icoder_environment(
                project_dir, provider=provider, mcp_config=mcp_config
            )
        except (FileNotFoundError, RuntimeError, PackageNotFoundError) as e:
            logger.error("Environment setup failed: %s", e)
            return 1

        env_vars = runtime_info.env_vars

        # Create MCPManager for persistent MCP connections (langchain only)
        mcp_manager: MCPManager | None = None
        if provider == "langchain" and mcp_config:
            server_config = _load_mcp_server_config(mcp_config, env_vars)
            mcp_manager = MCPManager(server_config)

        # Resume resolution.
        # The three flags (--session-id / --continue-session-from /
        # --continue-session) are mutually exclusive at the argparse layer,
        # so at most one branch fires here. --session-id is consumed
        # directly via ``resume_session_id`` below; the other two flags
        # need to resolve to a log path first.
        resume_session_id = getattr(args, "session_id", None)
        resume_log_path: Path | None = None

        if getattr(args, "continue_session_from", None):
            fp = Path(args.continue_session_from)
            if fp.suffix.lower() == ".json":
                logger.error(
                    "--continue-session-from now expects a .jsonl event-log "
                    "path, not a response JSON. Refusing to resume."
                )
                return 1
            if fp.suffix.lower() != ".jsonl" or not fp.exists():
                logger.error("Log file not found or not a .jsonl: %s", fp)
                return 1
            resume_log_path = fp
        elif getattr(args, "continue_session", False):
            summaries = list_icoder_logs(project_dir / "logs", provider=provider)
            if not summaries:
                logger.log(OUTPUT, "No previous sessions in this project.")
            else:
                chosen = run_startup_picker(summaries)
                if chosen is not None:
                    resume_log_path = chosen
                # else: Esc → fresh session

        if resume_log_path is not None:
            resume_session_id = read_session_id_from_log(resume_log_path)
            if resume_session_id:
                logger.log(OUTPUT, "Resuming session: %s...", resume_session_id[:16])

        session_id = resume_session_id

        # Create registry and load skills
        from ...icoder.core.command_registry import create_default_registry
        from ...icoder.core.commands.color import register_color
        from ...icoder.core.commands.display import register_display
        from ...icoder.core.commands.info import register_info
        from ...icoder.skills import load_skills, register_skill_commands

        registry = create_default_registry()
        skills = load_skills(project_dir)
        register_skill_commands(registry, skills, provider)

        # Create core components
        from ...icoder.core.event_log import EventLog
        from ...icoder.services.llm_service import RealLLMService

        llm_service = RealLLMService(
            provider=provider,
            session_id=session_id,
            execution_dir=str(execution_dir),
            mcp_config=mcp_config,
            settings_file=settings_file,
            env_vars=env_vars,
            timeout=args.timeout,
            mcp_manager=mcp_manager,
            project_dir=str(project_dir),
            enforce_skill_tools=False,
        )

        from ...icoder.core.app_core import AppCore
        from ...icoder.ui.app import ICoderApp

        try:
            with EventLog(logs_dir=project_dir / "logs") as event_log:
                emit_session_start(
                    event_log,
                    provider=provider,
                    runtime_info=runtime_info,
                    session_id=session_id,
                )
                app_core = AppCore(
                    llm_service,
                    event_log,
                    registry=registry,
                    runtime_info=runtime_info,
                    tool_display=getattr(args, "tool_display", "compressed"),
                )
                initial_color = getattr(args, "initial_color", None)
                if initial_color:
                    error = app_core.set_prompt_color(initial_color)
                    if error:
                        logger.warning(
                            "Invalid --initial-color '%s': %s",
                            initial_color,
                            error,
                        )
                register_info(
                    registry, runtime_info, event_log, mcp_manager=mcp_manager
                )
                register_color(registry, app_core)
                register_display(registry, app_core)
                format_tools = not getattr(args, "no_format_tools", False)
                ICoderApp(
                    app_core,
                    format_tools=format_tools,
                    resume_log_path=resume_log_path,
                ).run()
        finally:
            if mcp_manager is not None:
                mcp_manager.close()

        return 0

    except TuiPreflightAbort as e:
        logger.log(OUTPUT, e.message)
        return e.exit_code

    except KeyboardInterrupt:
        logger.log(OUTPUT, "Operation cancelled by user.")
        return 1

    except (
        Exception
    ) as e:  # pylint: disable=broad-exception-caught  # top-level CLI error boundary
        logger.error(f"Unexpected error in icoder command: {e}", exc_info=True)
        return 1
