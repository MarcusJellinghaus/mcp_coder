"""High-level LLM interface for extensible provider support."""

from .claude_code_interface import ask_claude_code


def ask_llm(question: str, provider: str = "claude", method: str = "cli", timeout: int = 30) -> str:
    """
    Ask a question to an LLM provider using the specified method.

    This is the main entry point for LLM interactions, designed to be extensible
    for multiple providers and implementation methods.

    Args:
        question: The question to ask the LLM
        provider: The LLM provider to use (currently only "claude" is supported)
        method: The implementation method to use ("cli" for now, "api" coming soon)
        timeout: Timeout in seconds for the request (default: 30)

    Returns:
        The LLM's response as a string

    Raises:
        ValueError: If the provider or method is not supported
        Various exceptions from underlying implementations (e.g., subprocess errors)

    Example:
        >>> response = ask_llm("What is Python?", provider="claude", method="cli")
        >>> print(response)
    """
    if provider == "claude":
        return ask_claude_code(question, method=method, timeout=timeout)
    else:
        raise ValueError(f"Unsupported provider: {provider}. Currently supported: 'claude'")
