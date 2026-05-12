"""Tests for Ollama-specific helpers in mcp_coder.llm.providers.langchain._models.

Covers:
    - list_ollama_models() via the ollama Python client
    - _check_ollama_daemon() reachability probe (401/403/connect/timeout)
    - check_ollama_tool_capability() tool-capability check via /api/show

These tests use sys.modules mocking for the ollama package so they work
regardless of whether the optional SDK is installed.
"""

from __future__ import annotations

import sys
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.llm.providers.langchain._exceptions import LLMConnectionError
from mcp_coder.llm.providers.langchain._models import (
    _check_ollama_daemon,
    check_ollama_tool_capability,
    list_ollama_models,
)


def _ollama_mock() -> MagicMock:
    """Create a fresh mock ollama module."""
    return MagicMock()


def _make_ollama_model(name: str) -> dict[str, str]:
    """Create a mock Ollama model entry as returned by client.list()."""
    return {"name": name}


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

    def test_passes_auth_header_when_api_key_set(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """api_key is forwarded as a Bearer header when set, omitted when None."""
        monkeypatch.delenv("OLLAMA_HOST", raising=False)
        mock_ollama = _ollama_mock()
        mock_ollama.Client.return_value.list.return_value = {"models": []}
        with patch.dict(sys.modules, {"ollama": mock_ollama}):
            list_ollama_models(api_key="my-token")
        _, kwargs = mock_ollama.Client.call_args
        assert kwargs.get("headers") == {"Authorization": "Bearer my-token"}

        mock_ollama.Client.reset_mock()
        mock_ollama.Client.return_value.list.return_value = {"models": []}
        with patch.dict(sys.modules, {"ollama": mock_ollama}):
            list_ollama_models(api_key=None)
        _, kwargs = mock_ollama.Client.call_args
        assert "headers" not in kwargs


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
