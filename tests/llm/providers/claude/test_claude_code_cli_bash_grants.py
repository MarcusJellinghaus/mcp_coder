"""Unit tests for ``bash_grants`` in the Claude CLI command builder."""

import tempfile
from collections.abc import Sequence
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.llm.providers.claude.claude_code_cli import (
    ask_claude_code_cli,
    build_cli_command,
)

from .conftest import StreamJsonFactory, _make_stream_gen

GRANTS = ["Bash(git config probe.a 1)", "Bash(npm test)"]


class TestBuildCliCommandBashGrants:
    """build_cli_command enables Bash only with grants and lists them last."""

    @pytest.mark.parametrize("grants", [None, []])
    def test_no_grants_matches_default_command(
        self, grants: Sequence[str] | None
    ) -> None:
        """None or an empty list yields exactly the grant-less command."""
        cmd = build_cli_command(None, "claude", bash_grants=grants)

        assert cmd == build_cli_command(None, "claude")
        assert cmd[cmd.index("--tools") + 1] == "ToolSearch"
        assert "--allowedTools" not in cmd

    def test_grants_enable_bash_and_are_appended_last(self) -> None:
        """Two grants: Bash joins --tools and --allowedTools ends the command."""
        cmd = build_cli_command(None, "claude", bash_grants=GRANTS)

        assert cmd[cmd.index("--tools") + 1] == "ToolSearch,Bash"
        assert cmd[-3:] == ["--allowedTools", *GRANTS]
        assert cmd.count("--allowedTools") == 1

    def test_grants_last_with_settings_and_mcp_config(self) -> None:
        """Grants stay at the end when settings_file and mcp_config are set."""
        cmd = build_cli_command(
            "session-1",
            "claude",
            mcp_config=".mcp.json",
            settings_file="settings.json",
            append_system_prompt="extra",
            bash_grants=GRANTS,
        )

        assert cmd[cmd.index("--tools") + 1] == "ToolSearch,Bash"
        assert cmd[cmd.index("--settings") + 1] == "settings.json"
        assert cmd[cmd.index("--mcp-config") + 1] == ".mcp.json"
        assert cmd[-3:] == ["--allowedTools", *GRANTS]


class TestAskClaudeCodeCliBashGrants:
    """ask_claude_code_cli forwards bash_grants down to the CLI command."""

    @patch(
        "mcp_coder.llm.providers.claude.claude_code_cli_streaming._find_claude_executable"
    )
    @patch("mcp_coder.llm.providers.claude.claude_code_cli_streaming.stream_subprocess")
    @patch(
        "mcp_coder.llm.providers.claude.claude_code_cli_streaming.get_stream_log_path"
    )
    def test_grants_reach_command(
        self,
        mock_get_path: MagicMock,
        mock_stream: MagicMock,
        mock_find: MagicMock,
        make_stream_json_output: StreamJsonFactory,
    ) -> None:
        """The subprocess command carries the grants after --allowedTools."""
        mock_find.return_value = "claude"
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_get_path.return_value = Path(tmpdir) / "test.ndjson"
            mock_stream.return_value = _make_stream_gen(
                make_stream_json_output("ok", "sess-1").split("\n")
            )

            ask_claude_code_cli("Test question", bash_grants=GRANTS)

            command = mock_stream.call_args[0][0]
            assert command[command.index("--tools") + 1] == "ToolSearch,Bash"
            assert command[-3:] == ["--allowedTools", *GRANTS]
