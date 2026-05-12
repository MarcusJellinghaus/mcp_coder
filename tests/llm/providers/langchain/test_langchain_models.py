"""Tests for mcp_coder.llm.providers.langchain._models.

These tests use sys.modules mocking for openai/anthropic so they work
regardless of whether the optional SDK packages are installed.
For google.genai (namespace package), patch.object on the real module
is used with pytest.importorskip for graceful skip when not installed.
"""

import sys
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.llm.providers.langchain._exceptions import (
    LLMAuthError,
    LLMConnectionError,
)
from mcp_coder.llm.providers.langchain._models import (
    _check_ollama_daemon,
    check_ollama_tool_capability,
    list_anthropic_models,
    list_gemini_models,
    list_ollama_models,
    list_openai_models,
)

_MODELS = "mcp_coder.llm.providers.langchain._models"
_HTTP = f"{_MODELS}.create_http_client"


class _FakeAuthError(Exception):
    """Fake auth error for testing exception tuple patching."""


class _FakeClientError(Exception):
    """Fake Google ClientError for testing."""

    def __init__(self, message: str, code: int) -> None:
        super().__init__(message)
        self.code = code


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


def _ollama_mock() -> MagicMock:
    """Create a fresh mock ollama module."""
    return MagicMock()


def _make_ollama_model(name: str) -> dict[str, str]:
    """Create a mock Ollama model entry as returned by client.list()."""
    return {"name": name}


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
        mock_openai.OpenAI.assert_called_once()
        _, kwargs = mock_openai.OpenAI.call_args
        assert kwargs["api_key"] == "my-key"
        assert kwargs["base_url"] == "https://custom.example.com"

    def test_omits_none_api_key_and_endpoint(self) -> None:
        """None values for api_key and endpoint are passed as None."""
        mock_openai = _openai_mock()
        mock_openai.OpenAI.return_value.models.list.return_value = []
        with patch.dict(sys.modules, {"openai": mock_openai}):
            list_openai_models(api_key=None, endpoint=None)
        mock_openai.OpenAI.assert_called_once()
        _, kwargs = mock_openai.OpenAI.call_args
        assert kwargs["api_key"] is None
        assert kwargs["base_url"] is None

    def test_returns_empty_list_when_no_models(self) -> None:
        """Returns empty list when API returns no models."""
        mock_openai = _openai_mock()
        mock_openai.OpenAI.return_value.models.list.return_value = []
        with patch.dict(sys.modules, {"openai": mock_openai}):
            result = list_openai_models(api_key=None)
        assert result == []

    def test_http_client_passed_to_openai_client(self) -> None:
        """create_http_client result is passed as http_client to openai.OpenAI."""
        sentinel = MagicMock(name="http_client_sentinel")
        mock_openai = _openai_mock()
        mock_openai.OpenAI.return_value.models.list.return_value = []
        with (
            patch.dict(sys.modules, {"openai": mock_openai}),
            patch(_HTTP, return_value=sentinel),
        ):
            list_openai_models(api_key="k")
        _, kwargs = mock_openai.OpenAI.call_args
        assert kwargs["http_client"] is sentinel


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
        mock_anthropic.Anthropic.assert_called_once()
        _, kwargs = mock_anthropic.Anthropic.call_args
        assert kwargs["api_key"] == "my-key"

    def test_omits_none_api_key(self) -> None:
        """None api_key is passed as None."""
        mock_anthropic = _anthropic_mock()
        mock_anthropic.Anthropic.return_value.models.list.return_value = []
        with patch.dict(sys.modules, {"anthropic": mock_anthropic}):
            list_anthropic_models(api_key=None)
        mock_anthropic.Anthropic.assert_called_once()
        _, kwargs = mock_anthropic.Anthropic.call_args
        assert kwargs["api_key"] is None

    def test_returns_empty_list_when_no_models(self) -> None:
        """Returns empty list when API returns no models."""
        mock_anthropic = _anthropic_mock()
        mock_anthropic.Anthropic.return_value.models.list.return_value = []
        with patch.dict(sys.modules, {"anthropic": mock_anthropic}):
            result = list_anthropic_models(api_key=None)
        assert result == []

    def test_http_client_passed_to_anthropic_client(self) -> None:
        """create_http_client result is passed as http_client to anthropic.Anthropic."""
        sentinel = MagicMock(name="http_client_sentinel")
        mock_anthropic = _anthropic_mock()
        mock_anthropic.Anthropic.return_value.models.list.return_value = []
        with (
            patch.dict(sys.modules, {"anthropic": mock_anthropic}),
            patch(_HTTP, return_value=sentinel),
        ):
            list_anthropic_models(api_key="k")
        _, kwargs = mock_anthropic.Anthropic.call_args
        assert kwargs["http_client"] is sentinel


class TestListOllamaModels:
    """Tests for list_ollama_models function."""

    def test_returns_sorted_model_names(self) -> None:
        """list_ollama_models returns sorted model names."""
        mock_ollama = _ollama_mock()
        mock_ollama.Client.return_value.list.return_value = {
            "models": [
                _make_ollama_model("mistral:7b"),
                _make_ollama_model("llama3:latest"),
            ]
        }
        with patch.dict(sys.modules, {"ollama": mock_ollama}):
            result = list_ollama_models(api_key=None)
        assert result == ["llama3:latest", "mistral:7b"]

    def test_passes_normalized_host_to_client(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """endpoint without scheme gets http:// prefix before passing to Client."""
        monkeypatch.delenv("OLLAMA_HOST", raising=False)
        mock_ollama = _ollama_mock()
        mock_ollama.Client.return_value.list.return_value = {"models": []}
        with patch.dict(sys.modules, {"ollama": mock_ollama}):
            list_ollama_models(api_key=None, endpoint="127.0.0.1:11434")
        mock_ollama.Client.assert_called_once_with(host="http://127.0.0.1:11434")

    def test_uses_default_client_when_no_endpoint(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """No env and no endpoint → Client() called without host kwarg."""
        monkeypatch.delenv("OLLAMA_HOST", raising=False)
        mock_ollama = _ollama_mock()
        mock_ollama.Client.return_value.list.return_value = {"models": []}
        with patch.dict(sys.modules, {"ollama": mock_ollama}):
            list_ollama_models(api_key=None)
        mock_ollama.Client.assert_called_once_with()

    def test_ollama_host_env_overrides_endpoint(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """OLLAMA_HOST env var takes precedence over endpoint argument."""
        monkeypatch.setenv("OLLAMA_HOST", "envhost:9999")
        mock_ollama = _ollama_mock()
        mock_ollama.Client.return_value.list.return_value = {"models": []}
        with patch.dict(sys.modules, {"ollama": mock_ollama}):
            list_ollama_models(api_key=None, endpoint="confighost:1111")
        mock_ollama.Client.assert_called_once_with(host="http://envhost:9999")

    def test_returns_empty_list_when_no_models(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Returns empty list when daemon returns no models."""
        monkeypatch.delenv("OLLAMA_HOST", raising=False)
        mock_ollama = _ollama_mock()
        mock_ollama.Client.return_value.list.return_value = {"models": []}
        with patch.dict(sys.modules, {"ollama": mock_ollama}):
            result = list_ollama_models(api_key=None)
        assert result == []

    def test_connection_error_raises_llm_connection_error(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """ConnectionError from client.list() raises LLMConnectionError."""
        monkeypatch.delenv("OLLAMA_HOST", raising=False)
        mock_ollama = _ollama_mock()
        mock_ollama.Client.return_value.list.side_effect = ConnectionError("refused")
        with patch.dict(sys.modules, {"ollama": mock_ollama}):
            with pytest.raises(LLMConnectionError):
                list_ollama_models(api_key=None)

    def test_connection_error_message_contains_hints(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Connection error message includes OLLAMA_API_KEY and OLLAMA_HOST hints."""
        monkeypatch.delenv("OLLAMA_HOST", raising=False)
        mock_ollama = _ollama_mock()
        mock_ollama.Client.return_value.list.side_effect = ConnectionError("refused")
        with patch.dict(sys.modules, {"ollama": mock_ollama}):
            with pytest.raises(LLMConnectionError) as exc_info:
                list_ollama_models(api_key=None)
        msg = str(exc_info.value)
        assert "OLLAMA_API_KEY" in msg
        assert "OLLAMA_HOST" in msg or "endpoint" in msg.lower()

    def test_import_error_when_sdk_not_installed(self) -> None:
        """list_ollama_models raises ImportError when ollama SDK missing."""
        with patch.dict(sys.modules, {"ollama": None}):
            with pytest.raises(ImportError):
                list_ollama_models(api_key=None)


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


# ---------------------------------------------------------------------------
# Connection-error wrapping tests
# ---------------------------------------------------------------------------


class TestListOpenaiModelsConnectionError:
    """list_openai_models wraps connection errors as LLMConnectionError."""

    def test_connection_error_raises_llm_connection_error(self) -> None:
        mock_openai = _openai_mock()
        mock_openai.OpenAI.return_value.models.list.side_effect = ConnectionError(
            "reset"
        )
        with patch.dict(sys.modules, {"openai": mock_openai}):
            with pytest.raises(LLMConnectionError):
                list_openai_models(api_key="k")

    def test_connection_error_message_contains_hints(self) -> None:
        mock_openai = _openai_mock()
        mock_openai.OpenAI.return_value.models.list.side_effect = ConnectionError(
            "reset"
        )
        with patch.dict(sys.modules, {"openai": mock_openai}):
            with pytest.raises(LLMConnectionError, match="OPENAI_API_KEY") as exc_info:
                list_openai_models(api_key="k")
        assert "endpoint" in str(exc_info.value).lower()


class TestListOpenaiModelsAuthError:
    """list_openai_models wraps auth errors as LLMAuthError."""

    def test_auth_error_raises_llm_auth_error(self) -> None:
        mock_openai = _openai_mock()
        mock_openai.OpenAI.return_value.models.list.side_effect = _FakeAuthError(
            "invalid key"
        )
        with (
            patch.dict(sys.modules, {"openai": mock_openai}),
            patch(f"{_MODELS}.OPENAI_AUTH_ERRORS", (_FakeAuthError,)),
        ):
            with pytest.raises(LLMAuthError):
                list_openai_models(api_key="k")

    def test_auth_error_message_contains_hints(self) -> None:
        mock_openai = _openai_mock()
        mock_openai.OpenAI.return_value.models.list.side_effect = _FakeAuthError(
            "invalid key"
        )
        with (
            patch.dict(sys.modules, {"openai": mock_openai}),
            patch(f"{_MODELS}.OPENAI_AUTH_ERRORS", (_FakeAuthError,)),
        ):
            with pytest.raises(LLMAuthError, match="OPENAI_API_KEY"):
                list_openai_models(api_key="k")


class TestListGeminiModelsConnectionError:
    """list_gemini_models wraps connection errors as LLMConnectionError."""

    def test_connection_error_raises_llm_connection_error(self) -> None:
        with patch.object(_google_genai, "Client") as mock_client:
            mock_client.return_value.models.list.side_effect = ConnectionError("reset")
            with pytest.raises(LLMConnectionError):
                list_gemini_models(api_key="k")

    def test_connection_error_message_contains_hints(self) -> None:
        with patch.object(_google_genai, "Client") as mock_client:
            mock_client.return_value.models.list.side_effect = ConnectionError("reset")
            with pytest.raises(LLMConnectionError, match="GEMINI_API_KEY"):
                list_gemini_models(api_key="k")


class TestListGeminiModelsAuthError:
    """list_gemini_models wraps ClientError auth codes as LLMAuthError."""

    def test_client_error_401_raises_llm_auth_error(self) -> None:
        exc = _FakeClientError("unauthorized", code=401)
        with (
            patch.object(_google_genai, "Client") as mock_client,
            patch(f"{_MODELS}.GOOGLE_CLIENT_ERRORS", (_FakeClientError,)),
            patch(f"{_MODELS}.is_google_auth_error", return_value=True),
        ):
            mock_client.return_value.models.list.side_effect = exc
            with pytest.raises(LLMAuthError):
                list_gemini_models(api_key="k")

    def test_client_error_500_raises_llm_connection_error(self) -> None:
        exc = _FakeClientError("server error", code=500)
        with (
            patch.object(_google_genai, "Client") as mock_client,
            patch(f"{_MODELS}.GOOGLE_CLIENT_ERRORS", (_FakeClientError,)),
            patch(f"{_MODELS}.is_google_auth_error", return_value=False),
        ):
            mock_client.return_value.models.list.side_effect = exc
            with pytest.raises(LLMConnectionError):
                list_gemini_models(api_key="k")


class TestListAnthropicModelsConnectionError:
    """list_anthropic_models wraps connection errors as LLMConnectionError."""

    def test_connection_error_raises_llm_connection_error(self) -> None:
        mock_anthropic = _anthropic_mock()
        mock_anthropic.Anthropic.return_value.models.list.side_effect = ConnectionError(
            "reset"
        )
        with patch.dict(sys.modules, {"anthropic": mock_anthropic}):
            with pytest.raises(LLMConnectionError):
                list_anthropic_models(api_key="k")

    def test_connection_error_message_contains_hints(self) -> None:
        mock_anthropic = _anthropic_mock()
        mock_anthropic.Anthropic.return_value.models.list.side_effect = ConnectionError(
            "reset"
        )
        with patch.dict(sys.modules, {"anthropic": mock_anthropic}):
            with pytest.raises(LLMConnectionError, match="ANTHROPIC_API_KEY"):
                list_anthropic_models(api_key="k")


class _FakeOllamaResponseError(Exception):
    """Fake ollama.ResponseError for testing status-code branching."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


def _ollama_mock_with_response_error() -> MagicMock:
    """Create a mock ollama module with a real ResponseError class."""
    m = MagicMock()
    m.ResponseError = _FakeOllamaResponseError
    return m


class TestCheckOllamaDaemon:
    """Tests for _check_ollama_daemon probe function."""

    def test_returns_ok_when_list_succeeds(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("OLLAMA_HOST", raising=False)
        mock_ollama = _ollama_mock_with_response_error()
        mock_ollama.Client.return_value.list.return_value = {"models": []}
        with patch.dict(sys.modules, {"ollama": mock_ollama}):
            result = _check_ollama_daemon(api_key=None, endpoint=None)
        assert result["ok"] is True
        assert "reachable" in result["value"].lower()
        assert "localhost:11434" in result["value"]

    def test_returns_auth_required_on_401(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("OLLAMA_HOST", raising=False)
        mock_ollama = _ollama_mock_with_response_error()
        mock_ollama.Client.return_value.list.side_effect = _FakeOllamaResponseError(
            "unauthorized", status_code=401
        )
        with patch.dict(sys.modules, {"ollama": mock_ollama}):
            result = _check_ollama_daemon(api_key=None, endpoint=None)
        assert result["ok"] is False
        assert "auth required" in result["value"].lower()
        assert "OLLAMA_API_KEY" in result["value"]

    def test_returns_auth_required_on_403(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("OLLAMA_HOST", raising=False)
        mock_ollama = _ollama_mock_with_response_error()
        mock_ollama.Client.return_value.list.side_effect = _FakeOllamaResponseError(
            "forbidden", status_code=403
        )
        with patch.dict(sys.modules, {"ollama": mock_ollama}):
            result = _check_ollama_daemon(api_key=None, endpoint=None)
        assert result["ok"] is False
        assert "auth required" in result["value"].lower()

    def test_returns_auth_required_via_message_when_status_missing(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Fall back to substring sniff when status_code is unavailable."""
        monkeypatch.delenv("OLLAMA_HOST", raising=False)
        mock_ollama = _ollama_mock_with_response_error()
        mock_ollama.Client.return_value.list.side_effect = _FakeOllamaResponseError(
            "HTTP 401 unauthorized", status_code=None
        )
        with patch.dict(sys.modules, {"ollama": mock_ollama}):
            result = _check_ollama_daemon(api_key=None, endpoint=None)
        assert result["ok"] is False
        assert "auth required" in result["value"].lower()

    def test_returns_unreachable_on_connection_error(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("OLLAMA_HOST", raising=False)
        mock_ollama = _ollama_mock_with_response_error()
        mock_ollama.Client.return_value.list.side_effect = ConnectionError("refused")
        with patch.dict(sys.modules, {"ollama": mock_ollama}):
            result = _check_ollama_daemon(api_key=None, endpoint=None)
        assert result["ok"] is False
        assert "not reachable" in result["value"].lower()
        assert "ollama serve" in result["value"]

    def test_returns_unreachable_on_timeout(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("OLLAMA_HOST", raising=False)
        mock_ollama = _ollama_mock_with_response_error()
        mock_ollama.Client.return_value.list.side_effect = TimeoutError("slow")
        with patch.dict(sys.modules, {"ollama": mock_ollama}):
            result = _check_ollama_daemon(api_key=None, endpoint=None)
        assert result["ok"] is False
        assert "not reachable" in result["value"].lower()

    def test_uses_default_host_when_neither_env_nor_endpoint_set(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("OLLAMA_HOST", raising=False)
        mock_ollama = _ollama_mock_with_response_error()
        mock_ollama.Client.return_value.list.return_value = {"models": []}
        with patch.dict(sys.modules, {"ollama": mock_ollama}):
            _check_ollama_daemon(api_key=None, endpoint=None)
        _, kwargs = mock_ollama.Client.call_args
        assert kwargs["host"] == "http://localhost:11434"

    def test_uses_normalized_host_from_endpoint(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("OLLAMA_HOST", raising=False)
        mock_ollama = _ollama_mock_with_response_error()
        mock_ollama.Client.return_value.list.return_value = {"models": []}
        with patch.dict(sys.modules, {"ollama": mock_ollama}):
            _check_ollama_daemon(api_key=None, endpoint="example.com:11434")
        _, kwargs = mock_ollama.Client.call_args
        assert kwargs["host"] == "http://example.com:11434"

    def test_falls_back_when_client_rejects_headers_kwarg(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """If ollama.Client doesn't accept headers/timeout kwargs, retry with host only."""
        monkeypatch.delenv("OLLAMA_HOST", raising=False)
        mock_ollama = _ollama_mock_with_response_error()
        # First call (with headers/timeout) raises TypeError; second (host-only) works
        client_mock = MagicMock()
        client_mock.list.return_value = {"models": []}
        mock_ollama.Client.side_effect = [
            TypeError("unexpected keyword argument 'headers'"),
            client_mock,
        ]
        with patch.dict(sys.modules, {"ollama": mock_ollama}):
            result = _check_ollama_daemon(api_key="some-key", endpoint=None)
        assert result["ok"] is True
        # Second invocation used host-only kwargs
        assert mock_ollama.Client.call_count == 2
        _, last_kwargs = mock_ollama.Client.call_args
        assert last_kwargs == {"host": "http://localhost:11434"}

    def test_passes_auth_header_when_api_key_set(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("OLLAMA_HOST", raising=False)
        mock_ollama = _ollama_mock_with_response_error()
        mock_ollama.Client.return_value.list.return_value = {"models": []}
        with patch.dict(sys.modules, {"ollama": mock_ollama}):
            _check_ollama_daemon(api_key="my-token", endpoint=None)
        _, kwargs = mock_ollama.Client.call_args
        assert kwargs.get("headers") == {"Authorization": "Bearer my-token"}


class TestCheckOllamaToolCapability:
    """Tests for check_ollama_tool_capability helper."""

    def test_returns_ok_when_tools_in_capabilities(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("OLLAMA_HOST", raising=False)
        mock_ollama = _ollama_mock()
        mock_ollama.Client.return_value.show.return_value = {
            "capabilities": ["tools", "completion"]
        }
        with patch.dict(sys.modules, {"ollama": mock_ollama}):
            result = check_ollama_tool_capability(
                model="llama3", api_key=None, endpoint=None
            )
        assert result["ok"] is True
        assert "tools" in result["value"].lower()
        assert "llama3" in result["value"]

    def test_returns_not_ok_when_tools_missing(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("OLLAMA_HOST", raising=False)
        mock_ollama = _ollama_mock()
        mock_ollama.Client.return_value.show.return_value = {
            "capabilities": ["completion"]
        }
        with patch.dict(sys.modules, {"ollama": mock_ollama}):
            result = check_ollama_tool_capability(
                model="some-model", api_key=None, endpoint=None
            )
        assert result["ok"] is False
        assert "tools" in result["value"].lower()
        # No hardcoded "use X instead" model suggestions — must not leak
        # specific model names from outside the configured one.
        assert "llama" not in result["value"].lower()
        assert "qwen" not in result["value"].lower()

    def test_returns_not_ok_when_capabilities_empty(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("OLLAMA_HOST", raising=False)
        mock_ollama = _ollama_mock()
        mock_ollama.Client.return_value.show.return_value = {}
        with patch.dict(sys.modules, {"ollama": mock_ollama}):
            result = check_ollama_tool_capability(
                model="llama3", api_key=None, endpoint=None
            )
        assert result["ok"] is False

    def test_returns_not_ok_when_show_raises(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("OLLAMA_HOST", raising=False)
        mock_ollama = _ollama_mock()
        mock_ollama.Client.return_value.show.side_effect = RuntimeError(
            "model not found"
        )
        with patch.dict(sys.modules, {"ollama": mock_ollama}):
            result = check_ollama_tool_capability(
                model="llama3", api_key=None, endpoint=None
            )
        assert result["ok"] is False
        assert "model not found" in result["value"]

    def test_returns_not_ok_when_model_is_empty_string(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("OLLAMA_HOST", raising=False)
        mock_ollama = _ollama_mock()
        with patch.dict(sys.modules, {"ollama": mock_ollama}):
            result = check_ollama_tool_capability(model="", api_key=None, endpoint=None)
        assert result["ok"] is False
        # Network must not be touched when model is empty.
        mock_ollama.Client.assert_not_called()

    def test_uses_normalized_host(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("OLLAMA_HOST", raising=False)
        mock_ollama = _ollama_mock()
        mock_ollama.Client.return_value.show.return_value = {"capabilities": ["tools"]}
        with patch.dict(sys.modules, {"ollama": mock_ollama}):
            check_ollama_tool_capability(
                model="llama3", api_key=None, endpoint="example.com:11434"
            )
        _, kwargs = mock_ollama.Client.call_args
        assert kwargs["host"] == "http://example.com:11434"

    def test_uses_default_host_when_no_endpoint(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("OLLAMA_HOST", raising=False)
        mock_ollama = _ollama_mock()
        mock_ollama.Client.return_value.show.return_value = {"capabilities": ["tools"]}
        with patch.dict(sys.modules, {"ollama": mock_ollama}):
            check_ollama_tool_capability(model="llama3", api_key=None, endpoint=None)
        _, kwargs = mock_ollama.Client.call_args
        assert kwargs["host"] == "http://localhost:11434"


class TestListAnthropicModelsAuthError:
    """list_anthropic_models wraps auth errors as LLMAuthError."""

    def test_auth_error_raises_llm_auth_error(self) -> None:
        mock_anthropic = _anthropic_mock()
        mock_anthropic.Anthropic.return_value.models.list.side_effect = _FakeAuthError(
            "invalid key"
        )
        with (
            patch.dict(sys.modules, {"anthropic": mock_anthropic}),
            patch(f"{_MODELS}.ANTHROPIC_AUTH_ERRORS", (_FakeAuthError,)),
        ):
            with pytest.raises(LLMAuthError):
                list_anthropic_models(api_key="k")

    def test_auth_error_message_contains_hints(self) -> None:
        mock_anthropic = _anthropic_mock()
        mock_anthropic.Anthropic.return_value.models.list.side_effect = _FakeAuthError(
            "invalid key"
        )
        with (
            patch.dict(sys.modules, {"anthropic": mock_anthropic}),
            patch(f"{_MODELS}.ANTHROPIC_AUTH_ERRORS", (_FakeAuthError,)),
        ):
            with pytest.raises(LLMAuthError, match="ANTHROPIC_API_KEY"):
                list_anthropic_models(api_key="k")
