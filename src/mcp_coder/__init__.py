"""MCP Coder - An AI-powered software development automation toolkit.

This package provides extensible LLM interfaces for code analysis, testing, and implementation
workflows. It supports multiple LLM providers.

Main Interfaces:
    prompt_llm: High-level interface returning full LLMResponseDict with session management

Example:
    >>> from mcp_coder import prompt_llm
    >>> result = prompt_llm("Explain recursion", provider="claude")
    >>> print(result["text"])
"""

from .checks.branch_status import collect_branch_status
from .llm.interface import prompt_llm
from .llm.mlflow_logger import verify_mlflow
from .llm.providers.claude.claude_cli_verification import verify_claude
from .llm.providers.claude.claude_executable_finder import (
    find_claude_executable,
    verify_claude_installation,
)
from .llm.providers.langchain.verification import verify_langchain
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
from .utils.github_operations.issues import CommentData, IssueData, IssueManager
from .utils.github_operations.labels_manager import LabelData
from .utils.subprocess_runner import (
    CommandOptions,
    CommandResult,
    execute_command,
    execute_subprocess,
)
from .workflow_utils.commit_operations import generate_commit_message_with_llm

# Version is automatically determined from git tags via setuptools-scm
try:
    from importlib.metadata import version

    __version__ = version("mcp-coder")
except (
    Exception
):  # pylint: disable=broad-exception-caught  # optional import fallback — broad catch intentional
    # Fallback for development/editable installs without proper metadata
    __version__ = "0.0.0.dev0+unknown"

__all__ = [
    # Core LLM interfaces
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
    # Verification functions
    "verify_claude",
    "verify_langchain",
    "verify_mlflow",
    # Commit operations
    "generate_commit_message_with_llm",
    # Branch status
    "collect_branch_status",
]
