"""Type definitions for LLM responses and serialization.

This module provides TypedDict definitions and constants for structured
LLM responses with session management and versioned serialization support.
"""

from typing import TypedDict

__all__ = [
    "LLMResponseDict",
    "LLM_RESPONSE_VERSION",
]


class LLMResponseDict(TypedDict):
    """Structured LLM response with session and serialization support.

    This TypedDict defines the complete structure for LLM responses that include
    session management, timestamps, and raw response data for comprehensive logging.

    Attributes:
        version: Serialization format version (e.g., "1.0")
        timestamp: ISO format timestamp when response was created
        text: The actual text response from the LLM
        session_id: Unique session identifier for conversation continuity.
                   None if session ID is not available or not provided by LLM.
        method: LLM communication method ("cli" or "api")
        provider: LLM provider name (e.g., "claude")
        raw_response: Complete unmodified response data from CLI JSON or API
                     This preserves all metadata, usage stats, and provider-specific
                     information for future analysis and parsing

    Example:
        {
            "version": "1.0",
            "timestamp": "2025-10-01T10:30:00.123456",
            "text": "Python is a programming language...",
            "session_id": "550e8400-e29b-41d4-a716-446655440000",
            "method": "cli",
            "provider": "claude",
            "raw_response": {
                "duration_ms": 2801,
                "cost_usd": 0.058,
                ...
            }
        }
    """

    version: str
    timestamp: str
    text: str
    session_id: str | None
    method: str
    provider: str
    raw_response: dict[str, object]


# Current serialization version
# Version numbering:
# - Major version (X.0): Breaking changes to structure
# - Minor version (1.X): Backward-compatible additions
LLM_RESPONSE_VERSION = "1.0"
