"""Integration tests for LLM session management and serialization.

These tests validate end-to-end functionality including:
- Session continuity across multiple turns
- Serialization and deserialization
- Parallel session safety
- Cross-method compatibility (CLI and API)
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder import (
    ask_llm,
    deserialize_llm_response,
    prompt_llm,
    serialize_llm_response,
)
from mcp_coder.llm.types import LLMResponseDict


class MockClaudeCLI:
    """Mock for Claude CLI that simulates real behavior."""

    def __init__(self) -> None:
        """Initialize mock with default response."""
        self.response_dict: Optional[LLMResponseDict] = None
        self.response_text: str = "Mock response"
        self.received_session_id: Optional[str] = None
        self.call_count: int = 0
        self.error_on_invalid_session: bool = False

    def set_response_dict(self, response: LLMResponseDict) -> None:
        """Set the mock to return a specific response dict."""
        self.response_dict = response

    def set_response(self, text: str) -> None:
        """Set the mock to return a simple text response."""
        self.response_text = text

    def set_error_on_invalid_session(self, error: bool) -> None:
        """Configure mock to error on invalid session IDs."""
        self.error_on_invalid_session = error

    def __call__(
        self,
        question: str,
        session_id: Optional[str] = None,
        timeout: int = 30,
        cwd: Optional[str] = None,
        env_vars: Optional[Dict[str, str]] = None,
        mcp_config: Optional[str] = None,
    ) -> LLMResponseDict:
        """Simulate CLI call."""
        self.call_count += 1
        self.received_session_id = session_id

        if (
            self.error_on_invalid_session
            and session_id
            and session_id.startswith("nonexistent")
        ):
            raise ValueError(f"Invalid session_id: {session_id}")

        if self.response_dict:
            return self.response_dict

        # Default response
        return {
            "version": "1.0",
            "timestamp": "2025-10-01T10:30:00",
            "text": self.response_text,
            "session_id": session_id or "mock-session",
            "method": "cli",
            "provider": "claude",
            "raw_response": {},
        }


class MockClaudeAPI:
    """Mock for Claude API that simulates real behavior."""

    def __init__(self) -> None:
        """Initialize mock with default response."""
        self.response_dict: Optional[LLMResponseDict] = None
        self.response_text: str = "Mock API response"
        self.received_session_id: Optional[str] = None
        self.call_count: int = 0

    def set_response_dict(self, response: LLMResponseDict) -> None:
        """Set the mock to return a specific response dict."""
        self.response_dict = response

    def set_response(self, text: str) -> None:
        """Set the mock to return a simple text response."""
        self.response_text = text

    def __call__(
        self,
        question: str,
        session_id: Optional[str] = None,
        timeout: int = 30,
        env_vars: Optional[Dict[str, str]] = None,
        cwd: Optional[str] = None,
        mcp_config: Optional[str] = None,
    ) -> LLMResponseDict:
        """Simulate API call."""
        self.call_count += 1
        self.received_session_id = session_id

        if self.response_dict:
            return self.response_dict

        # Default response
        return {
            "version": "1.0",
            "timestamp": "2025-10-01T10:30:00",
            "text": self.response_text,
            "session_id": session_id or "mock-api-session",
            "method": "api",
            "provider": "claude",
            "raw_response": {},
        }


@pytest.fixture
def mock_claude_cli() -> MockClaudeCLI:
    """Fixture providing mock for Claude CLI."""
    return MockClaudeCLI()


@pytest.fixture
def mock_claude_api() -> MockClaudeAPI:
    """Fixture providing mock for Claude API."""
    return MockClaudeAPI()


@pytest.mark.claude_cli_integration
class TestSessionContinuity:
    """Test session continuity across multiple turns."""

    def test_session_continuity_cli(self, mock_claude_cli: MockClaudeCLI) -> None:
        """Test multi-turn conversation with CLI method."""
        with patch(
            "mcp_coder.llm.interface.ask_claude_code_cli",
            mock_claude_cli,
        ):
            # First turn
            mock_claude_cli.set_response_dict(
                {
                    "version": "1.0",
                    "timestamp": "2025-10-01T10:30:00",
                    "text": "Your favorite color is blue.",
                    "session_id": "session-123",
                    "method": "cli",
                    "provider": "claude",
                    "raw_response": {},
                }
            )

            result1 = prompt_llm("My favorite color is blue", method="cli")
            session_id = result1["session_id"]
            assert session_id == "session-123"

            # Second turn with same session
            mock_claude_cli.set_response_dict(
                {
                    "version": "1.0",
                    "timestamp": "2025-10-01T10:31:00",
                    "text": "You told me your favorite color is blue.",
                    "session_id": "session-123",
                    "method": "cli",
                    "provider": "claude",
                    "raw_response": {},
                }
            )

            result2 = prompt_llm(
                "What's my favorite color?", method="cli", session_id=session_id
            )

            # Validate session continuity
            assert result2["session_id"] == session_id
            assert mock_claude_cli.received_session_id == session_id
            assert "blue" in result2["text"].lower()

    def test_session_continuity_api(self, mock_claude_api: MockClaudeAPI) -> None:
        """Test multi-turn conversation with API method."""
        with patch(
            "mcp_coder.llm.interface.ask_claude_code_api",
            mock_claude_api,
        ):
            # First turn
            mock_claude_api.set_response_dict(
                {
                    "version": "1.0",
                    "timestamp": "2025-10-01T10:30:00",
                    "text": "Your favorite color is red.",
                    "session_id": "api-session-456",
                    "method": "api",
                    "provider": "claude",
                    "raw_response": {},
                }
            )

            result1 = prompt_llm("My favorite color is red", method="api")
            session_id = result1["session_id"]
            assert session_id == "api-session-456"

            # Second turn
            mock_claude_api.set_response_dict(
                {
                    "version": "1.0",
                    "timestamp": "2025-10-01T10:31:00",
                    "text": "You said your favorite color is red.",
                    "session_id": "api-session-456",
                    "method": "api",
                    "provider": "claude",
                    "raw_response": {},
                }
            )

            result2 = prompt_llm(
                "What's my color?", method="api", session_id=session_id
            )

            assert result2["session_id"] == session_id
            assert mock_claude_api.received_session_id == session_id

    def test_multi_turn_conversation(self, mock_claude_cli: MockClaudeCLI) -> None:
        """Test conversation with 3+ turns."""
        with patch(
            "mcp_coder.llm.interface.ask_claude_code_cli",
            mock_claude_cli,
        ):
            session_id = "multi-turn-session"

            # Turn 1
            mock_claude_cli.set_response_dict(
                {
                    "version": "1.0",
                    "timestamp": "2025-10-01T10:30:00",
                    "text": "Got it, your name is Alice.",
                    "session_id": session_id,
                    "method": "cli",
                    "provider": "claude",
                    "raw_response": {},
                }
            )
            result1 = prompt_llm("My name is Alice", method="cli")

            # Turn 2
            mock_claude_cli.set_response_dict(
                {
                    "version": "1.0",
                    "timestamp": "2025-10-01T10:31:00",
                    "text": "Your favorite color is green.",
                    "session_id": session_id,
                    "method": "cli",
                    "provider": "claude",
                    "raw_response": {},
                }
            )
            result2 = prompt_llm(
                "My favorite color is green", method="cli", session_id=session_id
            )

            # Turn 3
            mock_claude_cli.set_response_dict(
                {
                    "version": "1.0",
                    "timestamp": "2025-10-01T10:32:00",
                    "text": "Your name is Alice and your favorite color is green.",
                    "session_id": session_id,
                    "method": "cli",
                    "provider": "claude",
                    "raw_response": {},
                }
            )
            result3 = prompt_llm(
                "What's my name and color?", method="cli", session_id=session_id
            )

            # All should have same session_id
            assert result1["session_id"] == session_id
            assert result2["session_id"] == session_id
            assert result3["session_id"] == session_id


@pytest.mark.claude_cli_integration
class TestSerialization:
    """Test serialization and deserialization workflows."""

    def test_serialization_roundtrip(
        self, mock_claude_cli: MockClaudeCLI, tmp_path: Path
    ) -> None:
        """Test save and load preserves all data."""
        with patch(
            "mcp_coder.llm.interface.ask_claude_code_cli",
            mock_claude_cli,
        ):
            mock_claude_cli.set_response_dict(
                {
                    "version": "1.0",
                    "timestamp": "2025-10-01T10:30:00",
                    "text": "Test response",
                    "session_id": "serialize-test",
                    "method": "cli",
                    "provider": "claude",
                    "raw_response": {
                        "duration_ms": 2801,
                        "cost_usd": 0.058,
                        "usage": {"input_tokens": 100, "output_tokens": 50},
                    },
                }
            )

            result = prompt_llm("Test question", method="cli")

            # Save to file
            filepath = tmp_path / "conversation.json"
            serialize_llm_response(result, str(filepath))

            # Load from file
            loaded = deserialize_llm_response(str(filepath))

            # Verify all data preserved
            assert loaded["text"] == result["text"]
            assert loaded["session_id"] == result["session_id"]
            assert loaded["version"] == result["version"]
            assert loaded["raw_response"]["duration_ms"] == 2801
            assert loaded["raw_response"]["cost_usd"] == 0.058

    def test_session_from_saved_file(
        self, mock_claude_cli: MockClaudeCLI, tmp_path: Path
    ) -> None:
        """Test resuming session from saved file."""
        with patch(
            "mcp_coder.llm.interface.ask_claude_code_cli",
            mock_claude_cli,
        ):
            # First conversation
            mock_claude_cli.set_response_dict(
                {
                    "version": "1.0",
                    "timestamp": "2025-10-01T10:30:00",
                    "text": "Conversation started",
                    "session_id": "saved-session",
                    "method": "cli",
                    "provider": "claude",
                    "raw_response": {},
                }
            )
            result1 = prompt_llm("Start conversation", method="cli")

            # Save session
            filepath = tmp_path / f"{result1['session_id']}.json"
            serialize_llm_response(result1, str(filepath))

            # Later: Load session_id and continue
            loaded = deserialize_llm_response(str(filepath))
            session_id = loaded["session_id"]

            mock_claude_cli.set_response_dict(
                {
                    "version": "1.0",
                    "timestamp": "2025-10-01T10:35:00",
                    "text": "Continuing from saved session",
                    "session_id": session_id,
                    "method": "cli",
                    "provider": "claude",
                    "raw_response": {},
                }
            )
            result2 = prompt_llm("Continue", method="cli", session_id=session_id)

            assert result2["session_id"] == session_id


@pytest.mark.claude_cli_integration
class TestParallelSafety:
    """Test that parallel sessions don't interfere."""

    def test_parallel_sessions_cli(self, mock_claude_cli: MockClaudeCLI) -> None:
        """Test two independent sessions running in parallel."""
        with patch(
            "mcp_coder.llm.interface.ask_claude_code_cli",
            mock_claude_cli,
        ):
            # Session 1: Color is blue
            mock_claude_cli.set_response_dict(
                {
                    "version": "1.0",
                    "timestamp": "2025-10-01T10:30:00",
                    "text": "Your color is blue",
                    "session_id": "session-1",
                    "method": "cli",
                    "provider": "claude",
                    "raw_response": {},
                }
            )
            result1a = prompt_llm("My color is blue", method="cli")
            session1_id = result1a["session_id"]

            # Session 2: Color is red
            mock_claude_cli.set_response_dict(
                {
                    "version": "1.0",
                    "timestamp": "2025-10-01T10:30:00",
                    "text": "Your color is red",
                    "session_id": "session-2",
                    "method": "cli",
                    "provider": "claude",
                    "raw_response": {},
                }
            )
            result2a = prompt_llm("My color is red", method="cli")
            session2_id = result2a["session_id"]

            # Sessions should have different IDs
            assert session1_id != session2_id

            # Continue session 1
            mock_claude_cli.set_response_dict(
                {
                    "version": "1.0",
                    "timestamp": "2025-10-01T10:31:00",
                    "text": "You said blue",
                    "session_id": "session-1",
                    "method": "cli",
                    "provider": "claude",
                    "raw_response": {},
                }
            )
            result1b = prompt_llm(
                "What was my color?", method="cli", session_id=session1_id
            )

            # Continue session 2
            mock_claude_cli.set_response_dict(
                {
                    "version": "1.0",
                    "timestamp": "2025-10-01T10:31:00",
                    "text": "You said red",
                    "session_id": "session-2",
                    "method": "cli",
                    "provider": "claude",
                    "raw_response": {},
                }
            )
            result2b = prompt_llm(
                "What was my color?", method="cli", session_id=session2_id
            )

            # Each session maintains its own context
            assert result1b["session_id"] == session1_id
            assert result2b["session_id"] == session2_id
            assert "blue" in result1b["text"].lower()
            assert "red" in result2b["text"].lower()

    def test_parallel_sessions_different_methods(
        self, mock_claude_cli: MockClaudeCLI, mock_claude_api: MockClaudeAPI
    ) -> None:
        """Test CLI and API sessions can run independently."""
        with (
            patch(
                "mcp_coder.llm.interface.ask_claude_code_cli",
                mock_claude_cli,
            ),
            patch(
                "mcp_coder.llm.interface.ask_claude_code_api",
                mock_claude_api,
            ),
        ):
            # CLI session
            mock_claude_cli.set_response_dict(
                {
                    "version": "1.0",
                    "timestamp": "2025-10-01T10:30:00",
                    "text": "CLI session",
                    "session_id": "cli-session",
                    "method": "cli",
                    "provider": "claude",
                    "raw_response": {},
                }
            )
            cli_result = prompt_llm("CLI test", method="cli")

            # API session
            mock_claude_api.set_response_dict(
                {
                    "version": "1.0",
                    "timestamp": "2025-10-01T10:30:00",
                    "text": "API session",
                    "session_id": "api-session",
                    "method": "api",
                    "provider": "claude",
                    "raw_response": {},
                }
            )
            api_result = prompt_llm("API test", method="api")

            # Different sessions
            assert cli_result["session_id"] != api_result["session_id"]
            assert cli_result["method"] == "cli"
            assert api_result["method"] == "api"


@pytest.mark.claude_cli_integration
class TestMetadataTracking:
    """Test metadata preservation and cost tracking."""

    def test_metadata_preserved_through_workflow(
        self, mock_claude_cli: MockClaudeCLI, tmp_path: Path
    ) -> None:
        """Test that metadata is preserved through complete workflow."""
        with patch(
            "mcp_coder.llm.interface.ask_claude_code_cli",
            mock_claude_cli,
        ):
            mock_claude_cli.set_response_dict(
                {
                    "version": "1.0",
                    "timestamp": "2025-10-01T10:30:00",
                    "text": "Response with metadata",
                    "session_id": "meta-session",
                    "method": "cli",
                    "provider": "claude",
                    "raw_response": {
                        "duration_ms": 2801,
                        "cost_usd": 0.058,
                        "usage": {
                            "input_tokens": 100,
                            "output_tokens": 50,
                            "cache_creation_input_tokens": 0,
                            "cache_read_input_tokens": 0,
                        },
                    },
                }
            )

            # Get response
            result = prompt_llm("Test with metadata", method="cli")

            # Verify metadata present
            assert result["raw_response"]["duration_ms"] == 2801
            assert result["raw_response"]["cost_usd"] == 0.058
            usage_dict = result["raw_response"].get("usage", {})
            assert isinstance(usage_dict, dict)
            assert usage_dict.get("input_tokens") == 100

            # Save and load
            filepath = tmp_path / "metadata_test.json"
            serialize_llm_response(result, str(filepath))
            loaded = deserialize_llm_response(str(filepath))

            # Metadata still present after serialization
            assert loaded["raw_response"]["duration_ms"] == 2801
            assert loaded["raw_response"]["cost_usd"] == 0.058

    def test_cost_tracking_across_sessions(
        self, mock_claude_cli: MockClaudeCLI
    ) -> None:
        """Test accumulating costs across conversation turns."""
        with patch(
            "mcp_coder.llm.interface.ask_claude_code_cli",
            mock_claude_cli,
        ):
            session_id = "cost-tracking"
            total_cost = 0.0

            # Turn 1
            mock_claude_cli.set_response_dict(
                {
                    "version": "1.0",
                    "timestamp": "2025-10-01T10:30:00",
                    "text": "Turn 1",
                    "session_id": session_id,
                    "method": "cli",
                    "provider": "claude",
                    "raw_response": {"cost_usd": 0.025},
                }
            )
            result1 = prompt_llm("Question 1", method="cli")
            cost1 = result1["raw_response"].get("cost_usd", 0)
            assert isinstance(cost1, (int, float))
            total_cost += float(cost1)

            # Turn 2
            mock_claude_cli.set_response_dict(
                {
                    "version": "1.0",
                    "timestamp": "2025-10-01T10:31:00",
                    "text": "Turn 2",
                    "session_id": session_id,
                    "method": "cli",
                    "provider": "claude",
                    "raw_response": {"cost_usd": 0.033},
                }
            )
            result2 = prompt_llm("Question 2", method="cli", session_id=session_id)
            cost2 = result2["raw_response"].get("cost_usd", 0)
            assert isinstance(cost2, (int, float))
            total_cost += float(cost2)

            # Can track total cost
            assert total_cost == pytest.approx(0.058)


@pytest.mark.claude_cli_integration
class TestErrorHandling:
    """Test error handling in integration scenarios."""

    def test_invalid_session_id_handled(self, mock_claude_cli: MockClaudeCLI) -> None:
        """Test behavior with invalid session_id."""
        with patch(
            "mcp_coder.llm.interface.ask_claude_code_cli",
            mock_claude_cli,
        ):
            mock_claude_cli.set_error_on_invalid_session(True)

            # Attempting to use non-existent session
            with pytest.raises(ValueError, match="Invalid session_id"):
                prompt_llm("Test", method="cli", session_id="nonexistent-session")

    def test_missing_fields_in_serialized_data(self, tmp_path: Path) -> None:
        """Test handling of incomplete serialized data."""
        # Create file with minimal data
        filepath = tmp_path / "minimal.json"
        minimal_data = {
            "version": "1.0",
            "text": "Minimal response",
            # Missing other fields
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(minimal_data, f)

        # Should load with best effort
        loaded = deserialize_llm_response(str(filepath))
        assert loaded["version"] == "1.0"
        assert loaded["text"] == "Minimal response"


@pytest.mark.claude_cli_integration
class TestBackwardCompatibility:
    """Test backward compatibility with existing code."""

    def test_ask_llm_still_works(self, mock_claude_cli: MockClaudeCLI) -> None:
        """Test that ask_llm (simple interface) still works."""
        with patch("mcp_coder.llm.interface.ask_claude_code") as mock_ask_claude_code:
            mock_ask_claude_code.return_value = "Simple response"

            response = ask_llm("Simple question")

            # Should return string as before
            assert isinstance(response, str)
            assert response == "Simple response"

    def test_ask_llm_without_session_id(self, mock_claude_cli: MockClaudeCLI) -> None:
        """Test ask_llm works without session_id parameter."""
        with patch("mcp_coder.llm.interface.ask_claude_code") as mock_ask_claude_code:
            mock_ask_claude_code.return_value = "No session needed"

            # Old calling pattern should still work
            response = ask_llm("Question", provider="claude", method="cli", timeout=30)

            assert response == "No session needed"
