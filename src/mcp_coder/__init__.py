"""MCP Coder - An AI-powered software development automation toolkit.

This package provides extensible LLM interfaces for code analysis, testing, and implementation
workflows. It supports multiple LLM providers and implementation methods.

Main Interfaces:
    ask_llm: High-level interface supporting multiple LLM providers and methods
    ask_claude_code: Claude-specific interface with CLI and API method routing

Example:
    >>> from mcp_coder import ask_llm
    >>> response = ask_llm("Explain recursion", provider="claude", method="api")
    >>> print(response)

    >>> from mcp_coder import ask_claude_code
    >>> response = ask_claude_code("Review this code", method="cli")
    >>> print(response)
"""

from .llm.interface import ask_llm, prompt_llm
from .llm.providers.claude.claude_code_interface import ask_claude_code
from .llm.providers.claude.claude_executable_finder import (
    find_claude_executable,
    verify_claude_installation,
)
from .llm.serialization import deserialize_llm_response, serialize_llm_response
from .llm.types import LLM_RESPONSE_VERSION, LLMResponseDict
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
    git_push,
    is_git_repository,
)
from .utils.github_operations import CommentData, IssueData, IssueManager, LabelData
from .utils.subprocess_runner import (
    CommandOptions,
    CommandResult,
    execute_command,
    execute_subprocess,
)

# Version is automatically determined from git tags via setuptools-scm
try:
    from importlib.metadata import version

    __version__ = version("mcp-coder")
except Exception:
    # Fallback for development/editable installs without proper metadata
    __version__ = "0.0.0.dev0+unknown"

__all__ = [
    # Core LLM interfaces
    "ask_claude_code",
    "ask_llm",
    "prompt_llm",
    "serialize_llm_response",
    "deserialize_llm_response",
    # LLM Types
    "LLMResponseDict",
    "LLM_RESPONSE_VERSION",
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
    "git_push",
    "is_git_repository",
    # GitHub operations - Public API
    "IssueManager",
    "IssueData",
    "CommentData",
    "LabelData",
    # Prompt management
    "get_prompt",
    "validate_prompt_markdown",
    "validate_prompt_directory",
]
