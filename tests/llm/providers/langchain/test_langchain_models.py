"""Tests for mcp_coder.llm.providers.langchain._models."""

from unittest.mock import MagicMock, patch

_MODELS_MOD = "mcp_coder.llm.providers.langchain._models"


class TestListGeminiModels:
    def _make_model(self, name: str, actions: list[str]) -> MagicMock:
        m = MagicMock()
        m.name = name
        m.supported_actions = actions
        return m

    def test_returns_model_names_without_prefix(self) -> None:
        """list_gemini_models strips 'models/' prefix from model names."""
        models = [
            self._make_model("models/gemini-2.0-flash", ["generateContent"]),
            self._make_model("models/gemini-2.5-pro", ["generateContent"]),
        ]
        with patch(f"{_MODELS_MOD}._genai") as mock_genai:
            mock_genai.Client.return_value.models.list.return_value = models
            from mcp_coder.llm.providers.langchain._models import list_gemini_models

            result = list_gemini_models(api_key="test-key")
        assert result == ["gemini-2.0-flash", "gemini-2.5-pro"]

    def test_filters_out_non_generate_content_models(self) -> None:
        """Only models supporting generateContent are returned."""
        models = [
            self._make_model("models/gemini-2.0-flash", ["generateContent"]),
            self._make_model("models/embedding-001", ["embedContent"]),
        ]
        with patch(f"{_MODELS_MOD}._genai") as mock_genai:
            mock_genai.Client.return_value.models.list.return_value = models
            from mcp_coder.llm.providers.langchain._models import list_gemini_models

            result = list_gemini_models(api_key=None)
        assert "gemini-2.0-flash" in result
        assert "embedding-001" not in result

    def test_passes_api_key_to_client(self) -> None:
        """api_key is forwarded to the genai Client constructor."""
        with patch(f"{_MODELS_MOD}._genai") as mock_genai:
            mock_genai.Client.return_value.models.list.return_value = []
            from mcp_coder.llm.providers.langchain._models import list_gemini_models

            list_gemini_models(api_key="my-key")
        mock_genai.Client.assert_called_once_with(api_key="my-key")

    def test_returns_empty_list_when_no_matching_models(self) -> None:
        """Returns empty list when no models support generateContent."""
        models = [
            self._make_model("models/embedding-001", ["embedContent"]),
        ]
        with patch(f"{_MODELS_MOD}._genai") as mock_genai:
            mock_genai.Client.return_value.models.list.return_value = models
            from mcp_coder.llm.providers.langchain._models import list_gemini_models

            result = list_gemini_models(api_key=None)
        assert result == []


class TestListOpenaiModels:
    def _make_model(self, model_id: str) -> MagicMock:
        m = MagicMock()
        m.id = model_id
        return m

    def test_returns_sorted_model_ids(self) -> None:
        """list_openai_models returns sorted model IDs."""
        models = [
            self._make_model("gpt-4o"),
            self._make_model("gpt-3.5-turbo"),
        ]
        with patch(f"{_MODELS_MOD}._openai_mod") as mock_openai:
            mock_openai.OpenAI.return_value.models.list.return_value = models
            from mcp_coder.llm.providers.langchain._models import list_openai_models

            result = list_openai_models(api_key="test-key")
        assert result == ["gpt-3.5-turbo", "gpt-4o"]

    def test_passes_api_key_and_endpoint(self) -> None:
        """api_key and endpoint are forwarded to the OpenAI client."""
        with patch(f"{_MODELS_MOD}._openai_mod") as mock_openai:
            mock_openai.OpenAI.return_value.models.list.return_value = []
            from mcp_coder.llm.providers.langchain._models import list_openai_models

            list_openai_models(api_key="my-key", endpoint="https://custom.example.com")
        mock_openai.OpenAI.assert_called_once_with(
            api_key="my-key", base_url="https://custom.example.com"
        )

    def test_omits_none_api_key_and_endpoint(self) -> None:
        """None values for api_key and endpoint are not passed to client."""
        with patch(f"{_MODELS_MOD}._openai_mod") as mock_openai:
            mock_openai.OpenAI.return_value.models.list.return_value = []
            from mcp_coder.llm.providers.langchain._models import list_openai_models

            list_openai_models(api_key=None, endpoint=None)
        mock_openai.OpenAI.assert_called_once_with()

    def test_returns_empty_list_when_no_models(self) -> None:
        """Returns empty list when API returns no models."""
        with patch(f"{_MODELS_MOD}._openai_mod") as mock_openai:
            mock_openai.OpenAI.return_value.models.list.return_value = []
            from mcp_coder.llm.providers.langchain._models import list_openai_models

            result = list_openai_models(api_key=None)
        assert result == []


class TestListAnthropicModels:
    def _make_model(self, model_id: str) -> MagicMock:
        m = MagicMock()
        m.id = model_id
        return m

    def test_returns_sorted_model_ids(self) -> None:
        """list_anthropic_models returns sorted model IDs."""
        models = [
            self._make_model("claude-opus-4-6"),
            self._make_model("claude-sonnet-4-5-20250929"),
        ]
        with patch(f"{_MODELS_MOD}._anthropic_mod") as mock_anthropic:
            mock_anthropic.Anthropic.return_value.models.list.return_value = models
            from mcp_coder.llm.providers.langchain._models import (
                list_anthropic_models,
            )

            result = list_anthropic_models(api_key="test-key")
        assert result == ["claude-opus-4-6", "claude-sonnet-4-5-20250929"]

    def test_passes_api_key(self) -> None:
        """api_key is forwarded to the Anthropic client."""
        with patch(f"{_MODELS_MOD}._anthropic_mod") as mock_anthropic:
            mock_anthropic.Anthropic.return_value.models.list.return_value = []
            from mcp_coder.llm.providers.langchain._models import (
                list_anthropic_models,
            )

            list_anthropic_models(api_key="my-key")
        mock_anthropic.Anthropic.assert_called_once_with(api_key="my-key")

    def test_omits_none_api_key(self) -> None:
        """None api_key is not passed to client."""
        with patch(f"{_MODELS_MOD}._anthropic_mod") as mock_anthropic:
            mock_anthropic.Anthropic.return_value.models.list.return_value = []
            from mcp_coder.llm.providers.langchain._models import (
                list_anthropic_models,
            )

            list_anthropic_models(api_key=None)
        mock_anthropic.Anthropic.assert_called_once_with()

    def test_returns_empty_list_when_no_models(self) -> None:
        """Returns empty list when API returns no models."""
        with patch(f"{_MODELS_MOD}._anthropic_mod") as mock_anthropic:
            mock_anthropic.Anthropic.return_value.models.list.return_value = []
            from mcp_coder.llm.providers.langchain._models import (
                list_anthropic_models,
            )

            result = list_anthropic_models(api_key=None)
        assert result == []
