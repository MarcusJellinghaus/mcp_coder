"""MCP Coder - An MCP server for code analysis and development tasks."""

from .claude_client import ask_claude
from .llm_interface import ask_llm
from .claude_executable_finder import find_claude_executable, verify_claude_installation
from .subprocess_runner import (
    CommandOptions,
    CommandResult,
    execute_command,
    execute_subprocess,
)

__version__ = "0.1.0"

__all__ = [
    "execute_command",
    "execute_subprocess",
    "CommandResult",
    "CommandOptions",
    "ask_claude",
    "ask_llm",
    "find_claude_executable",
    "verify_claude_installation",
]
