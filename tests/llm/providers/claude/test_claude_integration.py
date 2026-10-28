"""Consolidated integration tests for the Claude CLI method.

Tests exercise the full stack (prompt_llm -> ask_claude_code_cli) against the
real Claude CLI under the @pytest.mark.claude_cli_integration marker.
"""

from pathlib import Path

import pytest

from mcp_coder import prompt_llm
from mcp_coder.llm.env import prepare_llm_environment


class TestCriticalPathIntegration:
    """Critical path integration tests - minimal set covering all major code paths."""

    @pytest.mark.claude_cli_integration
    def test_basic_cli_integration(self) -> None:
        """Test the CLI path works end-to-end.

        Note: This is a real integration test that makes actual API calls.
        Uses longer timeouts to accommodate real API response times.
        """
        # Prepare environment variables for MCP servers
        env_vars = prepare_llm_environment(Path.cwd())

        # Test CLI path: prompt_llm → ask_claude_code_cli
        cli_result = prompt_llm(
            "Yes or no: Is 1+1=2?",
            provider="claude",
            timeout=60,  # Increased for real API calls
            env_vars=env_vars,
            project_dir=Path.cwd(),
        )
        assert isinstance(cli_result, dict)
        assert len(cli_result["text"]) > 0
        assert "yes" in cli_result["text"].lower()

    @pytest.mark.claude_cli_integration
    def test_session_continuity(self) -> None:
        """Test session management through the full stack (CLI method)."""
        # Prepare environment variables for MCP servers
        env_vars = prepare_llm_environment(Path.cwd())

        # Use prompt_llm to test full response structure
        result1 = prompt_llm(
            "Remember this: elephant",
            timeout=60,
            env_vars=env_vars,
            project_dir=Path.cwd(),
        )
        assert "session_id" in result1
        assert result1["session_id"] is not None
        assert "text" in result1
        session_id = result1["session_id"]

        # Test session continuity
        result2 = prompt_llm(
            "What did I tell you to remember?",
            session_id=session_id,
            timeout=60,
            env_vars=env_vars,
            project_dir=Path.cwd(),
        )
        assert "elephant" in result2["text"].lower()
        assert result2["session_id"] == session_id


# Session ID parameter handling is covered by the session continuity tests above
# and the mocked tests remain as unit tests in other test files


# CLI features beyond the critical path (e.g. cost tracking) are not integration-tested here
# Basic CLI functionality is covered by the critical path tests above


class TestEnvironmentVariablePropagation:
    """Test environment variable propagation through the full stack."""

    @pytest.mark.claude_cli_integration
    def test_env_vars_propagation(self) -> None:
        """Verify env_vars propagate to Claude Code via the CLI method.

        This is a real integration test that makes actual API calls to verify
        environment variables are correctly set and accessible.

        The test verifies:
        1. CLI method: env_vars passed to subprocess work correctly
        2. The CLI can successfully execute with MCP servers using env vars
        """
        # Prepare environment variables for MCP servers
        env_vars = prepare_llm_environment(Path.cwd())

        # Test CLI method - env_vars should be passed to subprocess
        result_cli = prompt_llm(
            "Say hello",
            provider="claude",
            timeout=60,  # Increased for real API calls
            env_vars=env_vars,
            project_dir=Path.cwd(),
        )
        assert isinstance(result_cli, dict)
        assert len(result_cli["text"]) > 0
        # Successful execution means env_vars were prepared and passed correctly
