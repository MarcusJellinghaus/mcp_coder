"""Claude Code interface with routing between different implementation methods."""

from .claude_code_api import ask_claude_code_api
from .claude_code_cli import ask_claude_code_cli


def ask_claude_code(
    question: str, method: str = "cli", timeout: int = 30, cwd: str | None = None
) -> str:
    """
    Ask Claude a question using the specified implementation method.

    Routes between different Claude Code implementation methods (CLI, API, etc.).
    Supports both CLI and Python SDK (API) methods.

    Args:
        question: The question to ask Claude
        method: The implementation method to use ("cli" or "api")
        timeout: Timeout in seconds for the request (default: 30)
        cwd: Working directory for the command (only used for CLI method)
             This is important for Claude to find .claude/settings.local.json

    Returns:
        Claude's response as a string

    Raises:
        ValueError: If the method is not supported or if input validation fails
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
    # Input validation
    if not question or not question.strip():
        raise ValueError("Question cannot be empty or whitespace only")

    if timeout <= 0:
        raise ValueError("Timeout must be a positive number")

    if method == "cli":
        result = ask_claude_code_cli(question, timeout=timeout, cwd=cwd)
        return result["text"]  # Extract text from LLMResponseDict
    elif method == "api":
        result = ask_claude_code_api(question, timeout=timeout)
        return result["text"]  # Extract text from LLMResponseDict
    else:
        raise ValueError(
            f"Unsupported method: {method}. Supported methods: 'cli', 'api'"
        )
