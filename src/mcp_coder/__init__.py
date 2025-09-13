"""MCP Coder - An MCP server for code analysis and development tasks."""

from .subprocess_runner import execute_command, execute_subprocess, CommandResult, CommandOptions
from .claude_client import ask_claude

__version__ = "0.1.0"

__all__ = [
    "execute_command",
    "execute_subprocess", 
    "CommandResult",
    "CommandOptions",
    "ask_claude",
]
