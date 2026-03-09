"""Tests for mcp_coder.llm.providers.langchain._models."""

from unittest.mock import MagicMock, patch


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
        with patch("mcp_coder.llm.providers.langchain._models.genai") as mock_genai:
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
        with patch("mcp_coder.llm.providers.langchain._models.genai") as mock_genai:
            mock_genai.Client.return_value.models.list.return_value = models
            from mcp_coder.llm.providers.langchain._models import list_gemini_models

            result = list_gemini_models(api_key=None)
        assert "gemini-2.0-flash" in result
        assert "embedding-001" not in result

    def test_passes_api_key_to_client(self) -> None:
        """api_key is forwarded to the genai Client constructor."""
        with patch("mcp_coder.llm.providers.langchain._models.genai") as mock_genai:
            mock_genai.Client.return_value.models.list.return_value = []
            from mcp_coder.llm.providers.langchain._models import list_gemini_models

            list_gemini_models(api_key="my-key")
        mock_genai.Client.assert_called_once_with(api_key="my-key")

    def test_returns_empty_list_when_no_matching_models(self) -> None:
        """Returns empty list when no models support generateContent."""
        models = [
            self._make_model("models/embedding-001", ["embedContent"]),
        ]
        with patch("mcp_coder.llm.providers.langchain._models.genai") as mock_genai:
            mock_genai.Client.return_value.models.list.return_value = models
            from mcp_coder.llm.providers.langchain._models import list_gemini_models

            result = list_gemini_models(api_key=None)
        assert result == []
