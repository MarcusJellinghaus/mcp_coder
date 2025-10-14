"""Claude Code interface with routing between different implementation methods."""

from .claude_code_api import ask_claude_code_api
from .claude_code_cli import ask_claude_code_cli


def ask_claude_code(  # pylint: disable=too-many-positional-arguments
    question: str,
    method: str = "cli",
    session_id: str | None = None,
    timeout: int = 30,
    env_vars: dict[str, str] | None = None,
    cwd: str | None = None,
) -> str:
    """
    Ask Claude a question using the specified implementation method.

    Routes between different Claude Code implementation methods (CLI, API, etc.).
    Supports both CLI and Python SDK (API) methods with session continuity.

    This function returns only the text response. For full session information
    and metadata, use the lower-level functions directly or use prompt_llm().

    Args:
        question: The question to ask Claude
        method: The implementation method to use ("cli" or "api")
        session_id: Optional session ID to resume previous conversation
        timeout: Timeout in seconds for the request (default: 30)
        env_vars: Optional environment variables to pass to the LLM subprocess
        cwd: Optional working directory for the LLM subprocess

    Returns:
        Claude's response text as a string

    Raises:
        ValueError: If the method is not supported or if input validation fails
        Various exceptions from underlying implementations (e.g., subprocess errors for CLI)

    Examples:
        >>> # Simple usage without session
        >>> response = ask_claude_code("Explain recursion")
        >>> print(response)

        >>> # With session continuity (text-only, session_id managed externally)
        >>> response1 = ask_claude_code("My color is blue")
        >>> # Note: session_id not available from this function
        >>> # Use ask_claude_code_cli/api directly or prompt_llm() for session management
    """
    # Input validation
    if not question or not question.strip():
        raise ValueError("Question cannot be empty or whitespace only")

    if timeout <= 0:
        raise ValueError("Timeout must be a positive number")

    if method == "cli":
        result = ask_claude_code_cli(
            question, session_id=session_id, timeout=timeout, env_vars=env_vars, cwd=cwd
        )
        return result["text"]  # Extract text from LLMResponseDict
    elif method == "api":
        result = ask_claude_code_api(
            question, session_id=session_id, timeout=timeout, env_vars=env_vars, cwd=cwd
        )
        return result["text"]  # Extract text from LLMResponseDict
    else:
        raise ValueError(
            f"Unsupported method: {method}. Supported methods: 'cli', 'api'"
        )
