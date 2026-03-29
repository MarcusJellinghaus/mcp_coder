"""Prompt command for the MCP Coder CLI."""

import argparse
import json
import logging
import sys
from pathlib import Path

from ...llm.env import prepare_llm_environment
from ...llm.formatting.formatters import print_stream_event
from ...llm.interface import prompt_llm, prompt_llm_stream
from ...llm.mlflow_conversation_logger import mlflow_conversation
from ...llm.storage import (
    extract_langchain_session_id,
    extract_session_id,
    find_latest_session,
    store_session,
)
from ...llm.types import ResponseAssembler
from ...utils.git_utils import get_branch_name_for_logging
from ..utils import (
    parse_llm_method_from_args,
    resolve_execution_dir,
    resolve_llm_method,
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

        # Resolve LLM method early (CLI arg > config > default)
        raw_llm_method = getattr(args, "llm_method", None)
        llm_method, _ = resolve_llm_method(raw_llm_method)
        provider = parse_llm_method_from_args(llm_method)

        # Handle continuation from previous session if requested
        # Priority: --session-id > --continue-session-from > --continue-session
        resume_session_id = getattr(args, "session_id", None)
        continue_file_path = None

        # Only check file-based continuation if --session-id not provided
        if not resume_session_id:
            if getattr(args, "continue_session_from", None):
                continue_file_path = args.continue_session_from
            elif getattr(args, "continue_session", False):
                # Find latest session file (provider-aware)
                continue_file_path = find_latest_session(provider=provider)
                if continue_file_path is None:
                    print(
                        "No previous response files found, starting new conversation. Save conversations with --store-response"
                    )
                    # Continue execution without session resumption

            if continue_file_path:
                # Extract session_id from the stored response file
                if provider == "langchain":
                    resume_session_id = extract_langchain_session_id(continue_file_path)
                else:
                    extracted_session_id = extract_session_id(continue_file_path)
                    if extracted_session_id:
                        resume_session_id = extracted_session_id
                if resume_session_id:
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

        # Get user-specified timeout, output_format, and mcp_config
        timeout = getattr(args, "timeout", 30)
        output_format = getattr(args, "output_format", "text")
        mcp_config = resolve_mcp_config_path(
            args.mcp_config, project_dir=args.project_dir
        )

        # Streaming formats use prompt_llm_stream()
        if output_format in ("text", "ndjson", "json-raw"):
            branch_name = get_branch_name_for_logging(project_dir)
            assembler = ResponseAssembler(provider)
            for event in prompt_llm_stream(
                args.prompt,
                provider=provider,
                timeout=timeout,
                session_id=resume_session_id,
                env_vars=env_vars,
                execution_dir=str(execution_dir),
                mcp_config=mcp_config,
                branch_name=branch_name,
            ):
                assembler.add(event)
                print_stream_event(event, output_format)

            llm_response = assembler.result()

            # MLflow logging (mirrors non-streaming path)
            metadata = {
                "branch_name": branch_name,
                "working_directory": str(execution_dir),
            }
            with mlflow_conversation(
                args.prompt, provider, resume_session_id, metadata
            ) as mlflow_ctx:
                mlflow_ctx["response_data"] = llm_response

            # Store response to file if requested
            if getattr(args, "store_response", False):
                stored_path = store_session(
                    llm_response, args.prompt, branch_name=branch_name
                )
                logger.info("Response stored to: %s", stored_path)

        elif output_format == "session-id":
            # Session ID only mode - return only the session_id for shell script capture
            response_dict = prompt_llm(
                args.prompt,
                provider=provider,
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

            print(session_id)
            return 0

        elif output_format == "json":
            # JSON output mode - return full LLMResponseDict
            branch_name = get_branch_name_for_logging(project_dir)
            response_dict = prompt_llm(
                args.prompt,
                provider=provider,
                timeout=timeout,
                session_id=resume_session_id,
                env_vars=env_vars,
                execution_dir=str(execution_dir),
                mcp_config=mcp_config,
                branch_name=branch_name,
            )
            # Output complete response as JSON (includes session_id)
            print(json.dumps(response_dict, indent=2, default=str))

            # Store response to file if requested
            if getattr(args, "store_response", False):
                stored_path = store_session(
                    response_dict, args.prompt, branch_name=branch_name
                )
                logger.info("Response stored to: %s", stored_path)

        logger.info("Prompt command completed successfully")
        return 0

    except (
        Exception
    ) as e:  # pylint: disable=broad-exception-caught  # top-level CLI error boundary
        # Handle API errors
        logger.error("Prompt command failed: %s", str(e))
        print(f"Error: {str(e)}", file=sys.stderr)
        return 1
