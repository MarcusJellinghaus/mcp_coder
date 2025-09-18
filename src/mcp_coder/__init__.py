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

from .cli.commands.commit import execute_commit_auto, execute_commit_clipboard
from .cli.commands.help import execute_help
from .cli.main import main as cli_main
from .llm_interface import ask_llm
from .llm_providers.claude.claude_client import ask_claude
from .llm_providers.claude.claude_code_interface import ask_claude_code
from .llm_providers.claude.claude_executable_finder import (
    find_claude_executable,
    verify_claude_installation,
)
from .log_utils import setup_logging
from .prompt_manager import (
    get_prompt,
    validate_prompt_directory,
    validate_prompt_markdown,
)
from .utils.git_operations import (
    CommitResult,
    commit_all_changes,
    commit_staged_files,
    get_full_status,
    is_git_repository,
)
from .utils.subprocess_runner import (
    CommandOptions,
    CommandResult,
    execute_command,
    execute_subprocess,
)

__version__ = "0.1.0"

__all__ = [
    # CLI interface
    "cli_main",
    "execute_help",
    "execute_commit_auto",
    "execute_commit_clipboard",
    # Core LLM interfaces
    "ask_claude",
    "ask_claude_code",
    "ask_llm",
    # Claude executable utilities
    "find_claude_executable",
    "verify_claude_installation",
    # Command execution
    "execute_command",
    "execute_subprocess",
    "CommandResult",
    "CommandOptions",
    # Git operations - Public API
    "CommitResult",
    "commit_all_changes",
    "commit_staged_files",
    "get_full_status",
    "is_git_repository",
    # Prompt management
    "get_prompt",
    "validate_prompt_markdown",
    "validate_prompt_directory",
    # Logging utilities
    "setup_logging",
]
