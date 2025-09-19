"""CLI command modules."""

from .commit import execute_commit_auto, execute_commit_clipboard
from .help import execute_help
from .prompt import execute_prompt
from .verify import execute_verify

__all__ = [
    "execute_help",
    "execute_verify",
    "execute_prompt",
    "execute_commit_auto",
    "execute_commit_clipboard",
]
