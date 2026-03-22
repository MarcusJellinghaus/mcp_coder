"""Tests for mcp_coder.llm.providers.langchain._models.

These tests use sys.modules mocking for openai/anthropic so they work
regardless of whether the optional SDK packages are installed.
For google.genai (namespace package), patch.object on the real module
is used with pytest.importorskip for graceful skip when not installed.
"""

import sys
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.llm.providers.langchain._models import (
    list_anthropic_models,
    list_gemini_models,
    list_openai_models,
)

# google.genai is a namespace package — sys.modules mocking doesn't
# reliably intercept its imports.  Use the real module + patch.object instead.
_google_genai = pytest.importorskip("google.genai")


def _make_genai_model(name: str, actions: list[str]) -> MagicMock:
    """Create a mock Gemini model object."""
    m = MagicMock()
    m.name = name
    m.supported_actions = actions
    return m


def _make_model(model_id: str) -> MagicMock:
    """Create a mock model object with an id attribute."""
    m = MagicMock()
    m.id = model_id
    return m


def _openai_mock() -> MagicMock:
    """Create a fresh mock openai module."""
    return MagicMock()


def _anthropic_mock() -> MagicMock:
    """Create a fresh mock anthropic module."""
    return MagicMock()


class TestListGeminiModels:
    """Tests for list_gemini_models function."""

    def test_returns_model_names_without_prefix(self) -> None:
        """list_gemini_models strips 'models/' prefix from model names."""
        models = [
            _make_genai_model("models/gemini-2.0-flash", ["generateContent"]),
            _make_genai_model("models/gemini-2.5-pro", ["generateContent"]),
        ]
        with patch.object(_google_genai, "Client") as MockClient:
            MockClient.return_value.models.list.return_value = models
            result = list_gemini_models(api_key="test-key")
        assert result == ["gemini-2.0-flash", "gemini-2.5-pro"]

    def test_filters_out_non_generate_content_models(self) -> None:
        """Only models supporting generateContent are returned."""
        models = [
            _make_genai_model("models/gemini-2.0-flash", ["generateContent"]),
            _make_genai_model("models/embedding-001", ["embedContent"]),
        ]
        with patch.object(_google_genai, "Client") as MockClient:
            MockClient.return_value.models.list.return_value = models
            result = list_gemini_models(api_key=None)
        assert "gemini-2.0-flash" in result
        assert "embedding-001" not in result

    def test_passes_api_key_to_client(self) -> None:
        """api_key is forwarded to the genai Client constructor."""
        with patch.object(_google_genai, "Client") as MockClient:
            MockClient.return_value.models.list.return_value = []
            list_gemini_models(api_key="my-key")
        MockClient.assert_called_once_with(api_key="my-key")

    def test_returns_empty_list_when_no_matching_models(self) -> None:
        """Returns empty list when no models support generateContent."""
        models = [
            _make_genai_model("models/embedding-001", ["embedContent"]),
        ]
        with patch.object(_google_genai, "Client") as MockClient:
            MockClient.return_value.models.list.return_value = models
            result = list_gemini_models(api_key=None)
        assert result == []


class TestListOpenaiModels:
    """Tests for list_openai_models function."""

    def test_returns_sorted_model_ids(self) -> None:
        """list_openai_models returns sorted model IDs."""
        models = [_make_model("gpt-4o"), _make_model("gpt-3.5-turbo")]
        mock_openai = _openai_mock()
        mock_openai.OpenAI.return_value.models.list.return_value = models
        with patch.dict(sys.modules, {"openai": mock_openai}):
            result = list_openai_models(api_key="test-key")
        assert result == ["gpt-3.5-turbo", "gpt-4o"]

    def test_passes_api_key_and_endpoint(self) -> None:
        """api_key and endpoint are forwarded to the OpenAI client."""
        mock_openai = _openai_mock()
        mock_openai.OpenAI.return_value.models.list.return_value = []
        with patch.dict(sys.modules, {"openai": mock_openai}):
            list_openai_models(api_key="my-key", endpoint="https://custom.example.com")
        mock_openai.OpenAI.assert_called_once_with(
            api_key="my-key", base_url="https://custom.example.com"
        )

    def test_omits_none_api_key_and_endpoint(self) -> None:
        """None values for api_key and endpoint are passed as None."""
        mock_openai = _openai_mock()
        mock_openai.OpenAI.return_value.models.list.return_value = []
        with patch.dict(sys.modules, {"openai": mock_openai}):
            list_openai_models(api_key=None, endpoint=None)
        mock_openai.OpenAI.assert_called_once_with(api_key=None, base_url=None)

    def test_returns_empty_list_when_no_models(self) -> None:
        """Returns empty list when API returns no models."""
        mock_openai = _openai_mock()
        mock_openai.OpenAI.return_value.models.list.return_value = []
        with patch.dict(sys.modules, {"openai": mock_openai}):
            result = list_openai_models(api_key=None)
        assert result == []


class TestListAnthropicModels:
    """Tests for list_anthropic_models function."""

    def test_returns_sorted_model_ids(self) -> None:
        """list_anthropic_models returns sorted model IDs."""
        models = [
            _make_model("claude-opus-4-6"),
            _make_model("claude-sonnet-4-5-20250929"),
        ]
        mock_anthropic = _anthropic_mock()
        mock_anthropic.Anthropic.return_value.models.list.return_value = models
        with patch.dict(sys.modules, {"anthropic": mock_anthropic}):
            result = list_anthropic_models(api_key="test-key")
        assert result == ["claude-opus-4-6", "claude-sonnet-4-5-20250929"]

    def test_passes_api_key(self) -> None:
        """api_key is forwarded to the Anthropic client."""
        mock_anthropic = _anthropic_mock()
        mock_anthropic.Anthropic.return_value.models.list.return_value = []
        with patch.dict(sys.modules, {"anthropic": mock_anthropic}):
            list_anthropic_models(api_key="my-key")
        mock_anthropic.Anthropic.assert_called_once_with(api_key="my-key")

    def test_omits_none_api_key(self) -> None:
        """None api_key is passed as None."""
        mock_anthropic = _anthropic_mock()
        mock_anthropic.Anthropic.return_value.models.list.return_value = []
        with patch.dict(sys.modules, {"anthropic": mock_anthropic}):
            list_anthropic_models(api_key=None)
        mock_anthropic.Anthropic.assert_called_once_with(api_key=None)

    def test_returns_empty_list_when_no_models(self) -> None:
        """Returns empty list when API returns no models."""
        mock_anthropic = _anthropic_mock()
        mock_anthropic.Anthropic.return_value.models.list.return_value = []
        with patch.dict(sys.modules, {"anthropic": mock_anthropic}):
            result = list_anthropic_models(api_key=None)
        assert result == []


class TestListModelsCommon:
    """Cross-cutting tests for all list_*_models() functions."""

    def test_list_openai_models_returns_list_of_strings(self) -> None:
        """list_openai_models returns a list of strings."""
        models = [_make_model("gpt-4o")]
        mock_openai = _openai_mock()
        mock_openai.OpenAI.return_value.models.list.return_value = models
        with patch.dict(sys.modules, {"openai": mock_openai}):
            result = list_openai_models(api_key="test")
        assert isinstance(result, list)
        assert all(isinstance(m, str) for m in result)

    def test_list_gemini_models_returns_list_of_strings(self) -> None:
        """list_gemini_models returns a list of strings."""
        models = [_make_genai_model("models/gemini-2.0-flash", ["generateContent"])]
        with patch.object(_google_genai, "Client") as MockClient:
            MockClient.return_value.models.list.return_value = models
            result = list_gemini_models(api_key="test")
        assert isinstance(result, list)
        assert all(isinstance(m, str) for m in result)

    def test_list_anthropic_models_returns_list_of_strings(self) -> None:
        """list_anthropic_models returns a list of strings."""
        models = [_make_model("claude-opus-4-6")]
        mock_anthropic = _anthropic_mock()
        mock_anthropic.Anthropic.return_value.models.list.return_value = models
        with patch.dict(sys.modules, {"anthropic": mock_anthropic}):
            result = list_anthropic_models(api_key="test")
        assert isinstance(result, list)
        assert all(isinstance(m, str) for m in result)

    def test_list_openai_models_handles_api_error(self) -> None:
        """list_openai_models propagates API errors."""
        mock_openai = _openai_mock()
        mock_openai.OpenAI.return_value.models.list.side_effect = Exception("API error")
        with patch.dict(sys.modules, {"openai": mock_openai}):
            with pytest.raises(Exception, match="API error"):
                list_openai_models(api_key="test")

    def test_list_gemini_models_handles_api_error(self) -> None:
        """list_gemini_models propagates API errors."""
        with patch.object(_google_genai, "Client") as MockClient:
            MockClient.return_value.models.list.side_effect = Exception("API error")
            with pytest.raises(Exception, match="API error"):
                list_gemini_models(api_key="test")

    def test_list_anthropic_models_handles_api_error(self) -> None:
        """list_anthropic_models propagates API errors."""
        mock_anthropic = _anthropic_mock()
        mock_anthropic.Anthropic.return_value.models.list.side_effect = Exception(
            "API error"
        )
        with patch.dict(sys.modules, {"anthropic": mock_anthropic}):
            with pytest.raises(Exception, match="API error"):
                list_anthropic_models(api_key="test")

    def test_list_openai_models_import_error(self) -> None:
        """list_openai_models raises ImportError when SDK not installed."""
        with patch.dict(sys.modules, {"openai": None}):
            with pytest.raises(ImportError):
                list_openai_models(api_key="test")

    def test_list_anthropic_models_import_error(self) -> None:
        """list_anthropic_models raises ImportError when SDK not installed."""
        with patch.dict(sys.modules, {"anthropic": None}):
            with pytest.raises(ImportError):
                list_anthropic_models(api_key="test")
