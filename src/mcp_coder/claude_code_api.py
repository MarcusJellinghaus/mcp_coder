#!/usr/bin/env python3
"""Claude Code Python SDK implementation for programmatic interaction."""

import asyncio
import subprocess
from typing import Any

try:
    from claude_code_sdk import query, ClaudeCodeOptions
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
    """
    # Use basic configuration - the SDK will handle authentication automatically
    return ClaudeCodeOptions()


async def _ask_claude_code_api_async(question: str, timeout: int = 30) -> str:
    """
    Ask Claude a question via Python SDK asynchronously.
    
    Args:
        question: The question to ask Claude
        timeout: Timeout in seconds for the request (default: 30)
        
    Returns:
        Claude's response as a string
        
    Raises:
        asyncio.TimeoutError: If the request times out
        Exception: Various exceptions from the SDK
    """
    options = _create_claude_client()
    
    # Use asyncio timeout to respect the timeout parameter
    async def _query_with_timeout() -> str:
        response_parts = []
        async for message in query(prompt=question, options=options):
            # Extract text content from the message
            if hasattr(message, 'text') and message.text:
                response_parts.append(message.text)
            elif hasattr(message, 'content') and message.content:
                response_parts.append(str(message.content))
            else:
                # Fallback: convert the entire message to string
                response_parts.append(str(message))
        
        return ''.join(response_parts).strip()
    
    try:
        return await asyncio.wait_for(_query_with_timeout(), timeout)
    except asyncio.TimeoutError:
        raise subprocess.TimeoutExpired(
            ["claude-code-sdk", "query"],
            timeout,
            f"Claude Code SDK request timed out after {timeout} seconds",
        )


def ask_claude_code_api(question: str, timeout: int = 30) -> str:
    """
    Ask Claude a question via Python SDK and return the response.
    
    This is a synchronous wrapper around the async SDK functionality.
    
    Args:
        question: The question to ask Claude
        timeout: Timeout in seconds for the request (default: 30)
        
    Returns:
        Claude's response as a string
        
    Raises:
        subprocess.TimeoutExpired: If the request times out
        subprocess.CalledProcessError: If the SDK request fails
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
        raise subprocess.CalledProcessError(
            1,  # Generic error code
            ["claude-code-sdk", "query"],
            output="",
            stderr=f"Claude Code SDK request failed: {str(e)}",
        ) from e
