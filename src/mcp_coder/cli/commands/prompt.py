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

from ...llm_providers.claude.claude_code_api import (
    AssistantMessage,
    ResultMessage,
    SystemMessage,
    TextBlock,
    UserMessage,
    ask_claude_code_api_detailed_sync,
)

logger = logging.getLogger(__name__)


# Utility functions for SDK message object handling
def _is_sdk_message(message: Any) -> bool:
    """Check if message is a Claude SDK object vs dictionary.

    This utility function distinguishes between Claude SDK message objects
    (SystemMessage, AssistantMessage, ResultMessage, UserMessage) and plain dictionaries.
    It's essential for the unified handling approach that fixes the
    AttributeError when SDK objects are accessed with .get() method.

    Args:
        message: Message object to check (can be SDK object, dict, or None)

    Returns:
        True if message is a Claude SDK object, False for dictionaries or None

    Example:
        >>> _is_sdk_message({"role": "user"})  # Dictionary
        False
        >>> _is_sdk_message(SystemMessage(subtype="test"))  # SDK object
        True
        >>> _is_sdk_message(None)  # None value
        False
    """
    # Handle None values gracefully
    if message is None:
        return False

    # Check if it's one of the known SDK message types
    return isinstance(
        message, (SystemMessage, AssistantMessage, ResultMessage, UserMessage)
    )


def _get_message_role(message: Any) -> Optional[str]:
    """Get role from message (SDK object or dict).

    This unified accessor safely extracts role information from both
    SDK objects and dictionaries, preventing AttributeError when SDK
    objects are accessed with dictionary methods.

    Args:
        message: Message object (SDK object, dictionary, or None)

    Returns:
        Role string ("assistant", "user", "system", "result") or None if not available

    Example:
        >>> _get_message_role({"role": "user"})  # Dictionary access
        "user"
        >>> _get_message_role(AssistantMessage(...))  # SDK object access
        "assistant"
        >>> _get_message_role(None)  # Graceful None handling
        None
    """
    # Handle None values gracefully
    if message is None:
        return None

    if _is_sdk_message(message):
        # For SDK objects, check for role attribute or infer from type
        if hasattr(message, "role"):
            role_value = getattr(message, "role", None)
            if isinstance(role_value, str):
                return role_value
        # Infer role from SDK message type
        if isinstance(message, AssistantMessage):
            return "assistant"
        elif isinstance(message, SystemMessage):
            return "system"
        elif isinstance(message, ResultMessage):
            return "result"
        return None
    else:
        # For dictionaries, use .get() method with fallback
        if isinstance(message, dict):
            return message.get("role")
        return None


def _get_message_tool_calls(message: Any) -> List[Dict[str, Any]]:
    """Get tool calls from message (SDK object or dict).

    Args:
        message: Message object (SDK object or dictionary)

    Returns:
        List of tool call dictionaries
    """
    # Handle None values gracefully
    if message is None:
        return []

    if _is_sdk_message(message):
        # For SDK objects, check for content with ToolUseBlock objects
        if isinstance(message, AssistantMessage) and hasattr(message, "content"):
            tool_calls: List[Dict[str, Any]] = []
            content = getattr(message, "content", None)
            if content is not None:
                try:
                    for block in content:
                        # Check if this is a tool use block by looking for name and input attributes
                        if hasattr(block, "name") and hasattr(block, "input"):
                            tool_name = getattr(block, "name", "unknown_tool")
                            tool_input = getattr(block, "input", {})
                            tool_calls.append(
                                {"name": tool_name, "parameters": tool_input}
                            )
                        # Also check for 'parameters' attribute as alternative to 'input'
                        elif hasattr(block, "name") and hasattr(block, "parameters"):
                            tool_name = getattr(block, "name", "unknown_tool")
                            tool_params = getattr(block, "parameters", {})
                            tool_calls.append(
                                {"name": tool_name, "parameters": tool_params}
                            )
                except (TypeError, AttributeError) as e:
                    # Handle cases where content is not iterable or has issues
                    logger.debug(f"Error extracting tool calls from SDK content: {e}")
            return tool_calls
        return []
    else:
        # For dictionaries, use .get() method with fallback
        if isinstance(message, dict):
            tool_calls_result = message.get("tool_calls", [])
            if isinstance(tool_calls_result, list):
                return tool_calls_result
        return []


def _serialize_message_for_json(obj: Any) -> Any:
    """Convert SDK message objects to JSON-serializable format.

    This function serves as a custom JSON serializer for json.dumps() default parameter.
    It converts Claude SDK message objects to dictionaries while leaving other
    JSON-serializable objects unchanged.

    Args:
        obj: Object to serialize (SDK message or any other object)

    Returns:
        For SDK objects: Dictionary representation using official SDK structure
        For other objects: The object unchanged (handled by json.dumps)
    """
    # Handle None values gracefully
    if obj is None:
        return None

    try:
        if _is_sdk_message(obj):
            # Use official SDK structure for serialization
            if isinstance(obj, SystemMessage):
                return {
                    "type": "SystemMessage",
                    "subtype": getattr(obj, "subtype", None),
                    "data": getattr(obj, "data", {}),
                }
            elif isinstance(obj, AssistantMessage):
                content_data = []
                content = getattr(obj, "content", None)
                if content is not None:
                    try:
                        for block in content:
                            if hasattr(block, "text"):  # TextBlock
                                content_data.append(
                                    {"type": "text", "text": getattr(block, "text", "")}
                                )
                            elif hasattr(block, "name") and hasattr(
                                block, "input"
                            ):  # ToolUseBlock
                                content_data.append(
                                    {
                                        "type": "tool_use",
                                        "id": getattr(block, "id", ""),
                                        "name": getattr(block, "name", ""),
                                        "input": getattr(block, "input", {}),
                                    }
                                )
                            else:
                                # Other block types - use string representation
                                content_data.append(
                                    {"type": "unknown", "data": str(block)}
                                )
                    except (TypeError, AttributeError):
                        # Handle cases where content is not iterable or has issues
                        content_data.append({"type": "error", "data": str(content)})
                return {
                    "type": "AssistantMessage",
                    "content": content_data,
                    "model": getattr(obj, "model", None),
                }
            elif isinstance(obj, UserMessage):
                content_data = []
                content = getattr(obj, "content", None)
                if content is not None:
                    try:
                        for block in content:
                            if hasattr(block, "tool_use_id"):  # ToolResultBlock
                                # Safely extract tool result content
                                tool_content = getattr(block, "content", "")
                                # Truncate very long content to prevent circular references
                                if (
                                    isinstance(tool_content, str)
                                    and len(tool_content) > 500
                                ):
                                    tool_content = (
                                        tool_content[:500] + "... [truncated]"
                                    )
                                content_data.append(
                                    {
                                        "type": "tool_result",
                                        "tool_use_id": getattr(
                                            block, "tool_use_id", ""
                                        ),
                                        "content": str(tool_content),
                                        "is_error": getattr(block, "is_error", False),
                                    }
                                )
                            else:
                                # Other block types - use string representation, safely truncated
                                block_str = str(block)
                                if len(block_str) > 500:
                                    block_str = block_str[:500] + "... [truncated]"
                                content_data.append(
                                    {"type": "unknown", "data": block_str}
                                )
                    except (TypeError, AttributeError) as e:
                        # Handle cases where content is not iterable or has issues
                        content_data.append(
                            {"type": "error", "data": f"Serialization error: {str(e)}"}
                        )
                return {
                    "type": "UserMessage",
                    "content": content_data,
                    "parent_tool_use_id": getattr(obj, "parent_tool_use_id", None),
                }
            elif isinstance(obj, ResultMessage):
                return {
                    "type": "ResultMessage",
                    "subtype": getattr(obj, "subtype", None),
                    "duration_ms": getattr(obj, "duration_ms", None),
                    "duration_api_ms": getattr(obj, "duration_api_ms", None),
                    "is_error": getattr(obj, "is_error", None),
                    "num_turns": getattr(obj, "num_turns", None),
                    "session_id": getattr(obj, "session_id", None),
                    "total_cost_usd": getattr(obj, "total_cost_usd", None),
                }
            else:
                # Fallback for unknown SDK message types or malformed objects
                try:
                    return {"type": type(obj).__name__, "data": str(obj)}
                except Exception as e:
                    # Log the error for debugging purposes
                    logger.debug(
                        f"Failed to serialize object {type(obj).__name__}: {e}"
                    )
                    # Final fallback for objects that can't be stringified
                    return {"type": "unknown", "data": "<unserializable object>"}
        # For non-SDK objects, return unchanged (let json.dumps handle them)
        return obj
    except Exception as e:
        # Catch any remaining serialization errors
        logger.debug(f"Serialization error for {type(obj).__name__}: {e}")
        return f"<serialization error: {type(obj).__name__}>"


def _extract_tool_interactions(raw_messages: List[Any]) -> List[str]:
    """Extract tool interaction summaries from raw messages.

    Args:
        raw_messages: List of message objects (SDK objects or dictionaries)

    Returns:
        List of tool interaction summary strings
    """
    tool_interactions: List[str] = []

    # Handle None or empty list gracefully
    if not raw_messages:
        return tool_interactions

    for message in raw_messages:
        # Skip None messages
        if message is None:
            continue

        try:
            # Use unified accessor to get role
            role = _get_message_role(message)
            if role == "assistant":
                # Use unified accessor to get tool calls
                tool_calls = _get_message_tool_calls(message)
                for tool_call in tool_calls:
                    if isinstance(tool_call, dict):
                        tool_name = tool_call.get("name", "unknown_tool")
                        tool_params = tool_call.get("parameters", {})
                        tool_interactions.append(f"  - {tool_name}: {tool_params}")
        except (AttributeError, TypeError, KeyError) as e:
            # Log the error but continue processing other messages
            logger.debug(f"Error processing message for tool interactions: {e}")
            continue

    return tool_interactions


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
        enhanced_prompt = args.prompt
        continue_file_path = None

        if getattr(args, "continue_from", None):
            continue_file_path = args.continue_from
        elif getattr(args, "continue", False):
            continue_file_path = _find_latest_response_file()
            if continue_file_path is None:
                print("No previous response files found, starting new conversation")
                # Continue execution with empty context instead of returning

        if continue_file_path:
            previous_context = _load_previous_chat(continue_file_path)
            enhanced_prompt = _build_context_prompt(previous_context, args.prompt)

        # Call Claude API using detailed function with user-specified timeout
        timeout = getattr(args, "timeout", 30)
        response_data = ask_claude_code_api_detailed_sync(enhanced_prompt, timeout)

        # Store response if requested
        if getattr(args, "store_response", False):
            stored_path = _store_response(response_data, args.prompt)
            logger.info("Response stored to: %s", stored_path)

        # Route to appropriate formatter based on verbosity level
        verbosity = getattr(args, "verbosity", "just-text")
        if verbosity == "raw":
            formatted_output = _format_raw(response_data)
        elif verbosity == "verbose":
            formatted_output = _format_verbose(response_data)
        else:
            # Default to just-text format
            formatted_output = _format_just_text(response_data)

        # Print formatted output to stdout
        print(formatted_output)

        logger.info("Prompt command completed successfully")
        return 0

    except Exception as e:
        # Handle API errors
        logger.error("Prompt command failed: %s", str(e))
        print(f"Error: {str(e)}", file=sys.stderr)
        return 1


def _format_just_text(response_data: Dict[str, Any]) -> str:
    """Format response data as just-text output (default verbosity level).

    Args:
        response_data: Response dictionary from ask_claude_code_api_detailed_sync

    Returns:
        Formatted string with Claude response + tool usage summary
    """
    # Extract Claude's response text
    response_text = response_data.get("text", "").strip()

    # Extract tools used from session info
    session_info = response_data.get("session_info", {})
    tools = session_info.get("tools", [])

    # Create tool usage summary
    if tools:
        tool_summary = f"Used {len(tools)} tools: {', '.join(tools)}"
    else:
        tool_summary = "No tools used"

    # Combine response and tool summary
    formatted_parts = []
    if response_text:
        formatted_parts.append(response_text)
    formatted_parts.append(f"\n--- {tool_summary} ---")

    return "\n".join(formatted_parts)


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


def _format_raw(response_data: Dict[str, Any]) -> str:
    """Format response data as raw output with complete debug output including JSON structures.

    Args:
        response_data: Response dictionary from ask_claude_code_api_detailed_sync

    Returns:
        Formatted string with complete debugging information including JSON structures
    """

    # Start with everything from verbose format
    verbose_output = _format_verbose(response_data)

    # Extract additional data for raw output
    raw_messages = response_data.get("raw_messages", [])
    api_metadata = response_data.get("api_metadata", {})

    # Build additional raw output sections
    formatted_parts = [verbose_output, ""]

    # Complete JSON API Response section
    formatted_parts.append("=== Complete JSON API Response ===")
    try:
        formatted_parts.append(
            json.dumps(response_data, indent=2, default=_serialize_message_for_json)
        )
    except Exception as e:
        # If serialization fails (e.g., circular reference), fall back to string representation
        formatted_parts.append(f"JSON serialization failed: {e}")
        formatted_parts.append(f"Response data type: {type(response_data)}")
        formatted_parts.append(
            f"Response data keys: {list(response_data.keys()) if isinstance(response_data, dict) else 'Not a dict'}"
        )
    formatted_parts.append("")

    # Raw Messages section with complete details
    formatted_parts.append("=== Raw Messages ===")
    if raw_messages:
        for i, message in enumerate(raw_messages):
            formatted_parts.append(f"Message {i + 1}:")
            try:
                formatted_parts.append(
                    json.dumps(message, indent=2, default=_serialize_message_for_json)
                )
            except Exception as e:
                # If individual message serialization fails, show basic info
                formatted_parts.append(f"Message serialization failed: {e}")
                formatted_parts.append(f"Message type: {type(message)}")
                formatted_parts.append(
                    f"Message string representation: {str(message)[:200]}..."
                )
            formatted_parts.append("")
    else:
        formatted_parts.append("  No raw messages available")
        formatted_parts.append("")

    # API Metadata section
    formatted_parts.append("=== API Metadata ===")
    if api_metadata:
        try:
            formatted_parts.append(
                json.dumps(api_metadata, indent=2, default=_serialize_message_for_json)
            )
        except Exception as e:
            formatted_parts.append(f"API metadata serialization failed: {e}")
            formatted_parts.append(f"Metadata type: {type(api_metadata)}")
    else:
        formatted_parts.append("  No API metadata available")

    return "\n".join(formatted_parts)


def _format_verbose(response_data: Dict[str, Any]) -> str:
    """Format response data as verbose output with detailed tool interactions and metrics.

    Args:
        response_data: Response dictionary from ask_claude_code_api_detailed_sync

    Returns:
        Formatted string with Claude response + tool details + performance metrics + session info
    """
    # Extract Claude's response text
    response_text = response_data.get("text", "").strip()

    # Extract session info
    session_info = response_data.get("session_info", {})
    session_id = session_info.get("session_id", "unknown")
    model = session_info.get("model", "unknown")
    tools = session_info.get("tools", [])
    mcp_servers = session_info.get("mcp_servers", [])

    # Extract performance metrics
    result_info = response_data.get("result_info", {})
    duration_ms = result_info.get("duration_ms", 0)
    cost_usd = result_info.get("cost_usd", 0.0)
    usage = result_info.get("usage", {})
    input_tokens = usage.get("input_tokens", 0)
    output_tokens = usage.get("output_tokens", 0)

    # Extract tool interactions from raw messages using utility functions
    raw_messages = response_data.get("raw_messages", [])
    tool_interactions = _extract_tool_interactions(raw_messages)

    # Build formatted output sections
    formatted_parts = []

    # Claude response
    if response_text:
        formatted_parts.append(response_text)
        formatted_parts.append("")

    # Tool interactions section
    formatted_parts.append("=== Tool Interactions ===")
    if tool_interactions:
        for interaction in tool_interactions:
            formatted_parts.append(interaction)
    else:
        formatted_parts.append("  No tool calls made")
    formatted_parts.append("")

    # Performance metrics section
    formatted_parts.append("=== Performance Metrics ===")
    duration_sec = duration_ms / 1000.0
    formatted_parts.append(f"  Duration: {duration_sec:.2f}s ({duration_ms}ms)")
    formatted_parts.append(f"  Cost: ${cost_usd:.4f}")
    formatted_parts.append(f"  Tokens: input={input_tokens}, output={output_tokens}")
    formatted_parts.append("")

    # Session information section
    formatted_parts.append("=== Session Information ===")
    formatted_parts.append(f"  Session ID: {session_id}")
    formatted_parts.append(f"  Model: {model}")
    if tools:
        formatted_parts.append(f"  Available Tools: {', '.join(tools)}")
    if mcp_servers:
        formatted_parts.append("  MCP Servers:")
        for server in mcp_servers:
            server_name = server.get("name", "unknown")
            server_status = server.get("status", "unknown")
            formatted_parts.append(f"    - {server_name}: {server_status}")

    return "\n".join(formatted_parts)


def _load_previous_chat(file_path: str) -> Dict[str, Any]:
    """Load stored session from JSON file for continuation.

    Args:
        file_path: Path to the stored session JSON file

    Returns:
        Dictionary containing previous session context

    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If file contains invalid JSON
        KeyError: If file is missing required fields
    """
    logger.info("Loading previous chat from: %s", file_path)

    # Check if file exists
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Previous session file not found: {file_path}")

    # Read and parse JSON file
    with open(file_path, "r", encoding="utf-8") as f:
        session_data = json.load(f)

    # Validate required fields
    required_fields = ["prompt", "response_data"]
    for field in required_fields:
        if field not in session_data:
            raise KeyError(f"Missing required field '{field}' in session file")

    # Extract previous conversation context
    previous_prompt = session_data["prompt"]
    previous_response = session_data["response_data"].get("text", "")

    return {
        "previous_prompt": previous_prompt,
        "previous_response": previous_response,
        "metadata": session_data.get("metadata", {}),
    }


def _build_context_prompt(previous_context: Dict[str, Any], new_prompt: str) -> str:
    """Build enhanced prompt with previous conversation context.

    Args:
        previous_context: Context from previous session
        new_prompt: New prompt from user

    Returns:
        Enhanced prompt combining previous context with new prompt
    """
    previous_prompt = previous_context.get("previous_prompt", "")
    previous_response = previous_context.get("previous_response", "")

    # Build context-aware prompt
    context_parts = [
        "Previous conversation:",
        f"User: {previous_prompt}",
        f"Assistant: {previous_response}",
        "",
        f"Current question: {new_prompt}",
    ]

    return "\n".join(context_parts)


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

        # Show selected filename to user for transparency (Decision #6)
        selected_filename = os.path.basename(latest_file)
        print(
            f"Found {len(valid_files)} previous sessions, continuing from: {selected_filename}"
        )

        logger.debug("Selected latest response file: %s", latest_file)
        return latest_file

    except (OSError, IOError) as e:
        logger.debug("Error accessing response directory %s: %s", responses_dir, e)
        return None
    except Exception as e:
        logger.debug("Unexpected error finding response files: %s", e)
        return None
