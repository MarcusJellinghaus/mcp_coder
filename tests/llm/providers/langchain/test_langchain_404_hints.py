"""404 / model-not-found hint tests for the langchain provider.

Covers the shared detection predicate (``_is_404_error``) and the hint
formatter (``_format_404_hint``) as exercised through both the non-streaming
``_ask_text`` path and the streaming ``_ask_text_stream`` path.
"""

from unittest.mock import MagicMock, patch

import pytest

_MOD_LC = "mcp_coder.llm.providers.langchain"
_SUGGEST = f"{_MOD_LC}._errors_404._get_model_suggestions"


class TestAskTextModelNotFound:
    """Tests for model-not-found error handling in _ask_text."""

    def _make_config(self, backend: str = "openai") -> dict[str, str | None]:
        return {
            "provider": "langchain",
            "backend": backend,
            "model": "bad-model",
            "api_key": None,
            "endpoint": None,
            "api_version": None,
        }

    @pytest.mark.parametrize(
        "error_message",
        [
            "Error code: 404 - The model 'bad-model' does not exist",
            "NOT_FOUND: model not registered",
            "model 'foo' not found",
            "Model 'foo' Not Found",
        ],
    )
    def test_404_error_raises_value_error_with_model_hint(
        self, error_message: str
    ) -> None:
        """NOT_FOUND-style errors raise ValueError with model name + suggestions."""
        mock_model = MagicMock()
        mock_model.invoke.side_effect = Exception(error_message)
        with (
            patch(
                f"{_MOD_LC}._load_langchain_config",
                return_value=self._make_config(),
            ),
            patch(
                f"{_MOD_LC}.load_langchain_history",
                return_value=[],
            ),
            patch(
                f"{_MOD_LC}._create_chat_model",
                return_value=mock_model,
            ),
            patch(
                _SUGGEST,
                return_value="\n\nAvailable models:\n  - gpt-4o",
            ),
        ):
            from mcp_coder.llm.providers.langchain import ask_langchain

            with pytest.raises(ValueError) as exc_info:
                ask_langchain("question")
        assert "bad-model" in str(exc_info.value)
        assert "gpt-4o" in str(exc_info.value)

    def test_not_found_error_raised_even_when_suggestions_fail(self) -> None:
        """404 still raises ValueError even if model listing fails."""
        mock_model = MagicMock()
        mock_model.invoke.side_effect = Exception("404 not_found_error")
        with (
            patch(
                f"{_MOD_LC}._load_langchain_config",
                return_value=self._make_config(),
            ),
            patch(
                f"{_MOD_LC}.load_langchain_history",
                return_value=[],
            ),
            patch(
                f"{_MOD_LC}._create_chat_model",
                return_value=mock_model,
            ),
            patch(
                _SUGGEST,
                side_effect=Exception("network error"),
            ),
        ):
            from mcp_coder.llm.providers.langchain import ask_langchain

            with pytest.raises(ValueError, match="not found"):
                ask_langchain("question")

    def test_non_404_exception_is_reraised_unchanged(self) -> None:
        """Non-404 exceptions propagate as-is without wrapping."""
        mock_model = MagicMock()
        mock_model.invoke.side_effect = RuntimeError("network timeout")
        with (
            patch(
                f"{_MOD_LC}._load_langchain_config",
                return_value=self._make_config(),
            ),
            patch(
                f"{_MOD_LC}.load_langchain_history",
                return_value=[],
            ),
            patch(
                f"{_MOD_LC}._create_chat_model",
                return_value=mock_model,
            ),
        ):
            from mcp_coder.llm.providers.langchain import ask_langchain

            with pytest.raises(RuntimeError, match="network timeout"):
                ask_langchain("question")

    def _make_endpoint_config(
        self,
        backend: str = "openai",
        endpoint: str | None = "https://h/v1",
        api_version: str | None = None,
    ) -> dict[str, str | None]:
        return {
            "provider": "langchain",
            "backend": backend,
            "model": "bad-model",
            "api_key": None,
            "endpoint": endpoint,
            "api_version": api_version,
        }

    def test_openai_custom_endpoint_404_gives_base_url_hint(self) -> None:
        """openai + custom endpoint 404 → base-URL hint, no model listing."""
        mock_model = MagicMock()
        mock_model.invoke.side_effect = Exception("Error code: 404 - Not Found")
        with (
            patch(
                f"{_MOD_LC}._load_langchain_config",
                return_value=self._make_endpoint_config(),
            ),
            patch(
                f"{_MOD_LC}.load_langchain_history",
                return_value=[],
            ),
            patch(
                f"{_MOD_LC}._create_chat_model",
                return_value=mock_model,
            ),
            patch(f"{_MOD_LC}._models.list_openai_models") as mock_list,
        ):
            from mcp_coder.llm.providers.langchain import ask_langchain

            with pytest.raises(ValueError) as exc_info:
                ask_langchain("question")
        message = str(exc_info.value)
        assert "base URL" in message
        assert "/chat/completions" in message
        mock_list.assert_not_called()

    def test_openai_no_endpoint_404_takes_suggestions_path(self) -> None:
        """openai + endpoint=None 404 → model-not-found + suggestions."""
        mock_model = MagicMock()
        mock_model.invoke.side_effect = Exception("Error code: 404 - Not Found")
        with (
            patch(
                f"{_MOD_LC}._load_langchain_config",
                return_value=self._make_endpoint_config(endpoint=None),
            ),
            patch(
                f"{_MOD_LC}.load_langchain_history",
                return_value=[],
            ),
            patch(
                f"{_MOD_LC}._create_chat_model",
                return_value=mock_model,
            ),
            patch(
                _SUGGEST,
                return_value="\n\nAvailable models:\n  - gpt-4o",
            ) as mock_suggest,
        ):
            from mcp_coder.llm.providers.langchain import ask_langchain

            with pytest.raises(ValueError) as exc_info:
                ask_langchain("question")
        message = str(exc_info.value)
        assert "not found" in message.lower()
        assert "base URL" not in message
        assert "gpt-4o" in message
        mock_suggest.assert_called_once()

    def test_non_openai_backend_404_keeps_default_wording(self) -> None:
        """ollama + custom endpoint 404 → default wording, NOT base-URL hint."""
        mock_model = MagicMock()
        mock_model.invoke.side_effect = Exception("Error code: 404 - Not Found")
        with (
            patch(
                f"{_MOD_LC}._load_langchain_config",
                return_value=self._make_endpoint_config(backend="ollama"),
            ),
            patch(
                f"{_MOD_LC}.load_langchain_history",
                return_value=[],
            ),
            patch(
                f"{_MOD_LC}._create_chat_model",
                return_value=mock_model,
            ),
            patch(
                _SUGGEST,
                return_value="\n\nAvailable models:\n  - llama3",
            ) as mock_suggest,
        ):
            from mcp_coder.llm.providers.langchain import ask_langchain

            with pytest.raises(ValueError) as exc_info:
                ask_langchain("question")
        message = str(exc_info.value)
        assert "not found" in message.lower()
        assert "base URL" not in message
        mock_suggest.assert_called_once()


class TestIs404Error:
    """Direct unit tests for the shared _is_404_error detection predicate."""

    @pytest.mark.parametrize(
        "message",
        [
            "Error code: 404 ...",
            "model NOT_FOUND",
            "not found",
        ],
    )
    def test_detects_404_variants(self, message: str) -> None:
        """404-style messages are detected as True."""
        from mcp_coder.llm.providers.langchain import _is_404_error

        assert _is_404_error(Exception(message)) is True

    def test_non_404_returns_false(self) -> None:
        """A non-404 exception is not detected."""
        from mcp_coder.llm.providers.langchain import _is_404_error

        assert _is_404_error(Exception("boom")) is False


def _make_endpoint_config(
    backend: str = "openai",
    endpoint: str | None = "https://h/v1",
    api_version: str | None = None,
) -> dict[str, str | None]:
    return {
        "provider": "langchain",
        "backend": backend,
        "model": "bad-model",
        "api_key": None,
        "endpoint": endpoint,
        "api_version": api_version,
    }


class TestAskTextStream404Hint:
    """_ask_text_stream 404 handling shares _format_404_hint with _ask_text."""

    def test_openai_custom_endpoint_404_yields_base_url_hint(self) -> None:
        """openai + custom endpoint 404 → base-URL error event, no model listing."""
        mock_model = MagicMock()
        mock_model.stream.side_effect = Exception("Error code: 404 - Not Found")

        with (
            patch(
                f"{_MOD_LC}._load_langchain_config",
                return_value=_make_endpoint_config(),
            ),
            patch(f"{_MOD_LC}.load_langchain_history", return_value=[]),
            patch(f"{_MOD_LC}.store_langchain_history"),
            patch(f"{_MOD_LC}._create_chat_model", return_value=mock_model),
            patch(f"{_MOD_LC}._models.list_openai_models") as mock_list,
        ):
            from mcp_coder.llm.providers.langchain import ask_langchain_stream

            events: list[dict[str, object]] = []
            with pytest.raises(ValueError) as exc_info:
                for event in ask_langchain_stream("Hi"):
                    events.append(event)

        error_events = [e for e in events if e["type"] == "error"]
        assert len(error_events) == 1
        assert "base URL" in str(error_events[0]["message"])
        assert "base URL" in str(exc_info.value)
        mock_list.assert_not_called()

    def test_openai_no_endpoint_404_yields_not_found(self) -> None:
        """openai + endpoint=None 404 → model-not-found error event + ValueError."""
        mock_model = MagicMock()
        mock_model.stream.side_effect = Exception("Error code: 404 - Not Found")

        with (
            patch(
                f"{_MOD_LC}._load_langchain_config",
                return_value=_make_endpoint_config(endpoint=None),
            ),
            patch(f"{_MOD_LC}.load_langchain_history", return_value=[]),
            patch(f"{_MOD_LC}.store_langchain_history"),
            patch(f"{_MOD_LC}._create_chat_model", return_value=mock_model),
            patch(
                _SUGGEST,
                return_value="",
            ),
        ):
            from mcp_coder.llm.providers.langchain import ask_langchain_stream

            events: list[dict[str, object]] = []
            with pytest.raises(ValueError, match="not found"):
                for event in ask_langchain_stream("Hi"):
                    events.append(event)

        error_events = [e for e in events if e["type"] == "error"]
        assert len(error_events) == 1
        assert "not found" in str(error_events[0]["message"]).lower()
        assert "base URL" not in str(error_events[0]["message"])

    def test_non_openai_backend_404_keeps_default_wording(self) -> None:
        """ollama + custom endpoint 404 → default wording, NOT base-URL hint."""
        mock_model = MagicMock()
        mock_model.stream.side_effect = Exception("Error code: 404 - Not Found")

        with (
            patch(
                f"{_MOD_LC}._load_langchain_config",
                return_value=_make_endpoint_config(backend="ollama"),
            ),
            patch(f"{_MOD_LC}.load_langchain_history", return_value=[]),
            patch(f"{_MOD_LC}.store_langchain_history"),
            patch(f"{_MOD_LC}._create_chat_model", return_value=mock_model),
            patch(
                _SUGGEST,
                return_value="\n\nAvailable models:\n  - llama3",
            ) as mock_suggest,
        ):
            from mcp_coder.llm.providers.langchain import ask_langchain_stream

            events: list[dict[str, object]] = []
            with pytest.raises(ValueError) as exc_info:
                for event in ask_langchain_stream("Hi"):
                    events.append(event)

        error_events = [e for e in events if e["type"] == "error"]
        assert len(error_events) == 1
        message = str(error_events[0]["message"])
        assert "not found" in message.lower()
        assert "base URL" not in message
        assert "/chat/completions" not in message
        assert "not found" in str(exc_info.value).lower()
        mock_suggest.assert_called_once()
