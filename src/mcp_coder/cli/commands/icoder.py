"""iCoder TUI command for the MCP Coder CLI."""

import argparse
import logging
import sys
from pathlib import Path

from ...llm.env import prepare_llm_environment
from ...llm.storage import extract_session_id, find_latest_session
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
            print(f"Error: {e}", file=sys.stderr)
            return 1

        # Resolve project directory
        project_dir_arg = getattr(args, "project_dir", None)
        if project_dir_arg:
            project_dir = Path(project_dir_arg).resolve()
            if not project_dir.exists():
                print(
                    f"Error: Project directory does not exist: {project_dir}",
                    file=sys.stderr,
                )
                return 1
            if not project_dir.is_dir():
                print(
                    f"Error: Project path is not a directory: {project_dir}",
                    file=sys.stderr,
                )
                return 1
        else:
            project_dir = Path.cwd()

        # Prepare environment variables for LLM subprocess
        try:
            env_vars = prepare_llm_environment(project_dir)
        except RuntimeError as e:
            logger.warning(f"Could not prepare environment: {e}")
            env_vars = None

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
            app_core = AppCore(llm_service, event_log)
            ICoderApp(app_core).run()

        return 0

    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        return 1

    except (
        Exception
    ) as e:  # pylint: disable=broad-exception-caught  # top-level CLI error boundary
        logger.error(f"Unexpected error in icoder command: {e}", exc_info=True)
        print(f"Error: {e}", file=sys.stderr)
        return 1
