"""Tests for Copilot CLI JSONL parser, tool permission converter, and command builder."""

import json
import logging
from collections.abc import Callable
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.llm.providers.copilot.copilot_cli import (
    COPILOT_CMD_LINE_LIMIT,
    _read_settings_allow,
    ask_copilot_cli,
    build_copilot_command,
    convert_settings_to_copilot_tools,
    parse_copilot_jsonl_line,
    parse_copilot_jsonl_output,
)
from mcp_coder.utils.subprocess_runner import CalledProcessError, TimeoutExpired


class TestParseCopilotJsonlLine:
    """Tests for parse_copilot_jsonl_line."""

    def test_parse_jsonl_line_valid(self) -> None:
        """Valid JSON line returns dict."""
        result = parse_copilot_jsonl_line('{"type": "result", "data": 1}')
        assert result == {"type": "result", "data": 1}

    def test_parse_jsonl_line_empty(self) -> None:
        """Empty string returns None."""
        assert parse_copilot_jsonl_line("") is None
        assert parse_copilot_jsonl_line("   ") is None

    def test_parse_jsonl_line_invalid_json(self) -> None:
        """Bad JSON returns None."""
        assert parse_copilot_jsonl_line("not json at all") is None
        assert parse_copilot_jsonl_line("{broken") is None


class TestParseCopilotJsonlOutput:
    """Tests for parse_copilot_jsonl_output."""

    def test_parse_output_extracts_text(self, make_copilot_jsonl_output) -> None:  # type: ignore[no-untyped-def]
        """Text from assistant.message content blocks is extracted."""
        lines = make_copilot_jsonl_output(text="Test response")
        result = parse_copilot_jsonl_output(lines)
        assert result["text"] == "Test response"

    def test_parse_output_extracts_session_id(self, make_copilot_jsonl_output) -> None:  # type: ignore[no-untyped-def]
        """sessionId from result message is extracted."""
        lines = make_copilot_jsonl_output(session_id="sess-abc-789")
        result = parse_copilot_jsonl_output(lines)
        assert result["session_id"] == "sess-abc-789"

    def test_parse_output_maps_usage(self, make_copilot_jsonl_output) -> None:  # type: ignore[no-untyped-def]
        """outputTokens is mapped to output_tokens."""
        lines = make_copilot_jsonl_output(output_tokens=100)
        result = parse_copilot_jsonl_output(lines)
        assert result["usage"]["output_tokens"] == 100

    def test_parse_output_skips_ephemeral_types(self, make_copilot_jsonl_output) -> None:  # type: ignore[no-untyped-def]
        """Ephemeral types like session.info don't appear in text."""
        lines = make_copilot_jsonl_output(
            text="Real content",
            extra_ephemeral_types=["session.info", "assistant.reasoning"],
        )
        result = parse_copilot_jsonl_output(lines)
        assert result["text"] == "Real content"
        # Ephemeral messages are still in messages list but don't affect text
        assert len(result["messages"]) == 4  # 2 ephemeral + assistant + result

    def test_parse_output_handles_tool_requests(self, make_copilot_jsonl_output) -> None:  # type: ignore[no-untyped-def]
        """toolRequests in assistant.message are preserved in messages."""
        lines = make_copilot_jsonl_output(include_tool_request=True)
        result = parse_copilot_jsonl_output(lines)
        # Find the assistant message
        assistant_msgs = [
            m for m in result["messages"] if m.get("type") == "assistant.message"
        ]
        assert len(assistant_msgs) == 1
        assert "toolRequests" in assistant_msgs[0]["data"]
        # tool.execution_complete should also be in messages
        tool_msgs = [
            m for m in result["messages"] if m.get("type") == "tool.execution_complete"
        ]
        assert len(tool_msgs) == 1

    def test_parse_output_empty_input(self) -> None:
        """Empty list returns empty response."""
        result = parse_copilot_jsonl_output([])
        assert result["text"] == ""
        assert result["session_id"] is None
        assert result["messages"] == []
        assert result["usage"] == {}
        assert result["raw_result"] is None

    def test_parse_output_raw_result_preserved(self, make_copilot_jsonl_output) -> None:  # type: ignore[no-untyped-def]
        """The result JSONL message is stored in raw_result."""
        lines = make_copilot_jsonl_output()
        result = parse_copilot_jsonl_output(lines)
        assert result["raw_result"] is not None
        assert result["raw_result"]["type"] == "result"
        assert result["raw_result"]["exitCode"] == 0

    def test_parse_output_skips_invalid_lines(self) -> None:
        """Invalid JSONL lines are silently skipped."""
        lines = [
            "not json",
            "",
            json.dumps(
                {
                    "type": "assistant.message",
                    "data": {"content": "hello", "toolRequests": []},
                }
            ),
        ]
        result = parse_copilot_jsonl_output(lines)
        assert result["text"] == "hello"
        assert len(result["messages"]) == 1


class TestConvertSettingsToCopilotTools:
    """Tests for convert_settings_to_copilot_tools."""

    def test_convert_mcp_tool_basic(self) -> None:
        """mcp__workspace__read_file → workspace-read_file."""
        result = convert_settings_to_copilot_tools(["mcp__workspace__read_file"])
        assert result["available_tools"] == ["workspace-read_file"]
        assert result["allow_tools"] == []

    def test_convert_mcp_tool_hyphenated_server(self) -> None:
        """mcp__tools-py__run_pytest_check → tools-py-run_pytest_check."""
        result = convert_settings_to_copilot_tools(["mcp__tools-py__run_pytest_check"])
        assert result["available_tools"] == ["tools-py-run_pytest_check"]

    def test_convert_mcp_tool_hyphenated_server_name(self) -> None:
        """mcp__obsidian-wiki__read-note → obsidian-wiki-read-note."""
        result = convert_settings_to_copilot_tools(["mcp__obsidian-wiki__read-note"])
        assert result["available_tools"] == ["obsidian-wiki-read-note"]

    def test_convert_bash_to_shell(self) -> None:
        """Bash(git diff:*) → shell(git diff:*)."""
        result = convert_settings_to_copilot_tools(["Bash(git diff:*)"])
        assert result["allow_tools"] == ["shell(git diff:*)"]
        assert result["available_tools"] == []

    def test_convert_bash_wildcard(self) -> None:
        """Bash(*) → shell(*)."""
        result = convert_settings_to_copilot_tools(["Bash(*)"])
        assert result["allow_tools"] == ["shell(*)"]

    def test_convert_skill_skipped_with_warning(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Skill(commit_push) is skipped with warning logged."""
        with caplog.at_level(logging.WARNING):
            result = convert_settings_to_copilot_tools(["Skill(commit_push)"])
        assert result["available_tools"] == []
        assert result["allow_tools"] == []
        assert "Skipping unmappable permission entry" in caplog.text

    def test_convert_webfetch_skipped_with_warning(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """WebFetch(domain:*) is skipped with warning logged."""
        with caplog.at_level(logging.WARNING):
            result = convert_settings_to_copilot_tools(["WebFetch(domain:*)"])
        assert result["available_tools"] == []
        assert result["allow_tools"] == []
        assert "Skipping unmappable permission entry" in caplog.text

    def test_convert_mixed_entries(self) -> None:
        """Real-world mix from settings.local.json."""
        entries = [
            "mcp__workspace__read_file",
            "mcp__workspace__save_file",
            "mcp__tools-py__run_pytest_check",
            "Bash(git diff:*)",
            "Bash(*)",
            "Skill(commit_push)",
            "WebFetch(domain:*)",
        ]
        result = convert_settings_to_copilot_tools(entries)
        assert result["available_tools"] == [
            "workspace-read_file",
            "workspace-save_file",
            "tools-py-run_pytest_check",
        ]
        assert result["allow_tools"] == ["shell(git diff:*)", "shell(*)"]

    def test_convert_empty_list(self) -> None:
        """Empty input returns empty lists."""
        result = convert_settings_to_copilot_tools([])
        assert result["available_tools"] == []
        assert result["allow_tools"] == []


class TestBuildCopilotCommand:
    """Tests for build_copilot_command."""

    def test_build_basic_command(self) -> None:
        """Minimal args produce correct flag order."""
        cmd = build_copilot_command("hello", "/usr/bin/copilot")
        assert cmd == [
            "/usr/bin/copilot",
            "-p",
            "hello",
            "--output-format",
            "json",
            "-s",
            "--allow-all-tools",
        ]

    def test_build_command_with_session_id(self) -> None:
        """--resume=<id> included."""
        cmd = build_copilot_command("hello", "copilot", session_id="sess-123")
        assert "--resume=sess-123" in cmd

    def test_build_command_with_available_tools(self) -> None:
        """--available-tools= comma-separated."""
        cmd = build_copilot_command(
            "hello", "copilot", available_tools=["workspace-read_file", "tools-py-run"]
        )
        assert "--available-tools=workspace-read_file,tools-py-run" in cmd

    def test_build_command_with_allow_tools(self) -> None:
        """Multiple --allow-tool= flags."""
        cmd = build_copilot_command(
            "hello", "copilot", allow_tools=["shell(git diff:*)", "shell(*)"]
        )
        assert "--allow-tool=shell(git diff:*)" in cmd
        assert "--allow-tool=shell(*)" in cmd

    def test_build_command_always_includes_s_flag(self) -> None:
        """-s always present."""
        cmd = build_copilot_command("hello", "copilot")
        assert "-s" in cmd

    def test_build_command_always_includes_allow_all_tools(self) -> None:
        """--allow-all-tools always present."""
        cmd = build_copilot_command("hello", "copilot")
        assert "--allow-all-tools" in cmd

    def test_build_command_empty_cmd_raises(self) -> None:
        """ValueError for empty copilot_cmd."""
        with pytest.raises(ValueError, match="copilot_cmd cannot be empty"):
            build_copilot_command("hello", "")
        with pytest.raises(ValueError, match="copilot_cmd cannot be empty"):
            build_copilot_command("hello", "   ")

    def test_build_command_exceeds_8kb_raises(self) -> None:
        """ValueError with guidance message."""
        # Create a prompt that will exceed 8KB
        long_prompt = "x" * (COPILOT_CMD_LINE_LIMIT + 100)
        with pytest.raises(ValueError, match="exceeds.*char limit"):
            build_copilot_command(long_prompt, "copilot")


class TestReadSettingsAllow:
    """Tests for _read_settings_allow."""

    def test_read_settings_allow_returns_list(self, tmp_path: Path) -> None:
        """Mock file with permissions.allow entries."""
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()
        settings = {
            "permissions": {"allow": ["mcp__workspace__read_file", "Bash(git diff:*)"]}
        }
        (claude_dir / "settings.local.json").write_text(
            json.dumps(settings), encoding="utf-8"
        )
        result = _read_settings_allow(str(tmp_path))
        assert result == ["mcp__workspace__read_file", "Bash(git diff:*)"]

    def test_read_settings_allow_file_missing_returns_none(
        self, tmp_path: Path
    ) -> None:
        """No file → None."""
        result = _read_settings_allow(str(tmp_path))
        assert result is None

    def test_read_settings_allow_no_permissions_key_returns_none(
        self, tmp_path: Path
    ) -> None:
        """JSON without permissions → None."""
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()
        (claude_dir / "settings.local.json").write_text(
            json.dumps({"other": "data"}), encoding="utf-8"
        )
        result = _read_settings_allow(str(tmp_path))
        assert result is None


class TestAskCopilotCli:
    """Tests for ask_copilot_cli (mocked subprocess)."""

    def _make_mock_result(
        self,
        make_copilot_jsonl_output: Callable[..., list[str]],
        text: str = "Hello from Copilot",
        session_id: str = "test-session-123",
    ) -> MagicMock:
        """Create a mock CommandResult with JSONL output."""
        lines = make_copilot_jsonl_output(text=text, session_id=session_id)
        mock_result = MagicMock()
        mock_result.stdout = "\n".join(lines)
        mock_result.stderr = ""
        mock_result.return_code = 0
        mock_result.timed_out = False
        return mock_result

    @patch(
        "mcp_coder.llm.providers.copilot.copilot_cli._read_settings_allow",
        return_value=None,
    )
    @patch("mcp_coder.llm.providers.copilot.copilot_cli.execute_subprocess")
    @patch(
        "mcp_coder.llm.providers.copilot.copilot_cli.find_executable",
        return_value="/usr/bin/copilot",
    )
    def test_ask_copilot_cli_success(
        self,
        mock_find: MagicMock,
        mock_exec: MagicMock,
        mock_settings: MagicMock,
        make_copilot_jsonl_output: Callable[..., list[str]],
        tmp_path: Path,
    ) -> None:
        """Mock subprocess, verify LLMResponseDict structure."""
        mock_exec.return_value = self._make_mock_result(make_copilot_jsonl_output)
        result = ask_copilot_cli(
            "What is 2+2?", logs_dir=str(tmp_path), cwd=str(tmp_path)
        )
        assert result["provider"] == "copilot"
        assert result["text"] == "Hello from Copilot"
        assert result["version"] == "1.0"
        assert "timestamp" in result
        assert "raw_response" in result

    @patch(
        "mcp_coder.llm.providers.copilot.copilot_cli._read_settings_allow",
        return_value=None,
    )
    @patch("mcp_coder.llm.providers.copilot.copilot_cli.execute_subprocess")
    @patch(
        "mcp_coder.llm.providers.copilot.copilot_cli.find_executable",
        return_value="/usr/bin/copilot",
    )
    def test_ask_copilot_cli_session_id_returned(
        self,
        mock_find: MagicMock,
        mock_exec: MagicMock,
        mock_settings: MagicMock,
        make_copilot_jsonl_output: Callable[..., list[str]],
        tmp_path: Path,
    ) -> None:
        """Verify session_id from JSONL result."""
        mock_exec.return_value = self._make_mock_result(
            make_copilot_jsonl_output, session_id="copilot-sess-456"
        )
        result = ask_copilot_cli("hello", logs_dir=str(tmp_path), cwd=str(tmp_path))
        assert result["session_id"] == "copilot-sess-456"

    @patch(
        "mcp_coder.llm.providers.copilot.copilot_cli._read_settings_allow",
        return_value=None,
    )
    @patch("mcp_coder.llm.providers.copilot.copilot_cli.execute_subprocess")
    @patch(
        "mcp_coder.llm.providers.copilot.copilot_cli.find_executable",
        return_value="/usr/bin/copilot",
    )
    def test_ask_copilot_cli_system_prompt_prepended(
        self,
        mock_find: MagicMock,
        mock_exec: MagicMock,
        mock_settings: MagicMock,
        make_copilot_jsonl_output: Callable[..., list[str]],
        tmp_path: Path,
    ) -> None:
        """Verify prompt starts with system prompt."""
        mock_exec.return_value = self._make_mock_result(make_copilot_jsonl_output)
        ask_copilot_cli(
            "What is 2+2?",
            system_prompt="You are a calculator",
            logs_dir=str(tmp_path),
            cwd=str(tmp_path),
        )
        # Check the command that was passed to execute_subprocess
        call_args = mock_exec.call_args[0][0]
        # -p arg is at index 2
        prompt_arg = call_args[2]
        assert prompt_arg.startswith("You are a calculator")
        assert "What is 2+2?" in prompt_arg

    @patch(
        "mcp_coder.llm.providers.copilot.copilot_cli._read_settings_allow",
        return_value=None,
    )
    @patch("mcp_coder.llm.providers.copilot.copilot_cli.execute_subprocess")
    @patch(
        "mcp_coder.llm.providers.copilot.copilot_cli.find_executable",
        return_value="/usr/bin/copilot",
    )
    def test_ask_copilot_cli_system_prompt_skipped_on_resume(
        self,
        mock_find: MagicMock,
        mock_exec: MagicMock,
        mock_settings: MagicMock,
        make_copilot_jsonl_output: Callable[..., list[str]],
        tmp_path: Path,
    ) -> None:
        """session_id set → no system prompt."""
        mock_exec.return_value = self._make_mock_result(make_copilot_jsonl_output)
        ask_copilot_cli(
            "What is 2+2?",
            session_id="existing-session",
            system_prompt="You are a calculator",
            logs_dir=str(tmp_path),
            cwd=str(tmp_path),
        )
        call_args = mock_exec.call_args[0][0]
        prompt_arg = call_args[2]
        # System prompt should NOT be prepended on resume
        assert not prompt_arg.startswith("You are a calculator")
        assert prompt_arg == "What is 2+2?"

    def test_ask_copilot_cli_empty_question_raises(self) -> None:
        """ValueError for empty question."""
        with pytest.raises(ValueError, match="empty"):
            ask_copilot_cli("")
        with pytest.raises(ValueError, match="empty"):
            ask_copilot_cli("   ")

    @patch(
        "mcp_coder.llm.providers.copilot.copilot_cli._read_settings_allow",
        return_value=None,
    )
    @patch("mcp_coder.llm.providers.copilot.copilot_cli.execute_subprocess")
    @patch(
        "mcp_coder.llm.providers.copilot.copilot_cli.find_executable",
        return_value="/usr/bin/copilot",
    )
    def test_ask_copilot_cli_timeout_raises(
        self,
        mock_find: MagicMock,
        mock_exec: MagicMock,
        mock_settings: MagicMock,
        tmp_path: Path,
    ) -> None:
        """TimeoutExpired propagated."""
        mock_result = MagicMock()
        mock_result.stdout = ""
        mock_result.stderr = ""
        mock_result.return_code = 0
        mock_result.timed_out = True
        mock_exec.return_value = mock_result
        with pytest.raises(TimeoutExpired):
            ask_copilot_cli("hello", logs_dir=str(tmp_path), cwd=str(tmp_path))

    @patch(
        "mcp_coder.llm.providers.copilot.copilot_cli._read_settings_allow",
        return_value=None,
    )
    @patch("mcp_coder.llm.providers.copilot.copilot_cli.execute_subprocess")
    @patch(
        "mcp_coder.llm.providers.copilot.copilot_cli.find_executable",
        return_value="/usr/bin/copilot",
    )
    def test_ask_copilot_cli_nonzero_exit_raises(
        self,
        mock_find: MagicMock,
        mock_exec: MagicMock,
        mock_settings: MagicMock,
        tmp_path: Path,
    ) -> None:
        """CalledProcessError with stream file path."""
        mock_result = MagicMock()
        mock_result.stdout = ""
        mock_result.stderr = "error occurred"
        mock_result.return_code = 1
        mock_result.timed_out = False
        mock_exec.return_value = mock_result
        with pytest.raises(CalledProcessError) as exc_info:
            ask_copilot_cli("hello", logs_dir=str(tmp_path), cwd=str(tmp_path))
        assert "Stream file" in str(exc_info.value.stderr)

    @patch(
        "mcp_coder.llm.providers.copilot.copilot_cli._read_settings_allow",
        return_value=None,
    )
    @patch("mcp_coder.llm.providers.copilot.copilot_cli.execute_subprocess")
    @patch(
        "mcp_coder.llm.providers.copilot.copilot_cli.find_executable",
        return_value="/usr/bin/copilot",
    )
    def test_ask_copilot_cli_saves_jsonl_log(
        self,
        mock_find: MagicMock,
        mock_exec: MagicMock,
        mock_settings: MagicMock,
        make_copilot_jsonl_output: Callable[..., list[str]],
        tmp_path: Path,
    ) -> None:
        """Verify log file written."""
        mock_exec.return_value = self._make_mock_result(make_copilot_jsonl_output)
        ask_copilot_cli("hello", logs_dir=str(tmp_path), cwd=str(tmp_path))
        # Check that a .ndjson file was created in the copilot-sessions subdir
        session_dir = tmp_path / "copilot-sessions"
        ndjson_files = list(session_dir.glob("*.ndjson"))
        assert len(ndjson_files) == 1

    @patch(
        "mcp_coder.llm.providers.copilot.copilot_cli.find_executable",
        side_effect=FileNotFoundError("not found"),
    )
    def test_ask_copilot_cli_not_found_raises(self, mock_find: MagicMock) -> None:
        """FileNotFoundError from find_executable."""
        with pytest.raises(FileNotFoundError):
            ask_copilot_cli("hello")
