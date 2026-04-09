"""iCoder TUI command for the MCP Coder CLI."""

import argparse
import logging
from importlib.metadata import PackageNotFoundError
from pathlib import Path

from ...icoder.env_setup import setup_icoder_environment
from ...llm.storage import extract_session_id, find_latest_session
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

        # Auto-resume: find latest session
        session_file = find_latest_session(provider=provider)
        session_id = extract_session_id(session_file) if session_file else None

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
            )
            app_core = AppCore(llm_service, event_log, runtime_info=runtime_info)
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
