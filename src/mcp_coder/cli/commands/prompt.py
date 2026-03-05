"""Prompt command for the MCP Coder CLI."""

import argparse
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from ...llm.env import prepare_llm_environment
from ...llm.formatting.formatters import (
    format_raw_response,
    format_text_response,
    format_verbose_response,
)
from ...llm.interface import prompt_llm
from ...llm.mlflow_logger import get_mlflow_logger
from ...llm.storage import extract_session_id, find_latest_session, store_session
from ...llm.types import LLMResponseDict
from ...utils.git_utils import get_branch_name_for_logging
from ..utils import (
    parse_llm_method_from_args,
    resolve_execution_dir,
    resolve_mcp_config_path,
)

logger = logging.getLogger(__name__)


def _log_to_mlflow(
    response_data: LLMResponseDict,
    prompt: str,
    project_dir: Path,
    branch_name: Optional[str] = None,
    step_name: Optional[str] = None,
) -> None:
    """Log conversation to MLflow if enabled.

    Args:
        response_data: Response dictionary from prompt_llm()
        prompt: Original user prompt
        project_dir: Project directory path
        branch_name: Optional branch name
        step_name: Optional step name
    """
    mlflow_logger = None
    try:
        mlflow_logger = get_mlflow_logger()
        # Skip if MLflow is not enabled or unavailable
        if not mlflow_logger.config.enabled:
            return

        # Extract model from response data
        raw_response = response_data.get("raw_response", {})
        session_info = raw_response.get("session_info")
        model = (
            session_info.get("model") if isinstance(session_info, dict) else None
        ) or response_data.get("provider", "unknown")

        # Build metadata
        metadata: Dict[str, Any] = {
            "timestamp": datetime.now().isoformat() + "Z",
            "working_directory": str(project_dir),
            "model": model,
        }
        if branch_name is not None:
            metadata["branch_name"] = branch_name
        if step_name is not None:
            metadata["step_name"] = step_name

        # Convert LLMResponseDict to Dict[str, Any] for MLflow compatibility
        response_dict: Dict[str, Any] = dict(response_data)
        response_sid = response_data.get("session_id")

        if response_sid and mlflow_logger.has_session(response_sid):
            # Resume closed run; metrics are already logged by log_llm_response()
            mlflow_logger.start_run(session_id=response_sid)
            mlflow_logger.log_conversation_artifacts(prompt, response_dict, metadata)
            mlflow_logger.end_run("FINISHED", session_id=response_sid)
        elif mlflow_logger.active_run_id is not None:
            # Run still open: session_id was None so log_llm_response left it open.
            # Metrics already logged — just add params + artifacts and close.
            mlflow_logger.log_conversation_artifacts(prompt, response_dict, metadata)
            mlflow_logger.end_run("FINISHED")
        else:
            # Fallback: no active run and no known session mapping.
            mlflow_logger.start_run()
            mlflow_logger.log_conversation(prompt, response_dict, metadata)
            mlflow_logger.end_run("FINISHED")

        logger.debug("Logged conversation to MLflow")
    except Exception as e:
        logger.debug(f"Failed to log conversation to MLflow: {e}")
        # Attempt to end run even if logging failed
        try:
            if mlflow_logger is not None:
                mlflow_logger.end_run("FAILED")
        except Exception:
            # Silent failure OK - MLflow is optional and should never break main workflow
            pass


def execute_prompt(
    args: argparse.Namespace,
) -> int:  # pylint: disable=too-many-statements
    """Execute prompt command to ask Claude a question.

    Args:
        args: Command line arguments with prompt attribute and optional verbosity

    Returns:
        Exit code (0 for success, 1 for error)
    """
    logger.info("Executing prompt command")

    try:
        # Extract and validate execution_dir
        try:
            execution_dir = resolve_execution_dir(getattr(args, "execution_dir", None))
            logger.debug(f"Execution directory: {execution_dir}")
        except ValueError as e:
            logger.error(f"Invalid execution directory: {e}")
            print(f"Error: {e}", file=sys.stderr)
            return 1
        # Prepare environment variables for LLM subprocess
        try:
            # Get project directory from args or use current directory
            project_dir_arg = getattr(args, "project_dir", None)
            if project_dir_arg:
                project_dir = Path(project_dir_arg).resolve()
                # Validate it exists and is accessible (no git requirement)
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

            env_vars = prepare_llm_environment(project_dir)
        except RuntimeError as e:
            # No venv found - continue without env vars for backward compat
            logger.warning(f"Could not prepare environment: {e}")
            env_vars = None

        # Handle continuation from previous session if requested
        # Priority: --session-id > --continue-session-from > --continue-session
        resume_session_id = getattr(args, "session_id", None)
        continue_file_path = None

        # Only check file-based continuation if --session-id not provided
        if not resume_session_id:
            if getattr(args, "continue_session_from", None):
                continue_file_path = args.continue_session_from
            elif getattr(args, "continue_session", False):
                # Find latest session file
                continue_file_path = find_latest_session()
                if continue_file_path is None:
                    print("No previous response files found, starting new conversation")
                    # Continue execution without session resumption

            if continue_file_path:
                # Extract session_id from the stored response file
                extracted_session_id = extract_session_id(continue_file_path)
                if extracted_session_id:
                    resume_session_id = extracted_session_id
                    print(f"Resuming session: {resume_session_id[:16]}...")
                else:
                    print(
                        "Warning: No session_id found in stored response, starting new conversation"
                    )
        else:
            # User provided explicit --session-id, inform them it takes priority
            if getattr(args, "continue_session_from", None) or getattr(
                args, "continue_session", False
            ):
                print("Using explicit session ID (ignoring file-based continuation)")

        # Get user-specified timeout, llm_method, output_format, and mcp_config
        timeout = getattr(args, "timeout", 30)
        llm_method = getattr(args, "llm_method", "claude_code_api")
        verbosity = getattr(args, "verbosity", "just-text")
        output_format = getattr(args, "output_format", "text")
        mcp_config = getattr(args, "mcp_config", None)
        mcp_config = resolve_mcp_config_path(mcp_config)

        # Route to appropriate method based on output_format and verbosity
        formatted_output = ""
        if output_format == "session-id":
            # Session ID only mode - return only the session_id for shell script capture
            provider, method = parse_llm_method_from_args(llm_method)
            response_dict = prompt_llm(
                args.prompt,
                provider=provider,
                method=method,
                timeout=timeout,
                session_id=resume_session_id,
                env_vars=env_vars,
                execution_dir=str(execution_dir),
                mcp_config=mcp_config,
            )

            session_id = response_dict.get("session_id", "")
            if not session_id:
                print("Error: No session_id in response", file=sys.stderr)
                return 1

            # Log to MLflow (even in session-id mode)
            _log_to_mlflow(response_dict, args.prompt, project_dir)

            print(session_id)
            return 0

        elif output_format == "json":
            # JSON output mode - return full LLMResponseDict
            provider, method = parse_llm_method_from_args(llm_method)
            branch_name = get_branch_name_for_logging(project_dir)
            response_dict = prompt_llm(
                args.prompt,
                provider=provider,
                method=method,
                timeout=timeout,
                session_id=resume_session_id,
                env_vars=env_vars,
                execution_dir=str(execution_dir),
                mcp_config=mcp_config,
                branch_name=branch_name,
            )
            # Output complete response as JSON (includes session_id)
            formatted_output = json.dumps(response_dict, indent=2, default=str)

            # Always log to MLflow if enabled
            _log_to_mlflow(response_dict, args.prompt, project_dir, branch_name)

            # Store response to file if requested
            if getattr(args, "store_response", False):
                stored_path = store_session(
                    response_dict, args.prompt, branch_name=branch_name
                )
                logger.info("Response stored to: %s", stored_path)
        elif verbosity == "just-text":
            # Use unified prompt_llm interface for simple text output
            provider, method = parse_llm_method_from_args(llm_method)
            branch_name = get_branch_name_for_logging(project_dir)
            llm_response = prompt_llm(
                args.prompt,
                provider=provider,
                method=method,
                timeout=timeout,
                session_id=resume_session_id,
                env_vars=env_vars,
                execution_dir=str(execution_dir),
                mcp_config=mcp_config,
                branch_name=branch_name,
            )

            # Simple text output with tool summary
            formatted_output = llm_response["text"].strip()

            # Always log to MLflow if enabled
            _log_to_mlflow(llm_response, args.prompt, project_dir, branch_name)

            # Store response to file if requested
            if getattr(args, "store_response", False):
                stored_path = store_session(
                    llm_response, args.prompt, branch_name=branch_name
                )
                logger.info("Response stored to: %s", stored_path)
        else:
            # Use prompt_llm for verbose/raw modes that need metadata
            provider, method = parse_llm_method_from_args(llm_method)
            branch_name = get_branch_name_for_logging(project_dir)
            llm_response = prompt_llm(
                args.prompt,
                provider=provider,
                method=method,
                timeout=timeout,
                session_id=resume_session_id,
                env_vars=env_vars,
                execution_dir=str(execution_dir),
                mcp_config=mcp_config,
                branch_name=branch_name,
            )

            # Always log to MLflow if enabled
            _log_to_mlflow(llm_response, args.prompt, project_dir, branch_name)

            # Store response to file if requested
            if getattr(args, "store_response", False):
                stored_path = store_session(
                    llm_response, args.prompt, branch_name=branch_name
                )
                logger.info("Response stored to: %s", stored_path)

            # Pass raw_response sub-dict to formatters — same shape as before
            raw_data = llm_response["raw_response"]

            # Format based on verbosity level
            if verbosity == "raw":
                formatted_output = format_raw_response(raw_data)
            elif verbosity == "verbose":
                formatted_output = format_verbose_response(raw_data)
            else:
                formatted_output = format_text_response(raw_data)

        # Print formatted output to stdout
        print(formatted_output)

        logger.info("Prompt command completed successfully")
        return 0

    except Exception as e:
        # Handle API errors
        logger.error("Prompt command failed: %s", str(e))
        print(f"Error: {str(e)}", file=sys.stderr)
        return 1
