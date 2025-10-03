"""SDK message object serialization and handling utilities.

This module provides utilities for working with Claude SDK message objects
and dictionary message formats, enabling unified handling of both formats.

Dual Message Format Compatibility:
This module handles two different message formats:
1. Dictionary format: {"role": "assistant", "content": "text"}
2. SDK object format: AssistantMessage(content=[...])

The utility functions provide unified access to both formats.
"""

import logging
from typing import Any, Dict, List, Optional

from ..providers.claude.claude_code_api import (
    AssistantMessage,
    ResultMessage,
    SystemMessage,
    UserMessage,
)

logger = logging.getLogger(__name__)

__all__ = [
    "is_sdk_message",
    "get_message_role",
    "get_message_tool_calls",
    "serialize_message_for_json",
    "extract_tool_interactions",
]


def is_sdk_message(message: Any) -> bool:
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
        >>> is_sdk_message({"role": "user"})  # Dictionary
        False
        >>> is_sdk_message(SystemMessage(subtype="test"))  # SDK object
        True
        >>> is_sdk_message(None)  # None value
        False
    """
    # Handle None values gracefully
    if message is None:
        return False

    # Check if it's one of the known SDK message types
    return isinstance(
        message, (SystemMessage, AssistantMessage, ResultMessage, UserMessage)
    )


def get_message_role(message: Any) -> Optional[str]:
    """Get role from message (SDK object or dict).

    This unified accessor safely extracts role information from both
    SDK objects and dictionaries, preventing AttributeError when SDK
    objects are accessed with dictionary methods.

    Args:
        message: Message object (SDK object, dictionary, or None)

    Returns:
        Role string ("assistant", "user", "system", "result") or None if not available

    Example:
        >>> get_message_role({"role": "user"})  # Dictionary access
        "user"
        >>> get_message_role(AssistantMessage(...))  # SDK object access
        "assistant"
        >>> get_message_role(None)  # Graceful None handling
        None
    """
    # Handle None values gracefully
    if message is None:
        return None

    if is_sdk_message(message):
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


def get_message_tool_calls(message: Any) -> List[Dict[str, Any]]:
    """Get tool calls from message (SDK object or dict).

    Args:
        message: Message object (SDK object or dictionary)

    Returns:
        List of tool call dictionaries
    """
    # Handle None values gracefully
    if message is None:
        return []

    if is_sdk_message(message):
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


def serialize_message_for_json(obj: Any) -> Any:
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
        if is_sdk_message(obj):
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


def extract_tool_interactions(raw_messages: List[Any]) -> List[str]:
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
            role = get_message_role(message)
            if role == "assistant":
                # Use unified accessor to get tool calls
                tool_calls = get_message_tool_calls(message)
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