"""Tests for Copilot CLI JSONL parser and tool permission converter."""

import json
import logging

import pytest

from mcp_coder.llm.providers.copilot.copilot_cli import (
    convert_settings_to_copilot_tools,
    parse_copilot_jsonl_line,
    parse_copilot_jsonl_output,
)


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
        assert "toolRequests" in assistant_msgs[0]["message"]
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
                    "message": {"content": [{"type": "text", "text": "hello"}]},
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
