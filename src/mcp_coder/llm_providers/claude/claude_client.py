#!/usr/bin/env python3
"""Claude Code client - compatibility wrapper."""

from .claude_code_cli import ask_claude_code_cli


def ask_claude(question: str, timeout: int = 30) -> str:
    """Ask Claude a question via Claude Code CLI."""
    return ask_claude_code_cli(question, timeout)
