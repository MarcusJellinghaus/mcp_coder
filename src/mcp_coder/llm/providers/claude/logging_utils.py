"""Logging utilities for LLM requests, responses, and errors."""

import logging
from typing import Any

logger = logging.getLogger(__name__)

# Import MLflow logger with graceful fallback
try:
    from ...mlflow_logger import get_mlflow_logger

    _mlflow_available = True
except ImportError:
    _mlflow_available = False
    get_mlflow_logger = None  # type: ignore


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

    # Start MLflow run if enabled
    if _mlflow_available and get_mlflow_logger is not None:
        try:
            mlflow_logger = get_mlflow_logger()
            run_name = f"{method}_{provider}_{session_status.strip('[]')}"
            tags = {
                "conversation.method": method,
                "conversation.provider": provider,
                "conversation.session_type": session_status.strip("[]"),
            }
            mlflow_logger.start_run(run_name=run_name, tags=tags)
        except Exception as e:
            logger.debug(f"Failed to start MLflow run: {e}")


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

    # Log metrics to MLflow if enabled
    if _mlflow_available and get_mlflow_logger is not None:
        try:
            mlflow_logger = get_mlflow_logger()
            metrics = {"duration_ms": float(duration_ms)}
            if cost_usd is not None:
                metrics["cost_usd"] = float(cost_usd)
            if num_turns is not None:
                metrics["num_turns"] = float(num_turns)

            mlflow_logger.log_metrics(metrics)

            # Log usage metrics if available
            if usage:
                usage_metrics = {}
                for key, value in usage.items():
                    if isinstance(value, (int, float)):
                        usage_metrics[f"usage_{key}"] = float(value)
                if usage_metrics:
                    mlflow_logger.log_metrics(usage_metrics)

            # End the run with success status
            mlflow_logger.end_run("FINISHED")
        except Exception as e:
            logger.debug(f"Failed to log MLflow response metrics: {e}")


# Maximum characters to include from subprocess stdout/stderr in error logs
_MAX_OUTPUT_CHARS = 1000


def log_llm_error(
    method: str,
    error: Exception,
    duration_ms: int | None = None,
) -> None:
    """Log LLM error at DEBUG level.

    For CalledProcessError, also logs stdout and stderr to help diagnose
    CLI failures (e.g., authentication errors, MCP server issues).

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

    # For CalledProcessError, include stdout and stderr for diagnosis
    if hasattr(error, "stderr") and error.stderr:
        stderr_str = str(error.stderr).strip()
        if len(stderr_str) > _MAX_OUTPUT_CHARS:
            stderr_str = stderr_str[:_MAX_OUTPUT_CHARS] + "... (truncated)"
        log_lines.append(f"  stderr: {stderr_str}")

    if hasattr(error, "output") and error.output:
        stdout_str = str(error.output).strip()
        if len(stdout_str) > _MAX_OUTPUT_CHARS:
            stdout_str = stdout_str[:_MAX_OUTPUT_CHARS] + "... (truncated)"
        log_lines.append(f"  stdout: {stdout_str}")

    log_message = "\n".join(log_lines)
    logger.debug(log_message)

    # Log error to MLflow if enabled
    if _mlflow_available and get_mlflow_logger is not None:
        try:
            mlflow_logger = get_mlflow_logger()
            mlflow_logger.log_error_metrics(error, duration_ms)
            mlflow_logger.end_run("FAILED")
        except Exception as e:
            logger.debug(f"Failed to log MLflow error: {e}")
