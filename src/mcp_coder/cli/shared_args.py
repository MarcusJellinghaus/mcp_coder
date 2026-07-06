"""Opt-in per-flag helpers for shared CLI arguments.

These helpers replace the ~13 copy-pasted ``--project-dir`` / ``--llm-method`` /
``--mcp-config`` / ``--settings`` / ``--execution-dir`` declarations across
``parsers.py`` and ``gh_parsers.py`` with a single canonical source of wording.

Each helper mutates the given parser in place (returns ``None``), mirroring the
existing ``add_*_parser`` style. Parsed argument values (dest, defaults,
choices) stay identical to the previous inline declarations — only ``--help``
text and ``metavar`` are unified. Per-call overrides are exposed for the few
commands that intentionally deviate.
"""

from __future__ import annotations

import argparse

from ..llm.types import SUPPORTED_PROVIDERS

_PROJECT_DIR_HELP = (
    "Project directory: where source code lives (git operations, file "
    "modifications). Default: current directory"
)
_LLM_METHOD_HELP = (
    "LLM method override. If omitted, uses config default_provider or claude"
)
_MCP_CONFIG_HELP = "Path to MCP configuration file (e.g., .mcp.linux.json)"
_SETTINGS_HELP = (
    "Path to Claude Code settings file (.claude/settings.local.json). "
    "Auto-detected from <project_dir>/.claude/ if omitted. "
    "Overrides Claude's cwd-based settings discovery."
)
_EXECUTION_DIR_HELP = (
    "Execution directory: where Claude subprocess runs (config discovery). "
    "Default: current directory"
)


def add_project_dir_arg(
    parser: argparse.ArgumentParser,
    *,
    help: str = _PROJECT_DIR_HELP,  # pylint: disable=redefined-builtin
    metavar: str | None = None,
) -> None:
    """Add the shared ``--project-dir`` flag to ``parser``."""
    parser.add_argument(
        "--project-dir",
        type=str,
        default=None,
        help=help,
        metavar=metavar,
    )


def add_llm_method_arg(
    parser: argparse.ArgumentParser,
    *,
    help: str = _LLM_METHOD_HELP,  # pylint: disable=redefined-builtin
    metavar: str = "METHOD",
) -> None:
    """Add the shared ``--llm-method`` flag to ``parser``."""
    parser.add_argument(
        "--llm-method",
        choices=sorted(SUPPORTED_PROVIDERS),
        default=None,
        metavar=metavar,
        help=help,
    )


def add_mcp_config_arg(
    parser: argparse.ArgumentParser,
    *,
    help: str = _MCP_CONFIG_HELP,  # pylint: disable=redefined-builtin
) -> None:
    """Add the shared ``--mcp-config`` flag to ``parser``."""
    parser.add_argument(
        "--mcp-config",
        type=str,
        default=None,
        help=help,
    )


def add_settings_arg(parser: argparse.ArgumentParser) -> None:
    """Add the shared ``--settings`` flag to ``parser``."""
    parser.add_argument(
        "--settings",
        type=str,
        default=None,
        help=_SETTINGS_HELP,
    )


def add_execution_dir_arg(parser: argparse.ArgumentParser) -> None:
    """Add the shared ``--execution-dir`` flag to ``parser``."""
    parser.add_argument(
        "--execution-dir",
        type=str,
        default=None,
        help=_EXECUTION_DIR_HELP,
    )
