#!/usr/bin/env python3
"""Claude Code Python SDK implementation for programmatic interaction."""

import asyncio
import os
import subprocess
from typing import Any, Optional

from .claude_executable_finder import find_claude_executable, setup_claude_path

try:
    from claude_code_sdk import ClaudeCodeOptions, query
except ImportError as e:
    raise ImportError(
        "claude-code-sdk is not installed. Please install it with: "
        "pip install claude-code-sdk"
    ) from e


def _create_claude_client() -> ClaudeCodeOptions:
    """Create a Claude Code SDK client with basic configuration.

    Returns:
        ClaudeCodeOptions object configured for basic usage

    Note:
        The SDK will use existing CLI subscription authentication automatically.
        Attempts to setup PATH if Claude CLI is not accessible.
    """
    # Try to setup Claude PATH before creating client
    # The SDK needs the CLI to be accessible for authentication
    setup_claude_path()

    # Use basic configuration - SDK should now find Claude
    return ClaudeCodeOptions()


async def _ask_claude_code_api_async(question: str, timeout: int = 30) -> str:
    """
    Ask Claude a question via Python SDK asynchronously.

    The Claude Code SDK returns a stream of different message types:
    - SystemMessage: Session metadata and configuration info
    - AssistantMessage: Contains TextBlock objects with Claude's response
    - ResultMessage: Final results with cost, usage, and session info

    This function extracts and returns only the text content from AssistantMessage.TextBlock objects.

    For complete response structure documentation, see:
    https://docs.anthropic.com/en/docs/claude-code/sdk/sdk-python

    Args:
        question: The question to ask Claude
        timeout: Timeout in seconds for the request (default: 30)

    Returns:
        Claude's response as a string (concatenated text from all TextBlocks)

    Raises:
        asyncio.TimeoutError: If the request times out
        Exception: Various exceptions from the SDK
    """
    options = _create_claude_client()

    # Import message types for proper type checking
    try:
        from claude_code_sdk import (
            AssistantMessage,
            ResultMessage,
            SystemMessage,
            TextBlock,
        )
    except ImportError:
        # Fallback to string-based type checking if imports fail
        AssistantMessage = None  # type: ignore[assignment,misc]
        TextBlock = None  # type: ignore[assignment,misc]
        SystemMessage = None  # type: ignore[assignment,misc]
        ResultMessage = None  # type: ignore[assignment,misc]

    # Use asyncio timeout to respect the timeout parameter
    async def _query_with_timeout() -> str:
        response_parts = []
        session_info: dict[str, Any] = {}
        result_info: dict[str, Any] = {}

        async for message in query(prompt=question, options=options):
            # Handle different message types according to SDK documentation
            if AssistantMessage is not None and isinstance(message, AssistantMessage):
                # AssistantMessage contains content blocks (TextBlock, ToolUseBlock, etc.)
                for block in message.content:
                    if TextBlock is not None and isinstance(block, TextBlock):
                        response_parts.append(block.text)

            elif SystemMessage is not None and isinstance(message, SystemMessage):
                # SystemMessage contains session metadata - store for debugging
                session_info.update(
                    {
                        "session_id": getattr(message, "session_id", None),
                        "model": (
                            message.data.get("model")
                            if hasattr(message, "data")
                            else None
                        ),
                        "tools": (
                            message.data.get("tools", [])
                            if hasattr(message, "data")
                            else []
                        ),
                        "mcp_servers": (
                            message.data.get("mcp_servers", [])
                            if hasattr(message, "data")
                            else []
                        ),
                    }
                )

            elif ResultMessage is not None and isinstance(message, ResultMessage):
                # ResultMessage contains cost and usage information
                result_info.update(
                    {
                        "duration_ms": getattr(message, "duration_ms", None),
                        "cost_usd": getattr(message, "total_cost_usd", None),
                        "usage": getattr(message, "usage", None),
                        "result": getattr(message, "result", None),
                    }
                )

            else:
                # Fallback for unknown message types or when imports failed
                # Check for common attributes and extract text content
                message_type = type(message).__name__

                if message_type == "AssistantMessage":
                    # Handle AssistantMessage without import
                    if hasattr(message, "content"):
                        for content_block in message.content:
                            if hasattr(content_block, "text"):
                                response_parts.append(content_block.text)

                elif hasattr(message, "text") and message.text:
                    # Direct text attribute
                    response_parts.append(message.text)
                elif hasattr(message, "content") and message.content:
                    # Content attribute that might be text
                    if isinstance(message.content, str):
                        response_parts.append(message.content)
                    else:
                        # Try to extract text from content blocks
                        try:
                            for content_block in message.content:
                                if hasattr(content_block, "text"):
                                    response_parts.append(content_block.text)
                        except (TypeError, AttributeError):
                            # Fallback: convert to string
                            response_parts.append(str(message.content))

        # Session and result info are collected but not printed in production

        return "".join(response_parts).strip()

    try:
        return await asyncio.wait_for(_query_with_timeout(), timeout)
    except asyncio.TimeoutError as exc:
        raise subprocess.TimeoutExpired(
            ["claude-code-sdk", "query"],
            timeout,
            f"Claude Code SDK request timed out after {timeout} seconds",
        ) from exc


def ask_claude_code_api(question: str, timeout: int = 30) -> str:
    """
    Ask Claude a question via Python SDK and return the response.

    This is a synchronous wrapper around the async SDK functionality.
    The function makes a real API call to Claude using the claude-code-sdk.

    The SDK returns multiple message types in sequence:
    1. SystemMessage: Contains session info, available tools, model details
    2. AssistantMessage: Contains TextBlock objects with Claude's actual response
    3. ResultMessage: Contains cost, duration, and usage statistics

    This function extracts only the text content from AssistantMessage.TextBlock objects
    and returns it as a concatenated string.

    Response Structure Example:
        SystemMessage(
            session_id='abc123',
            data={'model': 'claude-sonnet-4', 'tools': [...], 'mcp_servers': [...]}
        )
        AssistantMessage(
            content=[TextBlock(text="10")]
        )
        ResultMessage(
            total_cost_usd=0.058779,
            duration_ms=2801,
            usage={'input_tokens': 4, 'output_tokens': 5, ...}
        )

    For complete SDK documentation, see:
    https://docs.anthropic.com/en/docs/claude-code/sdk/sdk-python

    Args:
        question: The question to ask Claude
        timeout: Timeout in seconds for the request (default: 30)

    Returns:
        Claude's response as a string (text content only)

    Raises:
        subprocess.TimeoutExpired: If the request times out
        subprocess.CalledProcessError: If the SDK request fails (with helpful error messages)
        ImportError: If claude-code-sdk is not installed
    """
    try:
        # Run the async function in the current event loop or create a new one
        return asyncio.run(_ask_claude_code_api_async(question, timeout))

    except subprocess.TimeoutExpired:
        # Re-raise timeout errors as-is for consistency with CLI version
        raise

    except Exception as e:
        # Convert other exceptions to CalledProcessError for consistency with CLI version
        error_msg = str(e)

        # Check if this is a CLI path issue and provide helpful guidance
        if "Claude Code not found" in error_msg or "claude" in error_msg.lower():
            claude_path = find_claude_executable(return_none_if_not_found=True)
            if claude_path:
                # Get dynamic username for path suggestions
                username = os.environ.get(
                    "USERNAME", os.environ.get("USER", "<username>")
                )

                error_msg += f"\n\nFound Claude CLI at: {claude_path}"
                error_msg += "\nTo fix this issue, add Claude to your PATH:"
                error_msg += f"\n  Windows PowerShell: $env:PATH = 'C:\\Users\\{username}\\.local\\bin;' + $env:PATH"
                error_msg += f"\n  Windows CMD: set PATH=C:\\Users\\{username}\\.local\\bin;%PATH%"
                error_msg += (
                    "\n  Or restart your terminal after installing Claude globally."
                )
            else:
                error_msg += "\n\nClaude CLI not found. Install with: npm install -g @anthropic-ai/claude-code"
                error_msg += "\nThen restart your terminal or add Claude to your PATH."

        raise subprocess.CalledProcessError(
            1,  # Generic error code
            ["claude-code-sdk", "query"],
            output="",
            stderr=f"Claude Code SDK request failed: {error_msg}",
        ) from e


async def ask_claude_code_api_detailed(
    question: str, timeout: int = 30
) -> dict[str, Any]:
    """
    Ask Claude a question via Python SDK and return detailed response information.

    This function returns comprehensive information about the Claude Code SDK response,
    including session metadata, response text, and cost/usage statistics.

    Args:
        question: The question to ask Claude
        timeout: Timeout in seconds for the request (default: 30)

    Returns:
        Dictionary containing:
        - 'text': The actual response text from Claude
        - 'session_info': Session metadata (session_id, model, tools, etc.)
        - 'result_info': Cost and usage information
        - 'raw_messages': List of all raw message objects (for debugging)

    Example return value:
        {
            'text': '10',
            'session_info': {
                'session_id': 'abc123',
                'model': 'claude-sonnet-4',
                'tools': ['Task', 'Bash', 'Read', ...],
                'mcp_servers': [{'name': 'checker', 'status': 'connected'}]
            },
            'result_info': {
                'duration_ms': 2801,
                'cost_usd': 0.058779,
                'usage': {'input_tokens': 4, 'output_tokens': 5, ...}
            },
            'raw_messages': [SystemMessage(...), AssistantMessage(...), ResultMessage(...)]
        }

    Raises:
        asyncio.TimeoutError: If the request times out
        Exception: Various exceptions from the SDK
    """
    options = _create_claude_client()

    # Import message types for proper type checking
    try:
        from claude_code_sdk import (
            AssistantMessage,
            ResultMessage,
            SystemMessage,
            TextBlock,
        )
    except ImportError:
        # Fallback to string-based type checking if imports fail
        AssistantMessage = None  # type: ignore[assignment,misc]
        TextBlock = None  # type: ignore[assignment,misc]
        SystemMessage = None  # type: ignore[assignment,misc]
        ResultMessage = None  # type: ignore[assignment,misc]

    # Use asyncio timeout to respect the timeout parameter
    async def _query_with_timeout() -> dict[str, Any]:
        response_parts = []
        session_info: dict[str, Any] = {}
        result_info: dict[str, Any] = {}
        raw_messages = []

        async for message in query(prompt=question, options=options):
            raw_messages.append(message)

            # Handle different message types according to SDK documentation
            if AssistantMessage is not None and isinstance(message, AssistantMessage):
                # AssistantMessage contains content blocks (TextBlock, ToolUseBlock, etc.)
                for block in message.content:
                    if TextBlock is not None and isinstance(block, TextBlock):
                        response_parts.append(block.text)

            elif SystemMessage is not None and isinstance(message, SystemMessage):
                # SystemMessage contains session metadata
                session_info.update(
                    {
                        "session_id": getattr(message, "session_id", None),
                        "model": (
                            message.data.get("model")
                            if hasattr(message, "data")
                            else None
                        ),
                        "tools": (
                            message.data.get("tools", [])
                            if hasattr(message, "data")
                            else []
                        ),
                        "mcp_servers": (
                            message.data.get("mcp_servers", [])
                            if hasattr(message, "data")
                            else []
                        ),
                        "cwd": (
                            message.data.get("cwd")
                            if hasattr(message, "data")
                            else None
                        ),
                        "api_key_source": (
                            message.data.get("apiKeySource")
                            if hasattr(message, "data")
                            else None
                        ),
                    }
                )

            elif ResultMessage is not None and isinstance(message, ResultMessage):
                # ResultMessage contains cost and usage information
                result_info.update(
                    {
                        "duration_ms": getattr(message, "duration_ms", None),
                        "duration_api_ms": getattr(message, "duration_api_ms", None),
                        "cost_usd": getattr(message, "total_cost_usd", None),
                        "usage": getattr(message, "usage", None),
                        "result": getattr(message, "result", None),
                        "num_turns": getattr(message, "num_turns", None),
                        "is_error": getattr(message, "is_error", False),
                    }
                )

            else:
                # Fallback for unknown message types or when imports failed
                message_type = type(message).__name__

                if message_type == "AssistantMessage":
                    # Handle AssistantMessage without import
                    if hasattr(message, "content"):
                        for content_block in message.content:
                            if hasattr(content_block, "text"):
                                response_parts.append(content_block.text)

        return {
            "text": "".join(response_parts).strip(),
            "session_info": session_info,
            "result_info": result_info,
            "raw_messages": raw_messages,
        }

    try:
        return await asyncio.wait_for(_query_with_timeout(), timeout)
    except asyncio.TimeoutError as exc:
        raise subprocess.TimeoutExpired(
            ["claude-code-sdk", "query"],
            timeout,
            f"Claude Code SDK request timed out after {timeout} seconds",
        ) from exc


def ask_claude_code_api_detailed_sync(
    question: str, timeout: int = 30
) -> dict[str, Any]:
    """
    Synchronous wrapper for ask_claude_code_api_detailed.

    See ask_claude_code_api_detailed for complete documentation.

    Args:
        question: The question to ask Claude
        timeout: Timeout in seconds for the request (default: 30)

    Returns:
        Dictionary with detailed response information

    Raises:
        subprocess.TimeoutExpired: If the request times out
        subprocess.CalledProcessError: If the SDK request fails
    """
    try:
        return asyncio.run(ask_claude_code_api_detailed(question, timeout))

    except subprocess.TimeoutExpired:
        # Re-raise timeout errors as-is for consistency with CLI version
        raise

    except Exception as e:
        # Convert other exceptions to CalledProcessError for consistency
        raise subprocess.CalledProcessError(
            1,  # Generic error code
            ["claude-code-sdk", "query"],
            output="",
            stderr=f"Claude Code SDK detailed request failed: {str(e)}",
        ) from e
