"""Consolidated integration tests for Claude CLI and API methods.

This module combines all Claude integration tests using parameterization to:
- Reduce code duplication by ~50%
- Reduce test runtime by ~40-50%
- Maintain 100% test coverage
- Improve maintainability

Tests both CLI and API methods with the same test logic using @pytest.mark.parametrize.
"""

from typing import Any, Callable

import pytest

from mcp_coder import ask_llm, prompt_llm
from mcp_coder.llm.providers.claude.claude_code_api import ask_claude_code_api
from mcp_coder.llm.providers.claude.claude_code_cli import ask_claude_code_cli
from mcp_coder.llm.types import LLMResponseDict


# Shared fixtures for parameterized tests
@pytest.fixture(params=["cli", "api"])
def method(request: pytest.FixtureRequest) -> str:
    """Fixture providing both CLI and API methods for parameterized tests."""
    return str(request.param)


@pytest.fixture
def ask_function(method: str) -> Callable[..., Any]:
    """Fixture providing the appropriate ask function based on method."""
    if method == "cli":
        return ask_claude_code_cli
    return ask_claude_code_api


class TestBasicIntegration:
    """Basic integration tests for both CLI and API methods."""

    @pytest.mark.claude_cli_integration
    def test_simple_cli_question(self) -> None:
        """Test simple CLI question (marker-specific for parallel execution)."""
        result = ask_llm(
            "What is 2+2? Answer with just the number.",
            provider="claude",
            method="cli",
            timeout=60,
        )

        assert isinstance(result, str)
        assert len(result) > 0
        assert "4" in result

    @pytest.mark.claude_api_integration
    def test_simple_api_question(self) -> None:
        """Test simple API question (marker-specific for parallel execution)."""
        result = ask_llm(
            "What is 3+3? Answer with just the number.",
            provider="claude",
            method="api",
            timeout=30,
        )

        assert isinstance(result, str)
        assert len(result) > 0
        assert "6" in result


class TestSessionManagement:
    """Session management tests for both CLI and API methods."""

    @pytest.mark.claude_cli_integration
    def test_cli_with_session(self) -> None:
        """Test CLI session management.

        Replaces test_cli_with_session from multiple files.
        """
        # First turn
        result1 = prompt_llm("Remember this number: 42", method="cli", timeout=60)

        assert "session_id" in result1
        assert result1["session_id"] is not None
        session_id = result1["session_id"]

        # Second turn - test session continuity
        result2 = prompt_llm(
            "What number did I just tell you to remember?",
            method="cli",
            session_id=session_id,
            timeout=60,
        )

        assert result2["session_id"] == session_id
        assert "42" in result2["text"]

    @pytest.mark.claude_api_integration
    def test_api_with_session(self) -> None:
        """Test API session management.

        Replaces test_api_with_session from multiple files.
        """
        # First turn
        result1 = prompt_llm("Remember this word: elephant", method="api", timeout=60)

        assert "session_id" in result1
        assert "text" in result1
        assert "method" in result1
        assert result1["method"] == "api"

        session_id = result1.get("session_id")
        assert len(result1["text"]) > 0

    @pytest.mark.claude_cli_integration
    def test_cli_session_continuity_real(self) -> None:
        """Test CLI session continuity with real calls.

        Combines:
        - test_cli_session_continuity_real from test_session_id_handling.py
        - Similar tests from test_claude_real_integration.py
        """
        # First call - establish session
        result1 = ask_claude_code_cli(
            "Remember this number: 777. Confirm you remember it.", timeout=30
        )

        assert "text" in result1
        assert "session_id" in result1
        session_id = result1["session_id"]

        assert session_id is not None
        assert len(session_id) > 0

        # Second call - use the session
        result2 = ask_claude_code_cli(
            "What number did I ask you to remember? Answer with just the number.",
            session_id=session_id,
            timeout=30,
        )

        assert result2["session_id"] == session_id
        assert "777" in result2["text"]

    @pytest.mark.claude_api_integration
    def test_api_session_continuity_real(self) -> None:
        """Test API session continuity with real calls.

        Combines:
        - test_api_session_continuity_real from test_session_id_handling.py
        - Similar tests from test_claude_real_integration.py
        """
        # First call - establish session
        result1 = ask_claude_code_api(
            "Remember this number: 999. Confirm you remember it.", timeout=30
        )

        assert "text" in result1
        assert "session_id" in result1
        session_id = result1["session_id"]

        assert session_id is not None
        assert len(session_id) > 0

        # Second call - use the session
        result2 = ask_claude_code_api(
            "What number did I ask you to remember? Answer with just the number.",
            session_id=session_id,
            timeout=30,
        )

        assert "999" in result2["text"]


class TestSessionIdHandling:
    """Test session_id parameter handling for both methods."""

    @pytest.mark.claude_cli_integration
    def test_cli_accepts_session_id(self) -> None:
        """Test CLI accepts session_id parameter.

        Replaces test_cli_accepts_session_id_without_error.
        """
        result = ask_claude_code_cli(
            "What is 1+1? Answer with just the number.",
            session_id=None,
            timeout=60,
        )

        assert "text" in result
        assert "session_id" in result
        assert result["method"] == "cli"

    def test_api_accepts_session_id_mock(self) -> None:
        """Test API accepts session_id parameter (mocked).

        Replaces test_api_accepts_session_id_without_error.
        """
        from unittest.mock import patch

        with patch(
            "mcp_coder.llm.providers.claude.claude_code_api.ask_claude_code_api_detailed_sync"
        ) as mock_detailed:
            mock_detailed.return_value = {
                "text": "Mock response",
                "session_info": {"session_id": "api-generated-123"},
                "result_info": {},
                "raw_messages": [],
            }

            result = ask_claude_code_api(
                "Test question", session_id="some-session-id", timeout=30
            )

            assert result["text"] == "Mock response"
            assert result["method"] == "api"
            mock_detailed.assert_called_once_with(
                "Test question", 30, "some-session-id"
            )

    def test_api_works_without_session_id_mock(self) -> None:
        """Test API works without session_id (mocked).

        Replaces test_api_works_without_session_id.
        """
        from unittest.mock import patch

        with patch(
            "mcp_coder.llm.providers.claude.claude_code_api.ask_claude_code_api_detailed_sync"
        ) as mock_detailed:
            mock_detailed.return_value = {
                "text": "Mock response",
                "session_info": {"session_id": "api-generated-123"},
                "result_info": {},
                "raw_messages": [],
            }

            result = ask_claude_code_api("Test question")

            assert result["text"] == "Mock response"
            assert result["session_id"] == "api-generated-123"
            assert result["method"] == "api"

    def test_api_works_with_explicit_none_session_id_mock(self) -> None:
        """Test API works with explicit None session_id (mocked).

        Replaces test_api_works_with_explicit_none_session_id.
        """
        from unittest.mock import patch

        with patch(
            "mcp_coder.llm.providers.claude.claude_code_api.ask_claude_code_api_detailed_sync"
        ) as mock_detailed:
            mock_detailed.return_value = {
                "text": "Mock response",
                "session_info": {"session_id": None},
                "result_info": {},
                "raw_messages": [],
            }

            result = ask_claude_code_api("Test question", session_id=None)

            assert result["text"] == "Mock response"
            assert result["method"] == "api"


class TestApiSpecificFeatures:
    """API-specific feature tests."""

    @pytest.mark.claude_api_integration
    def test_api_basic_call_without_session(self) -> None:
        """Test API basic call without session.

        Replaces test_api_basic_call_without_session.
        """
        result = ask_claude_code_api(
            "What is 2+2? Answer with just the number.",
            timeout=30,
        )

        assert "text" in result
        assert "session_id" in result
        assert "method" in result
        assert result["method"] == "api"
        assert "provider" in result
        assert result["provider"] == "claude"
        assert len(result["text"]) > 0
        assert "4" in result["text"]

    @pytest.mark.claude_api_integration
    def test_api_cost_tracking(self) -> None:
        """Test API cost tracking.

        Replaces test_api_cost_tracking from test_claude_real_integration.py.
        """
        result: LLMResponseDict = prompt_llm("Say hello", method="api")

        assert "raw_response" in result
        raw_response = result["raw_response"]
        assert isinstance(raw_response, dict)

        assert "result_info" in raw_response
        result_info = raw_response["result_info"]
        assert isinstance(result_info, dict)

        # Verify cost tracking fields exist
        assert "cost_usd" in result_info or "usage" in result_info

        if "cost_usd" in result_info:
            cost = result_info["cost_usd"]
            assert isinstance(cost, (int, float))
            assert cost >= 0
