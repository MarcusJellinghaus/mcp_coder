"""Subprocess execution utilities — thin shim over mcp-coder-utils."""

from mcp_coder_utils.subprocess_runner import (
    MAX_STDERR_IN_ERROR,
    CalledProcessError,
    CommandOptions,
    CommandResult,
    SubprocessError,
    TimeoutExpired,
    check_tool_missing_error,
    execute_command,
    execute_subprocess,
    format_command,
    get_python_isolation_env,
    get_utf8_env,
    is_python_command,
    launch_process,
    prepare_env,
    truncate_stderr,
)

__all__ = [
    "CommandResult",
    "CommandOptions",
    "MAX_STDERR_IN_ERROR",
    "check_tool_missing_error",
    "execute_command",
    "execute_subprocess",
    "launch_process",
    "truncate_stderr",
    "prepare_env",
    "is_python_command",
    "get_python_isolation_env",
    "get_utf8_env",
    "format_command",
    "CalledProcessError",
    "SubprocessError",
    "TimeoutExpired",
]
