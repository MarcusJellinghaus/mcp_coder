"""Session management and LLM method resolution utilities.

This module provides utilities for resolving session parameters and
parsing LLM method strings into provider/method tuples.
"""

__all__ = [
    "parse_llm_method",
]


def parse_llm_method(llm_method: str) -> tuple[str, str]:
    """Parse llm_method parameter into provider and method.

    Args:
        llm_method: Either 'claude_code_cli' or 'claude_code_api'

    Returns:
        Tuple of (provider, method)
        - provider: "claude"
        - method: "cli" or "api"

    Raises:
        ValueError: If llm_method is not supported

    Example:
        >>> provider, method = parse_llm_method("claude_code_api")
        >>> print(provider, method)
        claude api

        >>> provider, method = parse_llm_method("claude_code_cli")
        >>> print(provider, method)
        claude cli
    """
    if llm_method == "claude_code_cli":
        return "claude", "cli"
    elif llm_method == "claude_code_api":
        return "claude", "api"
    else:
        raise ValueError(
            f"Unsupported llm_method: {llm_method}. "
            f"Supported: 'claude_code_cli', 'claude_code_api'"
        )
