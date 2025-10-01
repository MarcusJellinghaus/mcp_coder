"""Real integration tests that call actual Claude CLI and API.

These tests make REAL calls to Claude services and should only be run when:
1. Claude CLI is installed and configured
2. Network access is available
3. API credentials are set up

Run with: pytest -m claude_cli_integration or -m claude_api_integration
"""

import pytest

from mcp_coder import ask_llm, prompt_llm


@pytest.mark.claude_cli_integration
class TestRealClaudeCLI:
    """Integration tests using REAL Claude CLI executable."""

    def test_simple_cli_question(self) -> None:
        """Test that we can ask Claude a simple question via CLI.

        This test makes a REAL call to Claude CLI.
        """
        result = ask_llm(
            "What is 2+2? Answer with just the number.",
            provider="claude",
            method="cli",
            timeout=30,
        )

        # Verify we got a response
        assert isinstance(result, str)
        assert len(result) > 0
        # Claude should answer with "4" or something containing "4"
        assert "4" in result

    def test_cli_with_session(self) -> None:
        """Test CLI with session management.

        This test makes REAL calls to Claude CLI with sessions.
        """
        # First turn
        result1 = prompt_llm("Remember this number: 42", method="cli")

        assert "session_id" in result1
        assert result1["session_id"] is not None
        session_id = result1["session_id"]

        # Second turn - test session continuity
        result2 = prompt_llm(
            "What number did I just tell you to remember?",
            method="cli",
            session_id=session_id,
        )

        assert result2["session_id"] == session_id
        # Claude should remember "42"
        assert "42" in result2["text"]


@pytest.mark.claude_api_integration
class TestRealClaudeAPI:
    """Integration tests using REAL Claude API."""

    def test_simple_api_question(self) -> None:
        """Test that we can ask Claude a simple question via API.

        This test makes a REAL call to Claude API.
        """
        result = ask_llm(
            "What is 3+3? Answer with just the number.",
            provider="claude",
            method="api",
            timeout=30,
        )

        # Verify we got a response
        assert isinstance(result, str)
        assert len(result) > 0
        # Claude should answer with "6" or something containing "6"
        assert "6" in result

    def test_api_with_session(self) -> None:
        """Test API with session management.

        NOTE: Session continuation is not yet implemented in the API method.
        The API returns a session_id but doesn't support passing it in for continuation.
        This test validates that session_id is returned (even if None currently).
        """
        # First turn
        result1 = prompt_llm("Remember this word: elephant", method="api")

        # Verify response structure
        assert "session_id" in result1
        assert "text" in result1
        assert "method" in result1
        assert result1["method"] == "api"

        # Note: session_id may be None if SDK doesn't provide it yet
        # This is expected until session management is fully implemented
        session_id = result1.get("session_id")

        # For now, just verify the response was successful
        assert len(result1["text"]) > 0

    def test_api_cost_tracking(self) -> None:
        """Test that API returns cost information.

        This test makes a REAL call to verify cost tracking works.
        """
        result = prompt_llm("Say hello", method="api")

        # Verify response structure
        assert "raw_response" in result
        raw_response = result["raw_response"]

        # Cost info is in raw_response.result_info
        assert "result_info" in raw_response
        result_info = raw_response["result_info"]

        # Verify cost tracking fields exist
        assert "cost_usd" in result_info or "usage" in result_info

        # If cost_usd exists, verify it's a reasonable value
        if "cost_usd" in result_info:
            cost = result_info["cost_usd"]
            assert isinstance(cost, (int, float))
            assert cost >= 0  # Cost should be non-negative
