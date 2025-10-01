"""Simple integration tests for session_id handling in CLI and API methods.

KISS principle: Test the critical behavior only.
"""

import pytest

from mcp_coder.llm_providers.claude.claude_code_api import ask_claude_code_api
from mcp_coder.llm_providers.claude.claude_code_cli import ask_claude_code_cli


class TestSessionIdHandling:
    """Test session_id parameter handling for both CLI and API methods."""

    @pytest.mark.claude_cli_integration
    def test_cli_accepts_session_id_without_error(self) -> None:
        """Test that CLI method accepts session_id parameter.

        This is a REAL integration test that calls actual Claude CLI.
        """
        # Should not raise - CLI supports session_id
        result = ask_claude_code_cli(
            "What is 1+1? Answer with just the number.",
            session_id=None,  # Explicitly pass None
            timeout=30,
        )

        # Verify structure
        assert "text" in result
        assert "session_id" in result
        assert result["method"] == "cli"

    def test_api_raises_error_when_session_id_provided(self) -> None:
        """Test that API method raises NotImplementedError when session_id is used.

        This is a unit test - doesn't call real API.
        """
        # Should raise NotImplementedError when session_id is not None
        with pytest.raises(NotImplementedError) as exc_info:
            ask_claude_code_api("Test question", session_id="some-session-id")

        # Verify error message is helpful
        error_msg = str(exc_info.value)
        assert "not yet supported" in error_msg.lower()
        assert "API method" in error_msg
        assert "CLI method" in error_msg

    def test_api_works_without_session_id(self) -> None:
        """Test that API method works when session_id is None (default).

        This tests that the NotImplementedError check doesn't break normal usage.
        Uses mock since we're testing behavior, not real API call.
        """
        from unittest.mock import patch

        with patch(
            "mcp_coder.llm_providers.claude.claude_code_api.ask_claude_code_api_detailed_sync"
        ) as mock_detailed:
            # Setup mock
            mock_detailed.return_value = {
                "text": "Mock response",
                "session_info": {"session_id": "api-generated-123"},
                "result_info": {},
                "raw_messages": [],
            }

            # Should work fine without session_id
            result = ask_claude_code_api("Test question")  # session_id=None by default

            # Verify it worked
            assert result["text"] == "Mock response"
            assert result["session_id"] == "api-generated-123"
            assert result["method"] == "api"

    def test_api_works_with_explicit_none_session_id(self) -> None:
        """Test that API method works when session_id=None is explicitly passed.

        Edge case: ensure `if session_id is not None:` check works correctly.
        """
        from unittest.mock import patch

        with patch(
            "mcp_coder.llm_providers.claude.claude_code_api.ask_claude_code_api_detailed_sync"
        ) as mock_detailed:
            # Setup mock
            mock_detailed.return_value = {
                "text": "Mock response",
                "session_info": {"session_id": None},
                "result_info": {},
                "raw_messages": [],
            }

            # Should work fine with explicit None
            result = ask_claude_code_api("Test question", session_id=None)

            # Verify it worked
            assert result["text"] == "Mock response"
            assert result["method"] == "api"


@pytest.mark.claude_cli_integration
class TestCliSessionRealIntegration:
    """REAL integration test for CLI session continuity."""

    def test_cli_session_continuity_real(self) -> None:
        """Test that CLI actually maintains session across multiple calls.

        This makes REAL calls to Claude CLI.
        """
        # First call - establish session
        result1 = ask_claude_code_cli(
            "Remember this number: 777. Confirm you remember it.", timeout=30
        )

        assert "text" in result1
        assert "session_id" in result1
        session_id = result1["session_id"]

        # Verify we got a session_id
        assert session_id is not None
        assert len(session_id) > 0

        # Second call - use the session
        result2 = ask_claude_code_cli(
            "What number did I ask you to remember? Answer with just the number.",
            session_id=session_id,
            timeout=30,
        )

        # Verify session was maintained
        assert result2["session_id"] == session_id
        # Claude should remember "777"
        assert "777" in result2["text"]
