"""MCP Coder - An AI-powered software development automation toolkit.

This package provides extensible LLM interfaces for code analysis, testing, and implementation
workflows. It supports multiple LLM providers and implementation methods.

Main Interfaces:
    ask_llm: High-level interface supporting multiple LLM providers and methods
    ask_claude: Legacy interface for Claude Code CLI (backward compatible)
    ask_claude_code: Claude-specific interface with CLI and API method routing

Example:
    >>> from mcp_coder import ask_llm
    >>> response = ask_llm("Explain recursion", provider="claude", method="api")
    >>> print(response)
    
    >>> from mcp_coder import ask_claude  # Legacy interface
    >>> response = ask_claude("Review this code")
    >>> print(response)
"""

from .claude_client import ask_claude
from .claude_code_interface import ask_claude_code
from .claude_executable_finder import find_claude_executable, verify_claude_installation
from .llm_interface import ask_llm
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
    "ask_claude_code",
    "ask_llm",
    "find_claude_executable",
    "verify_claude_installation",
]
