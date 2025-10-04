"""CLI utility functions for shared parameter handling.

This module provides utilities that are shared across CLI commands
for parameter parsing and conversion.
"""

from ..llm.session import parse_llm_method

__all__ = [
    "parse_llm_method_from_args",
]


def parse_llm_method_from_args(llm_method: str) -> tuple[str, str]:
    """Parse CLI llm_method into provider, method for internal APIs.

    Args:
        llm_method: CLI parameter ('claude_code_cli' or 'claude_code_api')

    Returns:
        Tuple of (provider, method) for internal API usage

    Raises:
        ValueError: If llm_method is not supported

    Example:
        >>> provider, method = parse_llm_method_from_args("claude_code_api")
        >>> print(provider, method)
        claude api
    """
    return parse_llm_method(llm_method)
