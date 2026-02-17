"""Prompt command for the MCP Coder CLI."""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Optional

from ...llm.env import prepare_llm_environment
from ...llm.formatting.formatters import (
    format_raw_response,
    format_text_response,
    format_verbose_response,
)
from ...llm.interface import prompt_llm
from ...llm.storage import extract_session_id, find_latest_session, store_session
from ...utils.git_utils import get_branch_name_for_logging
from ..utils import (
    parse_llm_method_from_args,
    resolve_execution_dir,
    resolve_mcp_config_path,
)

logger = logging.getLogger(__name__)


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
                project_dir=str(project_dir),
                execution_dir=str(execution_dir),
                mcp_config=mcp_config,
            )

            session_id = response_dict.get("session_id", "")
            if not session_id:
                print("Error: No session_id in response", file=sys.stderr)
                return 1

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
                project_dir=str(project_dir),
                execution_dir=str(execution_dir),
                mcp_config=mcp_config,
                branch_name=branch_name,
            )
            # Output complete response as JSON (includes session_id)
            formatted_output = json.dumps(response_dict, indent=2, default=str)

            # Store response if requested
            if getattr(args, "store_response", False):
                stored_path = store_session(response_dict, args.prompt)
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
                project_dir=str(project_dir),
                execution_dir=str(execution_dir),
                mcp_config=mcp_config,
                branch_name=branch_name,
            )

            # Simple text output with tool summary
            formatted_output = llm_response["text"].strip()

            # Store simple response if requested
            if getattr(args, "store_response", False):
                stored_path = store_session(llm_response, args.prompt)
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
                project_dir=str(project_dir),
                execution_dir=str(execution_dir),
                mcp_config=mcp_config,
                branch_name=branch_name,
            )

            # Store response if requested
            if getattr(args, "store_response", False):
                stored_path = store_session(llm_response, args.prompt)
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
