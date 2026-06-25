"""Tests for iCoder CLI parser flags and defaults."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from mcp_coder.cli.main import create_parser


def test_icoder_parser_registered() -> None:
    """Test parser is registered (icoder appears in subcommands)."""
    parser = create_parser()
    args = parser.parse_args(["icoder"])
    assert args.command == "icoder"


def test_icoder_llm_method_flag() -> None:
    """Test parser accepts --llm-method flag."""
    parser = create_parser()
    args = parser.parse_args(["icoder", "--llm-method", "langchain"])
    assert args.llm_method == "langchain"


def test_icoder_project_dir_flag() -> None:
    """Test parser accepts --project-dir flag."""
    parser = create_parser()
    args = parser.parse_args(["icoder", "--project-dir", "/tmp/test"])
    assert args.project_dir == "/tmp/test"


def test_icoder_mcp_config_flag() -> None:
    """Test parser accepts --mcp-config flag."""
    parser = create_parser()
    args = parser.parse_args(["icoder", "--mcp-config", "/tmp/.mcp.json"])
    assert args.mcp_config == "/tmp/.mcp.json"


def test_icoder_execution_dir_flag() -> None:
    """Test parser accepts --execution-dir flag."""
    parser = create_parser()
    args = parser.parse_args(["icoder", "--execution-dir", "/tmp/exec"])
    assert args.execution_dir == "/tmp/exec"


def test_icoder_default_values() -> None:
    """Test parser default values."""
    parser = create_parser()
    args = parser.parse_args(["icoder"])
    assert args.llm_method is None
    assert args.project_dir is None
    assert args.mcp_config is None
    assert args.execution_dir is None


def test_icoder_no_format_tools_flag() -> None:
    """Test parser accepts --no-format-tools flag."""
    parser = create_parser()
    args = parser.parse_args(["icoder", "--no-format-tools"])
    assert args.no_format_tools is True


def test_icoder_no_format_tools_default() -> None:
    """Test --no-format-tools defaults to False (formatting on)."""
    parser = create_parser()
    args = parser.parse_args(["icoder"])
    assert args.no_format_tools is False


def test_execute_icoder_importable() -> None:
    """Test execute_icoder is importable and callable."""
    from mcp_coder.cli.commands.icoder import execute_icoder

    assert callable(execute_icoder)


def test_main_routes_icoder(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify main() dispatches 'icoder' to execute_icoder."""
    called: dict[str, object] = {}

    def mock_execute(args):  # type: ignore[no-untyped-def]
        called["args"] = args
        return 0

    monkeypatch.setattr("sys.argv", ["mcp-coder", "icoder"])

    with patch("mcp_coder.cli.main.execute_icoder", mock_execute):
        from mcp_coder.cli.main import main

        result = main()

    assert result == 0
    args_obj = called["args"]
    assert getattr(args_obj, "command") == "icoder"


def test_icoder_initial_color_flag() -> None:
    """Parser accepts --initial-color."""
    parser = create_parser()
    args = parser.parse_args(["icoder", "--initial-color", "red"])
    assert args.initial_color == "red"


def test_icoder_initial_color_default() -> None:
    """Default --initial-color is None."""
    parser = create_parser()
    args = parser.parse_args(["icoder"])
    assert args.initial_color is None


def test_tool_display_arg_default_compressed() -> None:
    """--tool-display defaults to 'compressed'."""
    parser = create_parser()
    args = parser.parse_args(["icoder"])
    assert args.tool_display == "compressed"


def test_tool_display_arg_accepts_oneline() -> None:
    """--tool-display accepts 'oneline'."""
    parser = create_parser()
    args = parser.parse_args(["icoder", "--tool-display", "oneline"])
    assert args.tool_display == "oneline"


def test_tool_display_arg_rejects_unknown_value() -> None:
    """--tool-display rejects values outside the choices."""
    parser = create_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["icoder", "--tool-display", "verbose"])


@pytest.mark.parametrize(
    "flags",
    [
        ["--continue-session", "--continue-session-from", "log.jsonl"],
        ["--continue-session", "--session-id", "sess-1"],
        ["--continue-session-from", "log.jsonl", "--session-id", "sess-1"],
    ],
)
def test_icoder_session_resume_flags_mutually_exclusive(flags: list[str]) -> None:
    """Passing two of {--continue-session, --continue-session-from, --session-id}
    raises an argparse error before any session resolution runs.
    """
    parser = create_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["icoder", *flags])
