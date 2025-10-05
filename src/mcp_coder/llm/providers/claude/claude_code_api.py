#!/usr/bin/env python3
"""Claude Code Python SDK implementation for programmatic interaction."""

import asyncio
import json
import logging
import os
import subprocess
import time
from datetime import datetime
from typing import Any, Callable, Optional, Tuple

from claude_code_sdk import (
    AssistantMessage,
    ClaudeCodeOptions,
    ResultMessage,
    SystemMessage,
    TextBlock,
    UserMessage,
    query,
)
from claude_code_sdk._errors import CLINotFoundError

from ...types import LLM_RESPONSE_VERSION, LLMResponseDict
from .claude_executable_finder import (
    find_claude_executable,
    setup_claude_path,
    verify_claude_installation,
)


class ClaudeAPIError(Exception):
    """Custom exception for Claude API errors with user-friendly messages."""

    pass


# Create logger for this module
logger = logging.getLogger(__name__)

# Export the classes that tests need to import
__all__ = [
    "AssistantMessage",
    "TextBlock",
    "SystemMessage",
    "ResultMessage",
    "UserMessage",
    "ClaudeCodeOptions",
    "query",
    "ask_claude_code_api",
    "ask_claude_code_api_detailed",
    "ask_claude_code_api_detailed_sync",
    "create_api_response_dict",
    "_ask_claude_code_api_async",
    "_create_claude_client",
    "_extract_real_error_message",
    "_verify_claude_before_use",
    "ClaudeAPIError",
]


def _extract_real_error_message(exception: Exception) -> str:
    """Extract the real, actionable error message from nested exceptions.

    Args:
        exception: The exception to analyze

    Returns:
        A clear, actionable error message for the user
    """
    # Start with the base exception message
    error_msg = str(exception)

    # Check for nested exceptions via __cause__ chain
    current_exc: Optional[BaseException] = exception
    error_details = []

    # Walk up the exception chain to find the root cause
    while current_exc:
        exc_type = type(current_exc).__name__
        exc_msg = str(current_exc)

        # Look for specific error patterns we care about
        if "WinError 206" in exc_msg or "filename or extension is too long" in exc_msg:
            error_details.append("Windows path length limit exceeded (WinError 206)")
            error_details.append(
                "This often happens when the current working directory path is very long"
            )
            break
        elif "CLINotFoundError" in exc_type or "Claude Code not found" in exc_msg:
            error_details.append(f"Claude CLI executable not found: {exc_msg}")
            break
        elif "FileNotFoundError" in exc_type:
            error_details.append(f"File/executable not found: {exc_msg}")
            break
        elif "PermissionError" in exc_type:
            error_details.append(f"Permission denied: {exc_msg}")
            break
        elif "OSError" in exc_type and exc_msg:
            error_details.append(f"System error: {exc_msg}")
            break

        # Move to the next exception in the chain
        current_exc = getattr(current_exc, "__cause__", None)

        # Avoid infinite loops
        if len(error_details) > 5:
            break

    # If we found specific error details, use them
    if error_details:
        return " | ".join(error_details)

    # Otherwise return the original message
    return error_msg


def _verify_claude_before_use() -> Tuple[bool, Optional[str], Optional[str]]:
    """Verify Claude installation before attempting to use it.

    Returns:
        Tuple of (success, claude_path, error_message)
    """
    logger.debug("Verifying Claude installation before use")

    try:
        # First try to setup the PATH
        claude_path = setup_claude_path()
        if claude_path:
            logger.debug("Claude CLI found and PATH configured: %s", claude_path)
        else:
            logger.warning(
                "setup_claude_path() returned None - Claude not found in standard locations"
            )
    except Exception as e:
        logger.warning("Error during PATH setup: %s", e)
        claude_path = None

    # Run detailed verification
    verification_result = verify_claude_installation()

    logger.debug("Claude verification result: %s", verification_result)

    if verification_result["found"] and verification_result["works"]:
        return True, verification_result["path"], None
    else:
        error_msg = verification_result.get("error", "Claude CLI verification failed")

        # If verification failed but we found Claude, provide more helpful error message
        if verification_result["found"] and verification_result["path"]:
            detailed_error = f"Claude found at {verification_result['path']} but version check failed: {error_msg}"
            logger.warning("Claude verification detailed error: %s", detailed_error)
            return False, verification_result.get("path"), detailed_error

        return False, verification_result.get("path"), error_msg


def _retry_with_backoff(
    func: Callable[[], Any], max_retries: int = 3, base_delay: float = 1.0
) -> Any:
    """Retry a function with exponential backoff.

    Args:
        func: Function to retry (should be callable with no args)
        max_retries: Maximum number of retry attempts
        base_delay: Base delay in seconds for exponential backoff

    Returns:
        Result of the successful function call

    Raises:
        The last exception if all retries fail
    """
    last_exception: Optional[Exception] = None

    for attempt in range(max_retries + 1):  # +1 for initial attempt
        try:
            logger.debug(
                "Attempt %d/%d for function %s",
                attempt + 1,
                max_retries + 1,
                func.__name__ if hasattr(func, "__name__") else "callable",
            )
            result = func()
            if attempt > 0:
                logger.debug("Function succeeded on attempt %d", attempt + 1)
            return result
        except Exception as e:
            last_exception = e

            if attempt < max_retries:  # Don't sleep after the last attempt
                delay = base_delay * (2**attempt)  # Exponential backoff
                logger.warning(
                    "Attempt %d failed: %s. Retrying in %.1f seconds...",
                    attempt + 1,
                    str(e),
                    delay,
                )
                time.sleep(delay)
            else:
                logger.error(
                    "All %d attempts failed. Final error: %s", max_retries + 1, str(e)
                )

    # If we get here, all retries failed
    if last_exception is not None:
        raise last_exception
    else:
        raise RuntimeError("All retry attempts failed with no exception recorded")


def _create_claude_client(session_id: str | None = None) -> ClaudeCodeOptions:
    """Create a Claude Code SDK client with optional session resumption.

    Args:
        session_id: Optional Claude session ID to resume conversation

    Returns:
        ClaudeCodeOptions object configured for basic usage or session resumption

    Note:
        The SDK will use existing CLI subscription authentication automatically.
        Attempts to setup PATH if Claude CLI is not accessible.

    Raises:
        RuntimeError: If Claude CLI cannot be found or verified
    """
    logger.debug("Creating Claude Code SDK client")

    # Verify Claude installation before creating client
    success, claude_path, error_msg = _verify_claude_before_use()

    if not success:
        logger.error("Claude verification failed: %s", error_msg)
        raise RuntimeError(f"Claude CLI verification failed: {error_msg}")

    logger.debug("Claude CLI verified successfully at: %s", claude_path)

    # Use basic configuration with optional session resumption
    if session_id:
        logger.debug(f"Resuming session: {session_id}")
        return ClaudeCodeOptions(resume=session_id)
    else:
        return ClaudeCodeOptions()


def create_api_response_dict(
    text: str, session_id: str | None, detailed_response: dict[str, Any]
) -> LLMResponseDict:
    """Create LLMResponseDict from API detailed response.

    Args:
        text: Extracted response text
        session_id: Session ID from session_info
        detailed_response: Complete response from ask_claude_code_api_detailed_sync()

    Returns:
        Complete LLMResponseDict
    """
    return {
        "version": LLM_RESPONSE_VERSION,
        "timestamp": datetime.now().isoformat(),
        "text": text,
        "session_id": session_id,
        "method": "api",
        "provider": "claude",
        "raw_response": {
            "session_info": detailed_response["session_info"],
            "result_info": detailed_response["result_info"],
            "raw_messages": detailed_response["raw_messages"],
        },
    }


async def _ask_claude_code_api_async(
    question: str, timeout: float = 30.0, session_id: str | None = None
) -> str:
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
        session_id: Optional Claude session ID to resume conversation

    Returns:
        Claude's response as a string (concatenated text from all TextBlocks)

    Raises:
        ValueError: If input validation fails
        asyncio.TimeoutError: If the request times out
        Exception: Various exceptions from the SDK
    """
    # Input validation
    if not question or not question.strip():
        raise ValueError("Question cannot be empty or whitespace only")

    if timeout <= 0:
        raise ValueError("Timeout must be a positive number")

    options = _create_claude_client(session_id)

    # Message types are now available at module level

    # Use asyncio timeout to respect the timeout parameter
    async def _query_with_timeout() -> str:
        response_parts = []
        session_info: dict[str, Any] = {}
        result_info: dict[str, Any] = {}

        async for message in query(prompt=question, options=options):
            # Handle different message types according to SDK documentation
            if isinstance(message, AssistantMessage):
                # AssistantMessage contains content blocks (TextBlock, ToolUseBlock, etc.)
                for block in message.content:
                    if isinstance(block, TextBlock):
                        response_parts.append(block.text)

            elif isinstance(message, SystemMessage):
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

            elif isinstance(message, ResultMessage):
                # ResultMessage contains cost and usage information
                result_info.update(
                    {
                        "duration_ms": getattr(message, "duration_ms", None),
                        "cost_usd": getattr(message, "total_cost_usd", None),
                        "usage": getattr(message, "usage", None),
                        "result": getattr(message, "result", None),
                    }
                )

        # Session and result info are collected but not printed in production

        return "".join(response_parts).strip()

    try:
        return await asyncio.wait_for(_query_with_timeout(), timeout)
    except asyncio.TimeoutError as exc:
        raise subprocess.TimeoutExpired(
            ["claude-code-sdk", "query"],
            timeout,
        ) from exc


def ask_claude_code_api(
    question: str, session_id: str | None = None, timeout: float = 30.0
) -> LLMResponseDict:
    """
    Ask Claude a question via Python SDK with native session support.

    Uses Claude's native session resumption via the resume parameter.
    Session continuity is handled by Claude Code SDK - no manual history management needed.

    Args:
        question: The question to ask Claude
        session_id: Optional Claude session ID to resume conversation
        timeout: Timeout in seconds for the request (default: 30)

    Returns:
        LLMResponseDict with complete response data including session_id

    Raises:
        ValueError: If input validation fails
        subprocess.TimeoutExpired: If the request times out
        subprocess.CalledProcessError: If the SDK request fails

    Examples:
        >>> # First call - get session_id from Claude
        >>> result = ask_claude_code_api("Remember: my color is blue")
        >>> session_id = result["session_id"]

        >>> # Resume conversation with Claude's session_id
        >>> result2 = ask_claude_code_api("What's my color?", session_id=session_id)
    """
    # Input validation
    if not question or not question.strip():
        raise ValueError("Question cannot be empty or whitespace only")
    if timeout <= 0:
        raise ValueError("Timeout must be a positive number")

    try:
        # Call detailed function with session_id for native resumption
        detailed = ask_claude_code_api_detailed_sync(question, timeout, session_id)

        # Extract session_id from Claude's response
        actual_session_id = detailed["session_info"].get("session_id")

        # Log warning if session IDs don't match (informational only)
        if session_id and actual_session_id and session_id != actual_session_id:
            logger.warning(
                f"Session ID mismatch: requested '{session_id}', got '{actual_session_id}' from Claude"
            )

        # Build and return response
        return create_api_response_dict(detailed["text"], actual_session_id, detailed)

    except subprocess.TimeoutExpired:
        # Re-raise timeout errors as-is
        raise

    except ValueError:
        # Re-raise input validation errors as-is
        raise

    except Exception as e:
        # Convert to ClaudeAPIError for consistency
        real_error = _extract_real_error_message(e)
        error_msg = f"Claude API Error: {real_error}"
        raise ClaudeAPIError(error_msg) from e


async def ask_claude_code_api_detailed(
    question: str, timeout: float = 30.0, session_id: str | None = None
) -> dict[str, Any]:
    """
    Ask Claude a question via Python SDK and return detailed response information.

    This function returns comprehensive information about the Claude Code SDK response,
    including session metadata, response text, and cost/usage statistics.

    Args:
        question: The question to ask Claude
        timeout: Timeout in seconds for the request (default: 30)
        session_id: Optional Claude session ID to resume conversation

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
        ValueError: If input validation fails
        asyncio.TimeoutError: If the request times out
        Exception: Various exceptions from the SDK
    """
    # Input validation
    if not question or not question.strip():
        raise ValueError("Question cannot be empty or whitespace only")

    if timeout <= 0:
        raise ValueError("Timeout must be a positive number")

    options = _create_claude_client(session_id)

    # Message types are now available at module level

    # Use asyncio timeout to respect the timeout parameter
    async def _query_with_timeout() -> dict[str, Any]:
        response_parts = []
        session_info: dict[str, Any] = {}
        result_info: dict[str, Any] = {}
        raw_messages = []

        async for message in query(prompt=question, options=options):
            raw_messages.append(message)

            # Handle different message types according to SDK documentation
            if isinstance(message, AssistantMessage):
                # AssistantMessage contains content blocks (TextBlock, ToolUseBlock, etc.)
                for block in message.content:
                    if isinstance(block, TextBlock):
                        response_parts.append(block.text)

            elif isinstance(message, SystemMessage):
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

            elif isinstance(message, ResultMessage):
                # ResultMessage contains cost and usage information + session_id
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
                # Extract session_id from ResultMessage and store in session_info
                result_session_id = getattr(message, "session_id", None)
                if result_session_id:
                    session_info["session_id"] = result_session_id

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
        ) from exc


def ask_claude_code_api_detailed_sync(
    question: str, timeout: float = 30.0, session_id: str | None = None
) -> dict[str, Any]:
    """
    Synchronous wrapper for ask_claude_code_api_detailed.

    See ask_claude_code_api_detailed for complete documentation.

    Args:
        question: The question to ask Claude
        timeout: Timeout in seconds for the request (default: 30)
        session_id: Optional Claude session ID to resume conversation

    Returns:
        Dictionary with detailed response information

    Raises:
        ValueError: If input validation fails
        subprocess.TimeoutExpired: If the request times out
        subprocess.CalledProcessError: If the SDK request fails
    """
    # Input validation is handled by ask_claude_code_api_detailed
    try:
        result = asyncio.run(
            ask_claude_code_api_detailed(question, timeout, session_id)
        )
        return result

    except subprocess.TimeoutExpired:
        # Re-raise timeout errors as-is for consistency with CLI version
        raise

    except ValueError:
        # Re-raise input validation errors as-is
        raise

    except Exception as e:
        # Convert other exceptions to CalledProcessError for consistency
        raise subprocess.CalledProcessError(
            1,  # Generic error code
            ["claude-code-sdk", "query"],
            output="",
            stderr=f"Claude Code SDK detailed request failed: {str(e)}",
        ) from e
