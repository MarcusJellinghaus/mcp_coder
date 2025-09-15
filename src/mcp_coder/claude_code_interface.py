"""Claude Code interface with routing between different implementation methods."""

from .claude_code_api import ask_claude_code_api
from .claude_code_cli import ask_claude_code_cli


def ask_claude_code(question: str, method: str = "cli", timeout: int = 30) -> str:
    """
    Ask Claude a question using the specified implementation method.

    Routes between different Claude Code implementation methods (CLI, API, etc.).
    Supports both CLI and Python SDK (API) methods.

    Args:
        question: The question to ask Claude
        method: The implementation method to use ("cli" or "api")
        timeout: Timeout in seconds for the request (default: 30)

    Returns:
        Claude's response as a string

    Raises:
        ValueError: If the method is not supported
        Various exceptions from underlying implementations (e.g., subprocess errors for CLI)

    Examples:
        >>> # Use CLI method
        >>> response = ask_claude_code("Explain recursion", method="cli")
        >>> print(response)
        
        >>> # Use API method (recommended)
        >>> response = ask_claude_code("Review this function", method="api")
        >>> print(response)
        
        >>> # Default method (CLI)
        >>> response = ask_claude_code("Optimize this code")
        >>> print(response)
    """
    if method == "cli":
        return ask_claude_code_cli(question, timeout=timeout)
    elif method == "api":
        return ask_claude_code_api(question, timeout=timeout)
    else:
        raise ValueError(
            f"Unsupported method: {method}. Supported methods: 'cli', 'api'"
        )
