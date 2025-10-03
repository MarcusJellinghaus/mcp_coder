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
from ..llm_helpers import parse_llm_method

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
                continue_file_path = _find_latest_response_file()
                if continue_file_path is None:
                    print("No previous response files found, starting new conversation")
                    # Continue execution without session resumption

            if continue_file_path:
                # Extract session_id from the stored response file
                extracted_session_id = _extract_session_id_from_file(continue_file_path)
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

            provider, method = parse_llm_method(llm_method)
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
            provider, method = parse_llm_method(llm_method)
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
                stored_path = _store_response(response_data, args.prompt)
                logger.info("Response stored to: %s", stored_path)
        else:
            # Use detailed API for verbose/raw modes that need metadata
            response_data = ask_claude_code_api_detailed_sync(
                args.prompt, timeout, resume_session_id
            )

            # Store response if requested
            if getattr(args, "store_response", False):
                stored_path = _store_response(response_data, args.prompt)
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


def _store_response(
    response_data: Dict[str, Any], prompt: str, store_path: Optional[str] = None
) -> str:
    """Store complete session data to .mcp-coder/responses/ directory.

    Args:
        response_data: Response dictionary from ask_claude_code_api_detailed_sync
        prompt: Original user prompt
        store_path: Optional custom path for storage directory

    Returns:
        File path of stored session for potential user reference
    """
    # Determine storage directory
    if store_path is None:
        storage_dir = ".mcp-coder/responses"
    else:
        storage_dir = store_path

    # Create storage directory if it doesn't exist
    os.makedirs(storage_dir, exist_ok=True)

    # Generate timestamp-based filename
    timestamp = datetime.now().isoformat().replace(":", "-").split(".")[0]
    filename = f"response_{timestamp}.json"
    file_path = os.path.join(storage_dir, filename)

    # Create complete session JSON structure
    session_data = {
        "prompt": prompt,
        "response_data": response_data,
        "metadata": {
            "timestamp": datetime.now().isoformat() + "Z",
            "working_directory": os.getcwd(),
            "model": response_data.get("session_info", {}).get(
                "model", "claude-3-5-sonnet"
            ),
        },
    }

    # Write JSON file
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(session_data, f, indent=2, default=str)

    return file_path


def _extract_session_id_from_file(file_path: str) -> Optional[str]:
    """Extract session_id from a stored response file.

    Args:
        file_path: Path to the stored session JSON file

    Returns:
        Session ID string if found, None otherwise
    """
    logger.info("Extracting session_id from: %s", file_path)

    try:
        # Check if file exists
        if not os.path.exists(file_path):
            logger.warning("Response file not found: %s", file_path)
            return None

        # Read and parse JSON file
        with open(file_path, "r", encoding="utf-8") as f:
            session_data = json.load(f)

        # Try multiple paths to find session_id
        # Path 1: response_data.session_info.session_id (detailed API response)
        session_id: Optional[str] = (
            session_data.get("response_data", {})
            .get("session_info", {})
            .get("session_id")
        )
        if session_id and isinstance(session_id, str):
            logger.debug(
                "Found session_id in response_data.session_info: %s", session_id
            )
            return session_id

        # Path 2: Direct session_id field (simple response format)
        session_id = session_data.get("session_id")
        if session_id and isinstance(session_id, str):
            logger.debug("Found session_id at root level: %s", session_id)
            return session_id

        # Path 3: metadata.session_id (alternative storage location)
        session_id = session_data.get("metadata", {}).get("session_id")
        if session_id and isinstance(session_id, str):
            logger.debug("Found session_id in metadata: %s", session_id)
            return session_id

        logger.warning("No session_id found in file: %s", file_path)
        return None

    except json.JSONDecodeError as e:
        logger.error("Invalid JSON in file %s: %s", file_path, e)
        return None
    except Exception as e:
        logger.error("Error reading session file %s: %s", file_path, e)
        return None


def _find_latest_response_file(
    responses_dir: str = ".mcp-coder/responses",
) -> Optional[str]:
    """Find the most recent response file by filename timestamp with strict validation.

    Args:
        responses_dir: Directory containing response files

    Returns:
        Path to latest response file, or None if none found
    """
    logger.debug("Searching for response files in: %s", responses_dir)

    # Check if responses directory exists
    if not os.path.exists(responses_dir):
        logger.debug("Responses directory does not exist: %s", responses_dir)
        return None

    try:
        # Use glob to find response files with the expected pattern
        pattern = os.path.join(responses_dir, "response_*.json")
        response_files = glob.glob(pattern)

        if not response_files:
            logger.debug("No response files found in: %s", responses_dir)
            return None

        # ISO timestamp pattern: response_YYYY-MM-DDTHH-MM-SS.json
        timestamp_pattern = r"^response_(\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2})\.json$"

        # Validate each file matches strict ISO timestamp pattern
        valid_files = []
        for file_path in response_files:
            filename = os.path.basename(file_path)
            match = re.match(timestamp_pattern, filename)
            if match:
                timestamp_str = match.group(1)  # Extract the timestamp part
                try:
                    # Use datetime.strptime for robust validation
                    datetime.strptime(timestamp_str, "%Y-%m-%dT%H-%M-%S")
                    valid_files.append(file_path)
                except ValueError:
                    logger.debug("Invalid timestamp in filename: %s", filename)
            else:
                logger.debug("Skipping invalid filename format: %s", filename)

        if not valid_files:
            logger.debug("No valid response files found with ISO timestamp format")
            return None

        # Sort validated filenames by timestamp (lexicographic sort works for ISO format)
        valid_files.sort()
        latest_file = valid_files[-1]  # Last file after sorting is the latest

        # Provide user feedback showing count and selected file
        num_sessions = len(valid_files)
        selected_filename = os.path.basename(latest_file)
        print(
            f"Found {num_sessions} previous sessions, continuing from: {selected_filename}"
        )

        logger.debug("Selected latest response file: %s", latest_file)
        return latest_file

    except (OSError, IOError) as e:
        logger.debug("Error accessing response directory %s: %s", responses_dir, e)
        return None
    except Exception as e:
        logger.debug("Unexpected error finding response files: %s", e)
        return None
