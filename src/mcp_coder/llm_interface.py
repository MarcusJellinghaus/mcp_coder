"""High-level LLM interface for extensible provider support."""

from .llm_providers.claude.claude_code_interface import ask_claude_code


def ask_llm(
    question: str,
    provider: str = "claude",
    method: str = "cli",
    session_id: str | None = None,
    timeout: int = 30,
    cwd: str | None = None,
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
        cwd: Working directory for the command (only used for CLI method)
             This is important for Claude to find .claude/settings.local.json

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
            question, method=method, session_id=session_id, timeout=timeout, cwd=cwd
        )
    else:
        raise ValueError(
            f"Unsupported provider: {provider}. Currently supported: 'claude'"
        )
