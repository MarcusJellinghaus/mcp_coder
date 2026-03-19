"""Session management and LLM method resolution utilities.

This module provides utilities for resolving session parameters and
parsing LLM method strings into provider names.
"""

__all__ = [
    "parse_llm_method",
]


def parse_llm_method(llm_method: str) -> str:
    """Parse llm_method parameter into a provider name.

    Args:
        llm_method: One of 'claude_code_cli' or 'langchain'

    Returns:
        Provider name: "claude" or "langchain"

    Raises:
        ValueError: If llm_method is not supported

    Example:
        >>> provider = parse_llm_method("claude_code_cli")
        >>> print(provider)
        claude

        >>> provider = parse_llm_method("langchain")
        >>> print(provider)
        langchain
    """
    if llm_method == "claude_code_cli":
        return "claude"
    elif llm_method == "langchain":
        return "langchain"
    else:
        raise ValueError(
            f"Unsupported llm_method: {llm_method}. "
            f"Supported: 'claude_code_cli', 'langchain'"
        )
