"""iCoder TUI command for the MCP Coder CLI."""

import argparse
import logging
from importlib.metadata import PackageNotFoundError
from pathlib import Path

from ...icoder.env_setup import setup_icoder_environment
from ...llm.storage import (
    extract_langchain_session_id,
    extract_session_id,
    find_latest_session,
)
from ...utils.log_utils import OUTPUT
from ..utils import (
    parse_llm_method_from_args,
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

        # Set up iCoder environment (paths, env vars, MCP verification)
        try:
            runtime_info = setup_icoder_environment(project_dir)
        except (FileNotFoundError, RuntimeError, PackageNotFoundError) as e:
            logger.error("Environment setup failed: %s", e)
            return 1

        env_vars = runtime_info.env_vars

        # Resolve LLM method
        llm_method, _ = resolve_llm_method(getattr(args, "llm_method", None))
        provider = parse_llm_method_from_args(llm_method)

        # Resolve MCP config
        mcp_config = resolve_mcp_config_path(
            args.mcp_config, project_dir=args.project_dir
        )

        # Handle continuation from previous session if requested
        # Priority: --session-id > --continue-session-from > --continue-session
        resume_session_id = getattr(args, "session_id", None)
        continue_file_path = None

        if not resume_session_id:
            if getattr(args, "continue_session_from", None):
                continue_file_path = args.continue_session_from
            elif getattr(args, "continue_session", False):
                continue_file_path = find_latest_session(provider=provider)
                if continue_file_path is None:
                    logger.log(
                        OUTPUT, "No previous session found, starting new conversation"
                    )

            if continue_file_path:
                if provider == "langchain":
                    resume_session_id = extract_langchain_session_id(continue_file_path)
                else:
                    extracted = extract_session_id(continue_file_path)
                    if extracted:
                        resume_session_id = extracted
                if resume_session_id:
                    logger.log(
                        OUTPUT, "Resuming session: %s...", resume_session_id[:16]
                    )
                else:
                    logger.log(
                        OUTPUT,
                        "Warning: No session_id found in stored response, starting new conversation",
                    )
        else:
            if getattr(args, "continue_session_from", None) or getattr(
                args, "continue_session", False
            ):
                logger.log(
                    OUTPUT,
                    "Using explicit session ID (ignoring file-based continuation)",
                )

        session_id = resume_session_id

        # Create registry and load skills
        from ...icoder.core.command_registry import create_default_registry
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
            env_vars=env_vars,
        )

        from ...icoder.core.app_core import AppCore
        from ...icoder.ui.app import ICoderApp

        with EventLog(logs_dir=project_dir / "logs") as event_log:
            event_log.emit(
                "session_start",
                mcp_coder_version=runtime_info.mcp_coder_version,
                tool_env=runtime_info.tool_env_path,
                project_venv=runtime_info.project_venv_path,
                project_dir=runtime_info.project_dir,
                mcp_servers={s.name: s.version for s in runtime_info.mcp_servers},
                mcp_connection_status={
                    s.name: {"ok": s.ok, "status_text": s.status_text}
                    for s in (runtime_info.mcp_connection_status or [])
                },
            )
            app_core = AppCore(
                llm_service, event_log, registry=registry, runtime_info=runtime_info
            )
            ICoderApp(app_core).run()

        return 0

    except KeyboardInterrupt:
        logger.log(OUTPUT, "Operation cancelled by user.")
        return 1

    except (
        Exception
    ) as e:  # pylint: disable=broad-exception-caught  # top-level CLI error boundary
        logger.error(f"Unexpected error in icoder command: {e}", exc_info=True)
        return 1
