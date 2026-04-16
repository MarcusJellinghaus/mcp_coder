"""Tests for usage extraction and summation in langchain provider."""

from unittest.mock import MagicMock, patch

_MOD = "mcp_coder.llm.providers.langchain"


# ---------------------------------------------------------------------------
# _extract_usage / _sum_usage tests
# ---------------------------------------------------------------------------


class TestExtractUsage:
    """_extract_usage maps LangChain usage_metadata onto UsageInfo."""

    def test_extract_usage_full_metadata(self) -> None:
        """AIMessage with full usage_metadata yields all 4 UsageInfo fields."""
        from mcp_coder.llm.providers.langchain._usage import _extract_usage

        ai_msg = MagicMock()
        ai_msg.usage_metadata = {
            "input_tokens": 1200,
            "output_tokens": 800,
            "total_tokens": 2000,
            "input_token_details": {
                "cache_read": 540,
                "cache_creation": 100,
            },
        }
        usage = _extract_usage(ai_msg)
        assert usage == {
            "input_tokens": 1200,
            "output_tokens": 800,
            "cache_read_input_tokens": 540,
            "cache_creation_input_tokens": 100,
        }

    def test_extract_usage_no_metadata(self) -> None:
        """Missing/empty usage_metadata returns empty dict in all cases."""
        from mcp_coder.llm.providers.langchain._usage import _extract_usage

        # Case (a): attribute absent on message
        class _NoAttr:
            pass

        assert _extract_usage(_NoAttr()) == {}

        # Case (b): usage_metadata is None
        msg_none = MagicMock(spec=[])  # no default usage_metadata attr
        msg_none.usage_metadata = None
        assert _extract_usage(msg_none) == {}

        # Case (c): usage_metadata is empty dict
        msg_empty = MagicMock(spec=[])
        msg_empty.usage_metadata = {}
        assert _extract_usage(msg_empty) == {}

    def test_extract_usage_no_cache_details(self) -> None:
        """usage_metadata with tokens but no input_token_details yields 2 fields."""
        from mcp_coder.llm.providers.langchain._usage import _extract_usage

        ai_msg = MagicMock()
        ai_msg.usage_metadata = {
            "input_tokens": 500,
            "output_tokens": 250,
            "total_tokens": 750,
        }
        usage = _extract_usage(ai_msg)
        assert usage == {"input_tokens": 500, "output_tokens": 250}


class TestSumUsage:
    """_sum_usage adds two UsageInfo dicts field-by-field, always 4 keys."""

    def test_sum_usage_basic(self) -> None:
        """Sum two dicts with all fields present."""
        from mcp_coder.llm.providers.langchain._usage import _sum_usage
        from mcp_coder.llm.types import UsageInfo

        a: UsageInfo = {
            "input_tokens": 100,
            "output_tokens": 50,
            "cache_read_input_tokens": 10,
            "cache_creation_input_tokens": 5,
        }
        b: UsageInfo = {
            "input_tokens": 200,
            "output_tokens": 75,
            "cache_read_input_tokens": 20,
            "cache_creation_input_tokens": 15,
        }
        assert _sum_usage(a, b) == {
            "input_tokens": 300,
            "output_tokens": 125,
            "cache_read_input_tokens": 30,
            "cache_creation_input_tokens": 20,
        }

    def test_sum_usage_partial_keys(self) -> None:
        """One dict has cache, other doesn't — all 4 keys present in result."""
        from mcp_coder.llm.providers.langchain._usage import _sum_usage
        from mcp_coder.llm.types import UsageInfo

        a: UsageInfo = {"input_tokens": 100, "output_tokens": 50}
        b: UsageInfo = {
            "input_tokens": 200,
            "output_tokens": 100,
            "cache_read_input_tokens": 30,
            "cache_creation_input_tokens": 5,
        }
        assert _sum_usage(a, b) == {
            "input_tokens": 300,
            "output_tokens": 150,
            "cache_read_input_tokens": 30,
            "cache_creation_input_tokens": 5,
        }


class TestAskTextIncludesUsage:
    """_ask_text populates raw_response['usage'] via _extract_usage."""

    def _make_config(self, backend: str = "openai") -> dict[str, str | None]:
        return {
            "provider": "langchain",
            "backend": backend,
            "model": "gpt-4o",
            "api_key": None,
            "endpoint": None,
            "api_version": None,
        }

    def test_ask_text_includes_usage(self) -> None:
        """chat_model.invoke() returning AIMessage with usage_metadata populates usage."""
        mock_model = MagicMock()
        mock_ai_msg = MagicMock()
        mock_ai_msg.content = "Hello!"
        mock_ai_msg.model_dump.return_value = {"type": "ai", "content": "Hello!"}
        mock_ai_msg.usage_metadata = {
            "input_tokens": 42,
            "output_tokens": 7,
            "input_token_details": {"cache_read": 3, "cache_creation": 1},
        }
        mock_model.invoke.return_value = mock_ai_msg

        with (
            patch(
                f"{_MOD}._load_langchain_config",
                return_value=self._make_config(),
            ),
            patch(f"{_MOD}.load_langchain_history", return_value=[]),
            patch(f"{_MOD}.store_langchain_history"),
            patch(f"{_MOD}._create_chat_model", return_value=mock_model),
        ):
            from mcp_coder.llm.providers.langchain import ask_langchain

            result = ask_langchain("Hi")

        assert result["raw_response"]["usage"] == {
            "input_tokens": 42,
            "output_tokens": 7,
            "cache_read_input_tokens": 3,
            "cache_creation_input_tokens": 1,
        }
