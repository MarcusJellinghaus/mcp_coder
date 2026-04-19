"""Copilot CLI provider module."""

from .copilot_cli import ask_copilot_cli
from .copilot_cli_streaming import ask_copilot_cli_stream

__all__ = [
    "ask_copilot_cli",
    "ask_copilot_cli_stream",
]
