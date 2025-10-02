"""High-level LLM interface for extensible provider support."""

from .llm_providers.claude.claude_code_api import ask_claude_code_api
from .llm_providers.claude.claude_code_cli import ask_claude_code_cli
from .llm_providers.claude.claude_code_interface import ask_claude_code
from .llm_serialization import deserialize_llm_response, serialize_llm_response
from .llm.types import LLMResponseDict

__all__ = [
    "ask_llm",
    "prompt_llm",
    "serialize_llm_response",
    "deserialize_llm_response",
]


def ask_llm(
    question: str,
    provider: str = "claude",
    method: str = "cli",
    session_id: str | None = None,
    timeout: int = 30,
) -> str:
    """
    Ask a question to an LLM provider using the specified method.

    This is the main entry point for simple LLM interactions. It returns only
    the text response. For full session management with metadata, use prompt_llm()
    or the provider-specific functions directly.

    Args:
        question: The question to ask the LLM
        provider: The LLM provider to use (currently only "claude" is supported)
        method: The implementation method to use ("cli" or "api")
                - "cli": Uses Claude Code CLI executable (requires installation)
                - "api": Uses Claude Code Python SDK (automatic authentication)
        session_id: Optional session ID to resume previous conversation
                   Note: This function doesn't return session_id. Use prompt_llm()
                   for full session management capabilities.
        timeout: Timeout in seconds for the request (default: 30)

    Returns:
        The LLM's response text as a string

    Raises:
        ValueError: If the provider or method is not supported, or if input validation fails
        Various exceptions from underlying implementations (e.g., subprocess errors)

    Examples:
        >>> # Simple usage (backward compatible)
        >>> response = ask_llm("What is Python?")
        >>> print(response)

        >>> # With API method
        >>> response = ask_llm("Explain recursion", method="api")
        >>> print(response)

        >>> # With session (managed externally - see prompt_llm for better approach)
        >>> response = ask_llm("My color is blue", session_id="known-session-id")
        >>> # Note: session_id not returned - use prompt_llm() instead

    Note:
        For session management with access to session_id and metadata, use:
        - prompt_llm() for high-level session-aware interface
        - ask_claude_code_cli() or ask_claude_code_api() directly for provider-specific control
    """
    # Input validation
    if not question or not question.strip():
        raise ValueError("Question cannot be empty or whitespace only")

    if timeout <= 0:
        raise ValueError("Timeout must be a positive number")

    if provider == "claude":
        return ask_claude_code(
            question, method=method, session_id=session_id, timeout=timeout
        )
    else:
        raise ValueError(
            f"Unsupported provider: {provider}. Currently supported: 'claude'"
        )


def prompt_llm(
    question: str,
    provider: str = "claude",
    method: str = "cli",
    session_id: str | None = None,
    timeout: int = 30,
) -> LLMResponseDict:
    """
    Ask a question to an LLM provider with full session management.

    This function returns complete response data including session_id and metadata,
    enabling conversation continuity and comprehensive logging.

    Args:
        question: The question to ask the LLM
        provider: The LLM provider to use (currently only "claude" is supported)
        method: The implementation method to use ("cli" or "api")
                - "cli": Uses Claude Code CLI executable (requires installation)
                - "api": Uses Claude Code Python SDK (automatic authentication)
        session_id: Optional session ID to resume previous conversation
        timeout: Timeout in seconds for the request (default: 30)

    Returns:
        LLMResponseDict containing:
        - version: Serialization format version
        - timestamp: ISO format timestamp
        - text: The response text
        - session_id: Session ID for conversation continuity
        - method: Communication method used ("cli" or "api")
        - provider: LLM provider name ("claude")
        - raw_response: Complete metadata (duration, cost, usage, etc.)

    Raises:
        ValueError: If the provider or method is not supported, or if input validation fails
        Various exceptions from underlying implementations (e.g., subprocess errors)

    Examples:
        >>> # Start new conversation
        >>> result = prompt_llm("My favorite color is blue")
        >>> print(result["text"])
        >>> session_id = result["session_id"]

        >>> # Continue conversation
        >>> result2 = prompt_llm("What's my favorite color?", session_id=session_id)
        >>> print(result2["text"])  # "Your favorite color is blue"

        >>> # Save conversation for later analysis
        >>> serialize_llm_response(result2, f"logs/{session_id}.json")

        >>> # Access metadata
        >>> print(f"Cost: ${result2['raw_response'].get('cost_usd', 0)}")
        >>> print(f"Duration: {result2['raw_response'].get('duration_ms')}ms")

    Note:
        For simple text-only responses without session management, use ask_llm().
        This function is designed for:
        - Conversation continuity across multiple turns
        - Comprehensive logging and analysis
        - Cost tracking and usage monitoring
        - Parallel usage safety (each conversation has unique session_id)
    """
    # Input validation
    if not question or not question.strip():
        raise ValueError("Question cannot be empty or whitespace only")

    if timeout <= 0:
        raise ValueError("Timeout must be a positive number")

    # Route to provider-specific implementation
    # Call lower-level functions directly to get LLMResponseDict
    if provider == "claude":
        if method == "cli":
            return ask_claude_code_cli(question, session_id=session_id, timeout=timeout)
        elif method == "api":
            return ask_claude_code_api(question, session_id=session_id, timeout=timeout)
        else:
            raise ValueError(
                f"Unsupported method: {method}. Supported methods: 'cli', 'api'"
            )
    else:
        raise ValueError(
            f"Unsupported provider: {provider}. Currently supported: 'claude'"
        )
