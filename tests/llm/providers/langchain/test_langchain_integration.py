"""Integration tests for mcp_coder.llm.providers.langchain.

These tests send real API requests to the configured backend.
They are skipped automatically when no credentials are configured.

Run with:
    pytest tests/llm/providers/langchain/test_langchain_integration.py \
           -m langchain_integration -v -s

For CI secrets configuration see .github/workflows/langchain-integration.yml.
"""

import os

import pytest

from mcp_coder.llm.providers.langchain import _load_langchain_config

pytestmark = pytest.mark.langchain_integration


def _require_langchain_config() -> None:
    """Skip the test if LangChain is not configured with valid credentials."""
    try:
        cfg = _load_langchain_config()
    except Exception as exc:  # pylint: disable=broad-except
        pytest.skip(f"Could not load langchain config: {exc}")

    if not cfg.get("backend"):
        pytest.skip("llm.langchain.backend not set in config.toml")
    if not cfg.get("model"):
        pytest.skip("llm.langchain.model not set in config.toml")

    backend = cfg["backend"]
    if backend == "openai":
        if not os.getenv("OPENAI_API_KEY") and not cfg.get("api_key"):
            pytest.skip(
                "No OpenAI credentials: set OPENAI_API_KEY or [llm.langchain] api_key"
            )
    elif backend == "gemini":
        if not os.getenv("GEMINI_API_KEY") and not cfg.get("api_key"):
            pytest.skip(
                "No Gemini credentials: set GEMINI_API_KEY or [llm.langchain] api_key"
            )
    elif backend == "anthropic":
        if not os.getenv("ANTHROPIC_API_KEY") and not cfg.get("api_key"):
            pytest.skip(
                "No Anthropic credentials: set ANTHROPIC_API_KEY "
                "or [llm.langchain] api_key"
            )


class TestLangchainIntegration:
    """Real API integration tests. Skipped unless [llm.langchain] is configured."""

    def test_ask_langchain_returns_valid_response(self) -> None:
        """ask_langchain sends a real question and returns a valid LLMResponseDict."""
        _require_langchain_config()
        from mcp_coder.llm.providers.langchain import ask_langchain

        result = ask_langchain("Reply with exactly the word: hello")

        assert result["provider"] == "langchain"
        assert result["method"] == "api"
        assert isinstance(result["text"], str)
        assert len(result["text"].strip()) > 0
        assert result["session_id"] is not None
        assert "raw_response" in result

    def test_session_continuity(self) -> None:
        """Second call with session_id remembers context from the first call."""
        _require_langchain_config()
        from mcp_coder.llm.providers.langchain import ask_langchain

        result1 = ask_langchain("My favourite colour is purple. Acknowledge with OK.")
        session_id = result1["session_id"]

        result2 = ask_langchain(
            "What colour did I just mention?", session_id=session_id
        )
        assert "purple" in result2["text"].lower()
        assert result2["session_id"] == session_id
