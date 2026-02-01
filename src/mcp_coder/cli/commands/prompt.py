"""Prompt command for the MCP Coder CLI.

Dual Message Format Compatibility:
This module handles two different message formats to maintain backward compatibility:

1. Dictionary format: Used in tests and legacy code
   - Accessed with .get() method: message.get("role")
   - Example: {"role": "assistant", "content": "text"}

2. SDK object format: Used in production with real Claude API
   - Accessed with attributes: message.role or message.subtype
   - Example: SystemMessage(subtype="test", data={...})

The utility functions (_is_sdk_message, _get_message_role, etc.) provide unified
access to both formats, preventing AttributeError when SDK objects are accessed
with dictionary methods like .get(). This fixes the original issue where
'SystemMessage' object has no attribute 'get' occurred in verbose/raw output."""

import argparse
import glob
import json
import logging
import os
import os.path
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from ...llm.env import prepare_llm_environment
from ...llm.formatting.formatters import (
    format_raw_response,
    format_text_response,
    format_verbose_response,
)
from ...llm.formatting.sdk_serialization import (
    extract_tool_interactions,
    get_message_role,
    get_message_tool_calls,
    is_sdk_message,
    serialize_message_for_json,
)
from ...llm.interface import ask_llm
from ...llm.providers.claude.claude_code_api import (
    AssistantMessage,
    ResultMessage,
    SystemMessage,
    TextBlock,
    UserMessage,
    ask_claude_code_api_detailed_sync,
)
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
        if output_format == "json":
            # JSON output mode - return full LLMResponseDict
            from ...llm.interface import prompt_llm

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
        elif verbosity == "just-text":
            # Use unified ask_llm interface for simple text output
            provider, method = parse_llm_method_from_args(llm_method)
            branch_name = get_branch_name_for_logging(project_dir)
            response = ask_llm(
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
            formatted_output = response.strip()

            # Store simple response if requested
            if getattr(args, "store_response", False):
                # Create minimal response data for storage
                response_data = {
                    "text": response,
                    "session_info": {"model": "claude", "tools": []},
                    "result_info": {"duration_ms": 0, "cost_usd": 0.0},
                }
                stored_path = store_session(response_data, args.prompt)
                logger.info("Response stored to: %s", stored_path)
        else:
            # Use detailed API for verbose/raw modes that need metadata
            response_data = ask_claude_code_api_detailed_sync(
                args.prompt, timeout, resume_session_id, env_vars, str(project_dir)
            )

            # Store response if requested
            if getattr(args, "store_response", False):
                stored_path = store_session(response_data, args.prompt)
                logger.info("Response stored to: %s", stored_path)

            # Format based on verbosity level
            if verbosity == "raw":
                formatted_output = format_raw_response(response_data)
            elif verbosity == "verbose":
                formatted_output = format_verbose_response(response_data)
            else:
                formatted_output = format_text_response(response_data)

        # Print formatted output to stdout
        print(formatted_output)

        logger.info("Prompt command completed successfully")
        return 0

    except Exception as e:
        # Handle API errors
        logger.error("Prompt command failed: %s", str(e))
        print(f"Error: {str(e)}", file=sys.stderr)
        return 1
