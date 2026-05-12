"""Tests for mcp_coder.llm.providers.langchain.ollama_backend."""

from unittest.mock import MagicMock, patch

import pytest


class TestResolveOllamaHost:
    """Tests for _resolve_ollama_host() helper in _models.py."""

    def test_env_overrides_config_endpoint(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """OLLAMA_HOST env var takes priority over endpoint argument."""
        monkeypatch.setenv("OLLAMA_HOST", "foo:1234")
        from mcp_coder.llm.providers.langchain._models import _resolve_ollama_host

        assert _resolve_ollama_host("bar:5678") == "http://foo:1234"

    def test_normalization_adds_http_scheme(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """OLLAMA_HOST without scheme gets http:// prefix."""
        monkeypatch.setenv("OLLAMA_HOST", "127.0.0.1:11434")
        from mcp_coder.llm.providers.langchain._models import _resolve_ollama_host

        assert _resolve_ollama_host(None) == "http://127.0.0.1:11434"

    def test_scheme_passes_through(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """OLLAMA_HOST that already includes a scheme is not modified."""
        monkeypatch.setenv("OLLAMA_HOST", "https://ollama.example.com")
        from mcp_coder.llm.providers.langchain._models import _resolve_ollama_host

        assert _resolve_ollama_host(None) == "https://ollama.example.com"

    def test_no_endpoint_no_env_returns_none(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Neither env nor endpoint set → returns None."""
        monkeypatch.delenv("OLLAMA_HOST", raising=False)
        from mcp_coder.llm.providers.langchain._models import _resolve_ollama_host

        assert _resolve_ollama_host(None) is None

    def test_endpoint_used_when_env_absent(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """endpoint argument is used when env var is absent."""
        monkeypatch.delenv("OLLAMA_HOST", raising=False)
        from mcp_coder.llm.providers.langchain._models import _resolve_ollama_host

        assert _resolve_ollama_host("bar:5678") == "http://bar:5678"


class TestCreateOllamaModel:
    """Tests for create_ollama_model() factory."""

    def test_ollama_host_env_overrides_config_endpoint(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """OLLAMA_HOST env var overrides endpoint argument."""
        monkeypatch.setenv("OLLAMA_HOST", "foo:1234")
        monkeypatch.delenv("OLLAMA_API_KEY", raising=False)
        with patch(
            "mcp_coder.llm.providers.langchain.ollama_backend.ChatOllama"
        ) as MockChat:
            from mcp_coder.llm.providers.langchain.ollama_backend import (
                create_ollama_model,
            )

            create_ollama_model(model="llama3.1", api_key=None, endpoint="bar:5678")
            _, kwargs = MockChat.call_args
            assert kwargs.get("base_url") == "http://foo:1234"

    def test_ollama_host_normalization_adds_http_scheme(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """OLLAMA_HOST=127.0.0.1:11434 → base_url=http://127.0.0.1:11434."""
        monkeypatch.setenv("OLLAMA_HOST", "127.0.0.1:11434")
        monkeypatch.delenv("OLLAMA_API_KEY", raising=False)
        with patch(
            "mcp_coder.llm.providers.langchain.ollama_backend.ChatOllama"
        ) as MockChat:
            from mcp_coder.llm.providers.langchain.ollama_backend import (
                create_ollama_model,
            )

            create_ollama_model(model="llama3.1", api_key=None)
            _, kwargs = MockChat.call_args
            assert kwargs.get("base_url") == "http://127.0.0.1:11434"

    def test_ollama_host_with_scheme_passes_through(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """OLLAMA_HOST that has a scheme is passed through unchanged."""
        monkeypatch.setenv("OLLAMA_HOST", "https://ollama.example.com")
        monkeypatch.delenv("OLLAMA_API_KEY", raising=False)
        with patch(
            "mcp_coder.llm.providers.langchain.ollama_backend.ChatOllama"
        ) as MockChat:
            from mcp_coder.llm.providers.langchain.ollama_backend import (
                create_ollama_model,
            )

            create_ollama_model(model="llama3.1", api_key=None)
            _, kwargs = MockChat.call_args
            assert kwargs.get("base_url") == "https://ollama.example.com"

    def test_no_endpoint_no_env_omits_base_url(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Neither endpoint nor OLLAMA_HOST set → base_url kwarg not passed."""
        monkeypatch.delenv("OLLAMA_HOST", raising=False)
        monkeypatch.delenv("OLLAMA_API_KEY", raising=False)
        with patch(
            "mcp_coder.llm.providers.langchain.ollama_backend.ChatOllama"
        ) as MockChat:
            from mcp_coder.llm.providers.langchain.ollama_backend import (
                create_ollama_model,
            )

            create_ollama_model(model="llama3.1", api_key=None)
            _, kwargs = MockChat.call_args
            assert "base_url" not in kwargs

    def test_api_key_env_overrides_config(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """OLLAMA_API_KEY env var overrides api_key argument."""
        monkeypatch.delenv("OLLAMA_HOST", raising=False)
        monkeypatch.setenv("OLLAMA_API_KEY", "env-key")
        with patch(
            "mcp_coder.llm.providers.langchain.ollama_backend.ChatOllama"
        ) as MockChat:
            from mcp_coder.llm.providers.langchain.ollama_backend import (
                create_ollama_model,
            )

            create_ollama_model(model="llama3.1", api_key="config-key")
            _, kwargs = MockChat.call_args
            client_kwargs = kwargs.get("client_kwargs")
            assert client_kwargs is not None
            assert client_kwargs["headers"]["Authorization"] == "Bearer env-key"

    def test_no_api_key_omits_client_kwargs(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """When no api_key is set anywhere, client_kwargs is not passed."""
        monkeypatch.delenv("OLLAMA_HOST", raising=False)
        monkeypatch.delenv("OLLAMA_API_KEY", raising=False)
        with patch(
            "mcp_coder.llm.providers.langchain.ollama_backend.ChatOllama"
        ) as MockChat:
            from mcp_coder.llm.providers.langchain.ollama_backend import (
                create_ollama_model,
            )

            create_ollama_model(model="llama3.1", api_key=None)
            _, kwargs = MockChat.call_args
            assert "client_kwargs" not in kwargs

    def test_timeout_is_forwarded_as_float(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """timeout is forwarded to ChatOllama as float."""
        monkeypatch.delenv("OLLAMA_HOST", raising=False)
        monkeypatch.delenv("OLLAMA_API_KEY", raising=False)
        with patch(
            "mcp_coder.llm.providers.langchain.ollama_backend.ChatOllama"
        ) as MockChat:
            from mcp_coder.llm.providers.langchain.ollama_backend import (
                create_ollama_model,
            )

            create_ollama_model(model="llama3.1", api_key=None, timeout=45)
            _, kwargs = MockChat.call_args
            assert kwargs.get("timeout") == 45.0

    def test_returns_chat_ollama_instance(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """create_ollama_model returns the ChatOllama instance."""
        monkeypatch.delenv("OLLAMA_HOST", raising=False)
        monkeypatch.delenv("OLLAMA_API_KEY", raising=False)
        with patch(
            "mcp_coder.llm.providers.langchain.ollama_backend.ChatOllama"
        ) as MockChat:
            mock_instance = MagicMock()
            MockChat.return_value = mock_instance
            from mcp_coder.llm.providers.langchain.ollama_backend import (
                create_ollama_model,
            )

            result = create_ollama_model(model="llama3.1", api_key=None)
            assert result is mock_instance
