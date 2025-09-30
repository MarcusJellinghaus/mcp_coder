"""High-level LLM interface for extensible provider support."""

from .llm_providers.claude.claude_code_interface import ask_claude_code


def ask_llm(
    question: str,
    provider: str = "claude",
    method: str = "cli",
    timeout: int = 30,
    cwd: str | None = None,
) -> str:
    """
    Ask a question to an LLM provider using the specified method.

    This is the main entry point for LLM interactions, designed to be extensible
    for multiple providers and implementation methods.

    Args:
        question: The question to ask the LLM
        provider: The LLM provider to use (currently only "claude" is supported)
        method: The implementation method to use ("cli" or "api")
                - "cli": Uses Claude Code CLI executable (requires installation)
                - "api": Uses Claude Code Python SDK (automatic authentication)
        timeout: Timeout in seconds for the request (default: 30)
        cwd: Working directory for the command (only used for CLI method)
             This is important for Claude to find .claude/settings.local.json

    Returns:
        The LLM's response as a string

    Raises:
        ValueError: If the provider or method is not supported, or if input validation fails
        Various exceptions from underlying implementations (e.g., subprocess errors)

    Examples:
        >>> # Use CLI method (default)
        >>> response = ask_llm("What is Python?", provider="claude", method="cli")
        >>> print(response)

        >>> # Use API method (recommended)
        >>> response = ask_llm("Explain recursion", provider="claude", method="api")
        >>> print(response)

        >>> # Default parameters
        >>> response = ask_llm("Review this code")  # Uses claude + cli
        >>> print(response)
    """
    # Input validation
    if not question or not question.strip():
        raise ValueError("Question cannot be empty or whitespace only")

    if timeout <= 0:
        raise ValueError("Timeout must be a positive number")

    if provider == "claude":
        return ask_claude_code(question, method=method, timeout=timeout, cwd=cwd)
    else:
        raise ValueError(
            f"Unsupported provider: {provider}. Currently supported: 'claude'"
        )
