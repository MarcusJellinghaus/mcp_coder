"""Integration tests for Copilot CLI provider.

These tests require the Copilot CLI to be installed and authenticated.
They make real API calls and are excluded from normal test runs.
"""

from pathlib import Path

import pytest

from mcp_coder.llm.env import prepare_llm_environment
from mcp_coder.llm.providers.copilot.copilot_cli import ask_copilot_cli


@pytest.mark.copilot_cli_integration
class TestCopilotIntegration:
    """Integration tests that invoke the real Copilot CLI."""

    def test_basic_prompt(self, require_copilot_cli: None) -> None:
        """Basic smoke test: send a prompt, verify response structure."""
        env_vars = prepare_llm_environment(Path.cwd())

        result = ask_copilot_cli(
            "Yes or no: Is 1+1=2?",
            timeout=120,
            env_vars=env_vars,
            cwd=str(Path.cwd()),
        )

        assert isinstance(result, dict)
        assert len(result["text"]) > 0
        assert "yes" in result["text"].lower()
        assert result["provider"] == "copilot"
        assert result["session_id"] is not None

    def test_session_continuity(self, require_copilot_cli: None) -> None:
        """Test --resume preserves conversation context."""
        env_vars = prepare_llm_environment(Path.cwd())

        result1 = ask_copilot_cli(
            "Remember this word: elephant. Reply with only 'OK'.",
            timeout=120,
            env_vars=env_vars,
            cwd=str(Path.cwd()),
        )
        assert result1["session_id"] is not None
        session_id = result1["session_id"]

        result2 = ask_copilot_cli(
            "What word did I ask you to remember? Reply with only the word.",
            session_id=session_id,
            timeout=120,
            env_vars=env_vars,
            cwd=str(Path.cwd()),
        )
        assert "elephant" in result2["text"].lower()
        assert result2["session_id"] == session_id

    def test_mcp_tool_usage(self, require_copilot_cli: None) -> None:
        """Test that Copilot can discover and use MCP tools."""
        env_vars = prepare_llm_environment(Path.cwd())

        result = ask_copilot_cli(
            "Use the workspace-read_file MCP tool to read the file 'pyproject.toml' "
            "and tell me the project name. Reply with only the name.",
            timeout=120,
            env_vars=env_vars,
            cwd=str(Path.cwd()),
            execution_dir=str(Path.cwd()),
        )

        assert isinstance(result, dict)
        assert len(result["text"]) > 0
        # The project name should appear in the response
        assert "mcp" in result["text"].lower() or "coder" in result["text"].lower()
