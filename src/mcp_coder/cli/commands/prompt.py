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
from typing import Any, Dict, List, Optional, Union

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
from ..utils import parse_llm_method_from_args
from ...llm.storage import (
    extract_session_id,
    find_latest_session,
    store_session,
)

logger = logging.getLogger(__name__)


def execute_prompt(args: argparse.Namespace) -> int:
    """Execute prompt command to ask Claude a question.

    Args:
        args: Command line arguments with prompt attribute and optional verbosity

    Returns:
        Exit code (0 for success, 1 for error)
    """
    logger.info("Executing prompt command")

    try:
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
                print(f"Using explicit session ID (ignoring file-based continuation)")

        # Get user-specified timeout, llm_method, and output_format
        timeout = getattr(args, "timeout", 30)
        llm_method = getattr(args, "llm_method", "claude_code_api")
        verbosity = getattr(args, "verbosity", "just-text")
        output_format = getattr(args, "output_format", "text")

        # Route to appropriate method based on output_format and verbosity
        if output_format == "json":
            # JSON output mode - return full LLMResponseDict
            from ...llm.interface import prompt_llm

            provider, method = parse_llm_method_from_args(llm_method)
            response_dict = prompt_llm(
                args.prompt,
                provider=provider,
                method=method,
                timeout=timeout,
                session_id=resume_session_id,
            )
            # Output complete response as JSON (includes session_id)
            formatted_output = json.dumps(response_dict, indent=2, default=str)
        elif verbosity == "just-text":
            # Use unified ask_llm interface for simple text output
            provider, method = parse_llm_method_from_args(llm_method)
            response = ask_llm(
                args.prompt,
                provider=provider,
                method=method,
                timeout=timeout,
                session_id=resume_session_id,
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
                args.prompt, timeout, resume_session_id
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
