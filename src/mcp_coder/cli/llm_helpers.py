"""CLI utilities for LLM parameter handling."""


def parse_llm_method(llm_method: str) -> tuple[str, str]:
    """Parse llm_method parameter into provider and method.

    Args:
        llm_method: Either 'claude_code_cli' or 'claude_code_api'

    Returns:
        Tuple of (provider, method)

    Raises:
        ValueError: If llm_method is not supported
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
