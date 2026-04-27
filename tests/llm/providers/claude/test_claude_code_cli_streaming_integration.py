"""Integration tests for the Claude Code CLI streaming pipeline.

These tests call the real Claude CLI and verify end-to-end streaming
behavior. They require:
- Claude CLI installed and authenticated
- Network access to Claude API

Run with: pytest -m claude_cli_integration
"""

import tempfile

import pytest

from mcp_coder.llm.interface import prompt_llm_stream
from mcp_coder.llm.providers.claude.claude_code_cli_streaming import (
    ask_claude_code_cli_stream,
)


@pytest.mark.claude_cli_integration
class TestClaudeCodeCliStreamingIntegration:
    """End-to-end streaming tests against the real Claude CLI."""

    def test_basic_question_yields_text_delta_and_done(self) -> None:
        """A simple question yields text_delta events followed by a done event."""
        with tempfile.TemporaryDirectory() as tmp_logs_dir:
            events = list(
                ask_claude_code_cli_stream(
                    question="What is 2+2? Reply with just the number.",
                    timeout=60,
                    logs_dir=tmp_logs_dir,
                )
            )

        assert any(e["type"] == "text_delta" for e in events)
        done = next(e for e in events if e["type"] == "done")
        assert done.get("session_id")

    def test_session_continuity_via_session_id(self) -> None:
        """A second call with session_id resumes the prior conversation."""
        with tempfile.TemporaryDirectory() as tmp_logs_dir:
            events1 = list(
                ask_claude_code_cli_stream(
                    question="Remember: my favorite color is blue. Reply 'noted'.",
                    timeout=60,
                    logs_dir=tmp_logs_dir,
                )
            )
            done1 = next(e for e in events1 if e["type"] == "done")
            session_id = done1["session_id"]
            assert isinstance(session_id, str)

            events2 = list(
                ask_claude_code_cli_stream(
                    question="What is my favorite color? Reply with just the color.",
                    session_id=session_id,
                    timeout=60,
                    logs_dir=tmp_logs_dir,
                )
            )
        text = "".join(str(e["text"]) for e in events2 if e["type"] == "text_delta")
        assert "blue" in text.lower()
        done2 = next(e for e in events2 if e["type"] == "done")
        assert done2["session_id"]

    def test_prompt_llm_stream_claude_provider_yields_events(self) -> None:
        """prompt_llm_stream() forwards Claude CLI events end-to-end."""
        with tempfile.TemporaryDirectory() as tmp_logs_dir:
            events = list(
                prompt_llm_stream(
                    "Reply 'ok'.",
                    provider="claude",
                    timeout=60,
                    env_vars={"MCP_CODER_PROJECT_DIR": tmp_logs_dir},
                )
            )

        assert any(e["type"] == "done" for e in events)
