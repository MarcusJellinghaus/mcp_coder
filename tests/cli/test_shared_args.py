"""Unit tests for the DRY shared CLI flag helpers (`cli/shared_args.py`).

These tests lock the canonical wording, defaults, choices, and metavar of the
five opt-in per-flag helpers, plus an integration guard verifying that every
parser owning ``--llm-method`` renders ``METHOD`` in its help output.
"""

from __future__ import annotations

import argparse

import pytest

from mcp_coder.cli.main import create_parser
from mcp_coder.cli.shared_args import (
    _EXECUTION_DIR_HELP,
    _LLM_METHOD_HELP,
    _MCP_CONFIG_HELP,
    _PROJECT_DIR_HELP,
    _SETTINGS_HELP,
    add_execution_dir_arg,
    add_llm_method_arg,
    add_mcp_config_arg,
    add_project_dir_arg,
    add_settings_arg,
)


def _get_subparser(
    parser: argparse.ArgumentParser, *path: str
) -> argparse.ArgumentParser:
    """Walk the subparser tree of ``parser`` following the given name path."""
    current = parser
    for name in path:
        subactions = [
            action
            for action in current._actions  # pylint: disable=protected-access
            if isinstance(
                action, argparse._SubParsersAction
            )  # pylint: disable=protected-access
        ]
        assert subactions, f"No subparsers on parser while resolving {name!r}"
        choices = subactions[0].choices
        assert name in choices, f"Subcommand {name!r} not found"
        current = choices[name]
    return current


class TestAddProjectDirArg:
    """Tests for add_project_dir_arg."""

    def test_default_is_none(self) -> None:
        """project_dir defaults to None."""
        parser = argparse.ArgumentParser()
        add_project_dir_arg(parser)
        args = parser.parse_args([])
        assert args.project_dir is None

    def test_canonical_help_in_format_help(self) -> None:
        """Canonical wording appears in help output."""
        parser = argparse.ArgumentParser()
        add_project_dir_arg(parser)
        assert "where source code lives" in parser.format_help()

    def test_help_override_honored(self) -> None:
        """A custom help string is used when provided."""
        parser = argparse.ArgumentParser()
        add_project_dir_arg(
            parser, help="Target project directory (default: current directory)"
        )
        assert "Target project directory" in parser.format_help()

    def test_metavar_override_honored(self) -> None:
        """A custom metavar is rendered in help output."""
        parser = argparse.ArgumentParser()
        add_project_dir_arg(parser, metavar="PATH")
        assert "PATH" in parser.format_help()


class TestAddLlmMethodArg:
    """Tests for add_llm_method_arg."""

    def test_default_is_none(self) -> None:
        """llm_method defaults to None."""
        parser = argparse.ArgumentParser()
        add_llm_method_arg(parser)
        args = parser.parse_args([])
        assert args.llm_method is None

    def test_valid_provider_parses(self) -> None:
        """A supported provider is accepted."""
        parser = argparse.ArgumentParser()
        add_llm_method_arg(parser)
        args = parser.parse_args(["--llm-method", "claude"])
        assert args.llm_method == "claude"

    def test_invalid_provider_exits(self) -> None:
        """An unsupported provider triggers SystemExit."""
        parser = argparse.ArgumentParser()
        add_llm_method_arg(parser)
        with pytest.raises(SystemExit):
            parser.parse_args(["--llm-method", "not-a-provider"])

    def test_method_metavar_in_help(self) -> None:
        """METHOD metavar appears in help output."""
        parser = argparse.ArgumentParser()
        add_llm_method_arg(parser)
        assert "METHOD" in parser.format_help()


class TestAddMcpConfigArg:
    """Tests for add_mcp_config_arg."""

    def test_default_is_none(self) -> None:
        """mcp_config defaults to None."""
        parser = argparse.ArgumentParser()
        add_mcp_config_arg(parser)
        args = parser.parse_args([])
        assert args.mcp_config is None

    def test_canonical_help(self) -> None:
        """Canonical wording appears in help output."""
        parser = argparse.ArgumentParser()
        add_mcp_config_arg(parser)
        assert ".mcp.linux.json" in parser.format_help()

    def test_help_override_honored(self) -> None:
        """A custom help string is used when provided."""
        parser = argparse.ArgumentParser()
        add_mcp_config_arg(parser, help="Path to .mcp.json for MCP agent smoke test")
        assert "MCP agent smoke test" in parser.format_help()


class TestAddSettingsArg:
    """Tests for add_settings_arg."""

    def test_default_is_none(self) -> None:
        """settings defaults to None."""
        parser = argparse.ArgumentParser()
        add_settings_arg(parser)
        args = parser.parse_args([])
        assert args.settings is None

    def test_canonical_help(self) -> None:
        """Canonical wording appears in help output."""
        parser = argparse.ArgumentParser()
        add_settings_arg(parser)
        assert "settings.local.json" in parser.format_help()


class TestAddExecutionDirArg:
    """Tests for add_execution_dir_arg."""

    def test_default_is_none(self) -> None:
        """execution_dir defaults to None."""
        parser = argparse.ArgumentParser()
        add_execution_dir_arg(parser)
        args = parser.parse_args([])
        assert args.execution_dir is None

    def test_canonical_help(self) -> None:
        """Canonical wording appears in help output."""
        parser = argparse.ArgumentParser()
        add_execution_dir_arg(parser)
        assert "where Claude subprocess runs" in parser.format_help()


class TestCanonicalWordingConstants:
    """The exported help constants carry the canonical wording."""

    def test_project_dir_wording(self) -> None:
        """Project-dir constant matches the settled canonical wording."""
        assert _PROJECT_DIR_HELP == (
            "Project directory: where source code lives (git operations, file "
            "modifications). Default: current directory"
        )

    def test_llm_method_wording(self) -> None:
        """LLM-method constant matches the settled canonical wording."""
        assert _LLM_METHOD_HELP == (
            "LLM method override. If omitted, uses config default_provider or claude"
        )

    def test_mcp_config_wording(self) -> None:
        """MCP-config constant matches the settled canonical wording."""
        assert (
            _MCP_CONFIG_HELP == "Path to MCP configuration file (e.g., .mcp.linux.json)"
        )

    def test_settings_wording(self) -> None:
        """Settings constant matches the settled canonical wording."""
        assert _SETTINGS_HELP == (
            "Path to Claude Code settings file (.claude/settings.local.json). "
            "Auto-detected from <project_dir>/.claude/ if omitted. "
            "Overrides Claude's cwd-based settings discovery."
        )

    def test_execution_dir_wording(self) -> None:
        """Execution-dir constant matches the settled canonical wording."""
        assert _EXECUTION_DIR_HELP == (
            "Execution directory: where Claude subprocess runs (config discovery). "
            "Default: current directory"
        )


class TestLlmMethodMetavarIntegration:
    """Every parser owning --llm-method renders METHOD in its help."""

    @pytest.mark.parametrize(
        "path",
        [
            ("prompt",),
            ("commit", "auto"),
            ("implement",),
            ("create-plan",),
            ("create-pr",),
            ("verify",),
            ("check", "branch-status"),
            ("icoder",),
        ],
    )
    def test_method_metavar_present(self, path: tuple[str, ...]) -> None:
        """The subparser's help shows METHOD for its --llm-method flag."""
        parser = create_parser()
        subparser = _get_subparser(parser, *path)
        help_text = subparser.format_help()
        assert "--llm-method METHOD" in help_text
