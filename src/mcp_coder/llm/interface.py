"""High-level LLM interface for extensible provider support."""

import asyncio
import logging
import os

from mcp_coder.utils.subprocess_runner import TimeoutExpired

from .mlflow_conversation_logger import mlflow_conversation
from .providers.claude.claude_code_cli import ask_claude_code_cli

# Serialization functions are now in .serialization module
from .types import LLMResponseDict

logger = logging.getLogger(__name__)

# Constants
LLM_DEFAULT_TIMEOUT_SECONDS = 30  # Default timeout for LLM requests

__all__ = [
    "prompt_llm",
]


def prompt_llm(
    question: str,
    provider: str = "claude",
    session_id: str | None = None,
    timeout: int = LLM_DEFAULT_TIMEOUT_SECONDS,
    env_vars: dict[str, str] | None = None,
    execution_dir: str | None = None,
    mcp_config: str | None = None,
    branch_name: str | None = None,
) -> LLMResponseDict:
    """Ask a question to an LLM provider with full session management.

    This function returns complete response data including session_id and metadata,
    enabling conversation continuity and comprehensive logging.

    Args:
        question: The question to ask the LLM
        provider: The LLM provider to use ("claude" or "langchain")
        session_id: Optional session ID to resume previous conversation
        timeout: Timeout in seconds for the request (default: 30)
        env_vars: Optional environment variables to pass to the LLM subprocess.
            MCP server configuration (e.g. MCP_CODER_PROJECT_DIR) is passed here
            via prepare_llm_environment(); see execution_dir for MCP discovery.
        execution_dir: Working directory for the LLM subprocess. Claude discovers
            .mcp.json (and therefore which MCP servers to load) relative to this
            directory. Defaults to the caller's current working directory.
        mcp_config: Optional path to MCP configuration file
        branch_name: Optional git branch name to include in log filename

    Returns:
        LLMResponseDict containing:
        - version: Serialization format version
        - timestamp: ISO format timestamp
        - text: The response text
        - session_id: Session ID for conversation continuity
        - provider: LLM provider name ("claude" or "langchain")
        - raw_response: Complete metadata (duration, cost, usage, etc.)

    Raises:
        ValueError: If the provider is not supported, or if input validation fails
        TimeoutExpired: If the Claude CLI subprocess times out
        TimeoutError: If the LangChain provider times out (asyncio.TimeoutError)

    Examples:
        >>> # Start new conversation
        >>> result = prompt_llm("My favorite color is blue")
        >>> print(result["text"])
        >>> session_id = result["session_id"]

        >>> # Continue conversation
        >>> result2 = prompt_llm("What's my favorite color?", session_id=session_id)
        >>> print(result2["text"])  # "Your favorite color is blue"

        >>> # Access metadata
        >>> print(f"Cost: ${result2['raw_response'].get('cost_usd', 0)}")
        >>> print(f"Duration: {result2['raw_response'].get('duration_ms')}ms")

    Note:
        For simple text-only responses, use ``prompt_llm(...)["text"]``.
        This function is designed for:
        - Conversation continuity across multiple turns
        - Comprehensive logging and analysis
        - Cost tracking and usage monitoring
        - Parallel usage safety (each conversation has unique session_id)
    """
    # Input validation
    if not question or not question.strip():
        raise ValueError("Question cannot be empty or whitespace only")

    if timeout <= 0:
        raise ValueError("Timeout must be a positive number")

    # Allow env var to override the provider parameter (e.g. in CI)
    provider = os.environ.get("MCP_CODER_LLM_PROVIDER") or provider

    # Unsupported provider check — before context manager (no MLflow run needed)
    if provider not in ("claude", "langchain"):
        raise ValueError(
            f"Unsupported provider: {provider}. Supported: 'claude', 'langchain'"
        )

    metadata = {"branch_name": branch_name, "working_directory": execution_dir}

    with mlflow_conversation(question, provider, session_id, metadata) as mlflow_ctx:
        if provider == "langchain":
            from .providers.langchain import (  # lazy import  # noqa: PLC0415
                ask_langchain,
            )

            try:
                response = ask_langchain(
                    question,
                    session_id=session_id,
                    timeout=timeout,
                    mcp_config=mcp_config,
                    execution_dir=execution_dir,
                    env_vars=env_vars,
                )
            except asyncio.TimeoutError:
                logger.error("LLM request timed out after %ds", timeout)
                logger.error(
                    "Prompt length: %d characters (%d words)",
                    len(question),
                    len(question.split()),
                )
                logger.error("LLM provider: %s", provider)
                logger.error(
                    "Consider: checking network, simplifying prompt, increasing timeout"
                )
                raise
        else:
            # Claude provider — always uses CLI
            try:
                response = ask_claude_code_cli(
                    question,
                    session_id=session_id,
                    timeout=timeout,
                    env_vars=env_vars,
                    cwd=execution_dir,
                    mcp_config=mcp_config,
                    branch_name=branch_name,
                )
            except TimeoutExpired:
                logger.error("LLM request timed out after %ds", timeout)
                logger.error(
                    "Prompt length: %d characters (%d words)",
                    len(question),
                    len(question.split()),
                )
                logger.error("LLM provider: %s", provider)
                logger.error(
                    "Consider: checking network, simplifying prompt, increasing timeout"
                )
                raise

        mlflow_ctx["response_data"] = response

    return response
