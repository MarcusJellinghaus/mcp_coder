"""Logging utilities for LLM requests, responses, and errors."""

import logging
from typing import Any

logger = logging.getLogger(__name__)


def log_llm_request(
    method: str,
    provider: str,
    session_id: str | None,
    prompt: str,
    timeout: int,
    env_vars: dict[str, str],
    cwd: str,
    command: list[str] | None = None,
    mcp_config: str | None = None,
) -> None:
    """Log LLM request details at DEBUG level.

    Args:
        method: 'cli' or 'api'
        provider: 'claude'
        session_id: Session ID or None for new session
        prompt: The prompt being sent
        timeout: Timeout in seconds
        env_vars: Environment variables
        cwd: Current working directory
        command: CLI command (for CLI method only)
        mcp_config: MCP config path (optional)
    """
    session_status = "[new]" if session_id is None else "[resuming]"
    prompt_preview = f"{len(prompt)} chars"
    if len(prompt) > 250:
        prompt_preview += f" - {prompt[:250]}..."
    else:
        prompt_preview += f" - {prompt}"

    log_lines = [
        f"LLM Request (method={method}, provider={provider}, session={session_status})",
        f"  prompt: {prompt_preview}",
        f"  timeout: {timeout}s",
        f"  cwd: {cwd}",
        f"  mcp_config: {mcp_config}",
    ]

    if command is not None:
        log_lines.insert(3, f"  command: {' '.join(command)}")

    if env_vars:
        env_str = ", ".join(f"{k}={v}" for k, v in env_vars.items())
        log_lines.append(f"  env_vars: {env_str}")

    log_message = "\n".join(log_lines)
    logger.debug(log_message)


def log_llm_response(
    method: str,
    duration_ms: int,
    cost_usd: float | None = None,
    usage: dict[str, Any] | None = None,
    num_turns: int | None = None,
) -> None:
    """Log LLM response metadata at DEBUG level.

    Args:
        method: 'cli' or 'api'
        duration_ms: Duration in milliseconds
        cost_usd: Cost in USD (API only)
        usage: Usage metadata (API only)
        num_turns: Number of turns (API only)
    """
    log_lines = [f"LLM Response (method={method})"]
    log_lines.append(f"  duration: {duration_ms}ms")

    if cost_usd is not None:
        log_lines.append(f"  cost: ${cost_usd:.4f}")

    if usage is not None:
        usage_str = ", ".join(f"{k}={v}" for k, v in usage.items())
        log_lines.append(f"  usage: {usage_str}")

    if num_turns is not None:
        log_lines.append(f"  turns: {num_turns}")

    log_message = "\n".join(log_lines)
    logger.debug(log_message)


def log_llm_error(
    method: str,
    error: Exception,
    duration_ms: int | None = None,
) -> None:
    """Log LLM error at DEBUG level.

    Args:
        method: 'cli' or 'api'
        error: The exception that occurred
        duration_ms: Duration before error (optional)
    """
    error_type = type(error).__name__
    error_msg = str(error)

    log_lines = [f"LLM Error (method={method})"]
    log_lines.append(f"  error_type: {error_type}")
    log_lines.append(f"  error_message: {error_msg}")

    if duration_ms is not None:
        log_lines.append(f"  duration: {duration_ms}ms")

    log_message = "\n".join(log_lines)
    logger.debug(log_message)
