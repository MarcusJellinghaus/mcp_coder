"""Claude Code interface with routing between different implementation methods."""

from .claude_code_cli import ask_claude_code_cli


def ask_claude_code(question: str, method: str = "cli", timeout: int = 30) -> str:
    """
    Ask Claude a question using the specified implementation method.

    Routes between different Claude Code implementation methods (CLI, API, etc.).
    Currently supports CLI method, with API method coming in a future step.

    Args:
        question: The question to ask Claude
        method: The implementation method to use ("cli" for now, "api" coming soon)
        timeout: Timeout in seconds for the request (default: 30)

    Returns:
        Claude's response as a string

    Raises:
        ValueError: If the method is not supported
        Various exceptions from underlying implementations (e.g., subprocess errors for CLI)

    Example:
        >>> response = ask_claude_code("Explain recursion", method="cli")
        >>> print(response)
    """
    if method == "cli":
        return ask_claude_code_cli(question, timeout=timeout)
    else:
        raise ValueError(f"Unsupported method: {method}. Currently supported: 'cli'")
