"""MCP Coder - An AI-powered software development automation toolkit.

This package provides extensible LLM interfaces for code analysis, testing, and implementation
workflows. It supports multiple LLM providers.

Main Interfaces:
    prompt_llm: High-level interface returning full LLMResponseDict with session management

Example:
    >>> from mcp_coder import prompt_llm
    >>> result = prompt_llm("Explain recursion", project_dir=".", provider="claude")
    >>> print(result["text"])
"""

# isort: skip_file
#
# This module's import order is load-bearing and must NOT be auto-sorted. isort
# is configured with `float_to_top`, which hoists every import to the top of the
# file and would move the dependency guard below the heavy imports — defeating
# it. `skip_file` freezes the order here; the imports below are kept sorted by
# hand. (black still runs; pylint's import-position checks are convention-class
# and disabled project-wide.)

# Fail cleanly (not with a cryptic traceback) when a mandatory dependency is
# missing — e.g. a `pip install --no-deps` install. This guard MUST run before
# the heavy imports below, which is why it is the first statement after the
# docstring. Fail-open: any unexpected internal error is swallowed so a healthy
# install is never broken (SystemExit subclasses BaseException, so the intended
# clean exit-1 still propagates). See mcp_coder/_depcheck.py.
try:
    from . import _depcheck

    _depcheck.ensure_dependencies()
except Exception:  # noqa: BLE001 — fail-open: never break a healthy install
    pass

from .checks.branch_status import collect_branch_status
from .llm.interface import prompt_llm
from .llm.mlflow_verify import verify_mlflow
from .llm.providers.claude.claude_cli_verification import verify_claude
from .llm.providers.claude.claude_executable_finder import (
    find_claude_executable,
    verify_claude_installation,
)
from .llm.providers.langchain.verification import verify_langchain
from .llm.serialization import deserialize_llm_response, serialize_llm_response
from .llm.types import LLM_RESPONSE_VERSION, LLMResponseDict
from .mcp_workspace_git import (
    CommitResult,
    commit_all_changes,
    commit_staged_files,
    get_full_status,
    git_push,
    is_git_repository,
)
from .mcp_workspace_github import CommentData, IssueData, IssueManager, LabelData
from .prompt_manager import (
    get_prompt,
    validate_prompt_directory,
    validate_prompt_markdown,
)
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
