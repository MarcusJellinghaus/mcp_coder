"""Tests for verify_langchain() domain function."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.llm.providers.langchain.verification import (
    _check_mcp_adapter_packages,
    _check_package_installed,
    _mask_api_key,
    _resolve_api_key,
    verify_langchain,
)


class TestMaskApiKey:
    """Focused tests for _mask_api_key helper."""

    def test_normal_key(self) -> None:
        assert _mask_api_key("sk-abcd1234wxyz5678") == "sk-a...5678"

    def test_short_key(self) -> None:
        assert _mask_api_key("short") == "****"

    def test_exactly_8_chars(self) -> None:
        assert _mask_api_key("12345678") == "****"

    def test_9_chars(self) -> None:
        assert _mask_api_key("123456789") == "1234...6789"

    def test_none(self) -> None:
        assert _mask_api_key(None) is None

    def test_empty_string(self) -> None:
        assert _mask_api_key("") is None


class TestResolveApiKey:
    """Tests for _resolve_api_key helper."""

    def test_env_var_takes_precedence(self) -> None:
        with patch.dict("os.environ", {"OPENAI_API_KEY": "env-key"}):
            key, source = _resolve_api_key("openai", "config-key")
        assert key == "env-key"
        assert source == "OPENAI_API_KEY env var"

    def test_falls_back_to_config(self) -> None:
        with patch.dict("os.environ", {}, clear=True):
            key, source = _resolve_api_key("openai", "config-key")
        assert key == "config-key"
        assert source == "config.toml"

    def test_no_key_available(self) -> None:
        with patch.dict("os.environ", {}, clear=True):
            key, source = _resolve_api_key("openai", None)
        assert key is None
        assert source is None

    def test_gemini_env_var(self) -> None:
        with patch.dict("os.environ", {"GEMINI_API_KEY": "gem-key"}):
            key, source = _resolve_api_key("gemini", None)
        assert key == "gem-key"
        assert source == "GEMINI_API_KEY env var"

    def test_anthropic_env_var(self) -> None:
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "ant-key"}):
            key, source = _resolve_api_key("anthropic", None)
        assert key == "ant-key"
        assert source == "ANTHROPIC_API_KEY env var"

    def test_unknown_backend(self) -> None:
        with patch.dict("os.environ", {}, clear=True):
            key, source = _resolve_api_key("unknown", "config-key")
        assert key == "config-key"
        assert source == "config.toml"

    def test_none_backend(self) -> None:
        with patch.dict("os.environ", {}, clear=True):
            key, source = _resolve_api_key(None, None)
        assert key is None
        assert source is None


class TestCheckPackageInstalled:
    """Tests for _check_package_installed helper."""

    def test_installed_package(self) -> None:
        assert _check_package_installed("os") is True

    def test_not_installed_package(self) -> None:
        assert _check_package_installed("nonexistent_package_xyz_123") is False


class TestVerifyLangchain:
    """Tests for verify_langchain() domain function."""

    @patch("mcp_coder.llm.providers.langchain.verification._load_langchain_config")
    def test_no_backend_configured(self, mock_config: MagicMock) -> None:
        mock_config.return_value = {
            "provider": "langchain",
            "backend": None,
            "model": None,
            "api_key": None,
            "endpoint": None,
            "api_version": None,
        }
        with patch.dict("os.environ", {}, clear=True):
            result = verify_langchain()
        assert result["backend"]["ok"] is False
        assert result["overall_ok"] is False

    @patch("mcp_coder.llm.providers.langchain.verification._check_package_installed")
    @patch("mcp_coder.llm.providers.langchain.verification._load_langchain_config")
    def test_openai_backend_configured(
        self, mock_config: MagicMock, mock_pkg: MagicMock
    ) -> None:
        mock_config.return_value = {
            "provider": "langchain",
            "backend": "openai",
            "model": "gpt-4o",
            "api_key": "sk-abcd1234wxyz5678",
            "endpoint": None,
            "api_version": None,
        }
        mock_pkg.return_value = True
        with patch.dict("os.environ", {}, clear=True):
            result = verify_langchain()
        assert result["backend"]["ok"] is True
        assert result["backend"]["value"] == "openai"
        assert result["model"]["value"] == "gpt-4o"

    @patch("mcp_coder.llm.providers.langchain.verification._load_langchain_config")
    def test_api_key_masking_in_result(self, mock_config: MagicMock) -> None:
        mock_config.return_value = {
            "provider": "langchain",
            "backend": "openai",
            "model": "gpt-4o",
            "api_key": "sk-abcd1234wxyz5678",
            "endpoint": None,
            "api_version": None,
        }
        with patch.dict("os.environ", {}, clear=True):
            result = verify_langchain()
        assert result["api_key"]["value"] == "sk-a...5678"
        assert result["api_key"]["source"] == "config.toml"

    @patch("mcp_coder.llm.providers.langchain.verification._check_package_installed")
    @patch("mcp_coder.llm.providers.langchain.verification._load_langchain_config")
    def test_no_api_key_overall_ok_true(
        self, mock_config: MagicMock, mock_pkg: MagicMock
    ) -> None:
        """overall_ok is True even when no API key (verify_langchain no longer tests prompt)."""
        mock_config.return_value = {
            "provider": "langchain",
            "backend": "openai",
            "model": "gpt-4o",
            "api_key": None,
            "endpoint": None,
            "api_version": None,
        }
        mock_pkg.return_value = True
        with patch.dict("os.environ", {}, clear=True):
            result = verify_langchain()
        assert "test_prompt" not in result
        assert result["overall_ok"] is True

    @patch("mcp_coder.llm.providers.langchain.verification._check_package_installed")
    @patch("mcp_coder.llm.providers.langchain.verification._load_langchain_config")
    def test_langchain_core_not_installed(
        self, mock_config: MagicMock, mock_pkg: MagicMock
    ) -> None:
        mock_config.return_value = {
            "provider": "langchain",
            "backend": "openai",
            "model": "gpt-4o",
            "api_key": None,
            "endpoint": None,
            "api_version": None,
        }
        # langchain_core missing, backend_package ok, mcp_adapters ok, langgraph ok
        mock_pkg.side_effect = [False, True, True, True]
        with patch.dict("os.environ", {}, clear=True):
            result = verify_langchain()
        assert result["langchain_core"]["ok"] is False
        assert result["langchain_core"]["value"] == "not installed"

    @patch("mcp_coder.llm.providers.langchain.verification._list_models_for_backend")
    @patch("mcp_coder.llm.providers.langchain.verification._check_package_installed")
    @patch("mcp_coder.llm.providers.langchain.verification._load_langchain_config")
    def test_check_models_flag(
        self,
        mock_config: MagicMock,
        mock_pkg: MagicMock,
        mock_list: MagicMock,
    ) -> None:
        mock_config.return_value = {
            "provider": "langchain",
            "backend": "openai",
            "model": "gpt-4o",
            "api_key": "sk-test1234test5678",
            "endpoint": None,
            "api_version": None,
        }
        mock_pkg.return_value = True
        mock_list.return_value = {"ok": True, "value": ["gpt-4o", "gpt-3.5-turbo"]}
        with patch.dict("os.environ", {}, clear=True):
            result = verify_langchain(check_models=True)
        assert "available_models" in result
        assert result["available_models"]["ok"] is True

    @patch("mcp_coder.llm.providers.langchain.verification._check_package_installed")
    @patch("mcp_coder.llm.providers.langchain.verification._load_langchain_config")
    def test_check_models_not_present_by_default(
        self, mock_config: MagicMock, mock_pkg: MagicMock
    ) -> None:
        mock_config.return_value = {
            "provider": "langchain",
            "backend": "openai",
            "model": "gpt-4o",
            "api_key": None,
            "endpoint": None,
            "api_version": None,
        }
        mock_pkg.return_value = True
        with patch.dict("os.environ", {}, clear=True):
            result = verify_langchain()
        assert "available_models" not in result

    @patch("mcp_coder.llm.providers.langchain.verification._check_package_installed")
    @patch("mcp_coder.llm.providers.langchain.verification._load_langchain_config")
    def test_backend_package_not_installed(
        self, mock_config: MagicMock, mock_pkg: MagicMock
    ) -> None:
        mock_config.return_value = {
            "provider": "langchain",
            "backend": "openai",
            "model": "gpt-4o",
            "api_key": None,
            "endpoint": None,
            "api_version": None,
        }
        # langchain_core ok, backend_package missing, mcp_adapters ok, langgraph ok
        mock_pkg.side_effect = [True, False, True, True]
        with patch.dict("os.environ", {}, clear=True):
            result = verify_langchain()
        assert result["backend_package"]["ok"] is False
        assert result["overall_ok"] is False

    @patch("mcp_coder.llm.providers.langchain.verification._check_package_installed")
    @patch("mcp_coder.llm.providers.langchain.verification._load_langchain_config")
    def test_api_key_from_env_var(
        self, mock_config: MagicMock, mock_pkg: MagicMock
    ) -> None:
        mock_config.return_value = {
            "provider": "langchain",
            "backend": "openai",
            "model": "gpt-4o",
            "api_key": None,
            "endpoint": None,
            "api_version": None,
        }
        mock_pkg.return_value = True
        with patch.dict("os.environ", {"OPENAI_API_KEY": "sk-from-env-12345678"}):
            result = verify_langchain()
        assert result["api_key"]["ok"] is True
        assert result["api_key"]["source"] == "OPENAI_API_KEY env var"
        assert result["api_key"]["value"] == "sk-f...5678"


class TestCheckMcpAdapterPackages:
    """Tests for _check_mcp_adapter_packages helper."""

    @patch("mcp_coder.llm.providers.langchain.verification._check_package_installed")
    def test_both_installed(self, mock_pkg: MagicMock) -> None:
        mock_pkg.return_value = True
        result = _check_mcp_adapter_packages()
        assert result["mcp_adapters"]["ok"] is True
        assert "installed" in result["mcp_adapters"]["value"]
        assert result["langgraph"]["ok"] is True
        assert "installed" in result["langgraph"]["value"]

    @patch("mcp_coder.llm.providers.langchain.verification._check_package_installed")
    def test_mcp_adapters_missing(self, mock_pkg: MagicMock) -> None:
        # langchain_mcp_adapters missing, langgraph installed
        mock_pkg.side_effect = [False, True]
        result = _check_mcp_adapter_packages()
        assert result["mcp_adapters"]["ok"] is False
        assert "not installed" in result["mcp_adapters"]["value"]
        assert result["langgraph"]["ok"] is True

    @patch("mcp_coder.llm.providers.langchain.verification._check_package_installed")
    def test_langgraph_missing(self, mock_pkg: MagicMock) -> None:
        # langchain_mcp_adapters installed, langgraph missing
        mock_pkg.side_effect = [True, False]
        result = _check_mcp_adapter_packages()
        assert result["mcp_adapters"]["ok"] is True
        assert result["langgraph"]["ok"] is False
        assert "not installed" in result["langgraph"]["value"]


class TestVerifyLangchainMcpSection:
    """Tests for MCP-related sections in verify_langchain()."""

    @patch("mcp_coder.llm.providers.langchain.verification._check_package_installed")
    @patch("mcp_coder.llm.providers.langchain.verification._load_langchain_config")
    def test_includes_mcp_adapter_check(
        self, mock_config: MagicMock, mock_pkg: MagicMock
    ) -> None:
        """verify_langchain() result includes mcp_adapters entry."""
        mock_config.return_value = {
            "provider": "langchain",
            "backend": "openai",
            "model": "gpt-4o",
            "api_key": None,
            "endpoint": None,
            "api_version": None,
        }
        mock_pkg.return_value = True
        with patch.dict("os.environ", {}, clear=True):
            result = verify_langchain()
        assert "mcp_adapters" in result
        assert "langgraph" in result
        assert result["mcp_adapters"]["ok"] is True
        assert result["langgraph"]["ok"] is True

    @patch("mcp_coder.llm.providers.langchain.verification._check_package_installed")
    @patch("mcp_coder.llm.providers.langchain.verification._load_langchain_config")
    def test_mcp_adapters_missing_fails_overall(
        self, mock_config: MagicMock, mock_pkg: MagicMock
    ) -> None:
        """overall_ok is False when MCP adapter packages are missing."""
        mock_config.return_value = {
            "provider": "langchain",
            "backend": "openai",
            "model": "gpt-4o",
            "api_key": None,
            "endpoint": None,
            "api_version": None,
        }
        # langchain_core ok, backend_package ok, mcp_adapters fail, langgraph ok
        mock_pkg.side_effect = [True, True, False, True]
        with patch.dict("os.environ", {}, clear=True):
            result = verify_langchain()
        assert result["mcp_adapters"]["ok"] is False
        assert result["overall_ok"] is False


class TestListModelsForBackendErrors:
    """Tests for _list_models_for_backend error handling with specific exceptions."""

    @patch("mcp_coder.llm.providers.langchain.verification._models")
    def test_connection_error_returns_error_type_connection(
        self, mock_models: MagicMock
    ) -> None:
        from mcp_coder.llm.providers.langchain._exceptions import LLMConnectionError
        from mcp_coder.llm.providers.langchain.verification import (
            _list_models_for_backend,
        )

        mock_models.list_openai_models.side_effect = LLMConnectionError(
            "Connection to OpenAI API failed"
        )
        result = _list_models_for_backend("openai", "sk-test", None)
        assert result["ok"] is False
        assert result["error_type"] == "connection"

    @patch("mcp_coder.llm.providers.langchain.verification._models")
    def test_auth_error_returns_error_type_auth(self, mock_models: MagicMock) -> None:
        from mcp_coder.llm.providers.langchain._exceptions import LLMAuthError
        from mcp_coder.llm.providers.langchain.verification import (
            _list_models_for_backend,
        )

        mock_models.list_openai_models.side_effect = LLMAuthError(
            "Authentication to OpenAI API failed"
        )
        result = _list_models_for_backend("openai", "sk-test", None)
        assert result["ok"] is False
        assert result["error_type"] == "auth"

    @patch("mcp_coder.llm.providers.langchain.verification._models")
    def test_unknown_error_returns_error_type_unknown(
        self, mock_models: MagicMock
    ) -> None:
        from mcp_coder.llm.providers.langchain.verification import (
            _list_models_for_backend,
        )

        mock_models.list_openai_models.side_effect = RuntimeError("something broke")
        result = _list_models_for_backend("openai", "sk-test", None)
        assert result["ok"] is False
        assert result["error_type"] == "unknown"

    @patch("mcp_coder.llm.providers.langchain.verification._models")
    def test_connection_error_message_preserved(self, mock_models: MagicMock) -> None:
        from mcp_coder.llm.providers.langchain._exceptions import LLMConnectionError
        from mcp_coder.llm.providers.langchain.verification import (
            _list_models_for_backend,
        )

        hint_msg = (
            "Connection to OpenAI API failed: some error\n"
            "Check:\n"
            "  1. OPENAI_API_KEY env var or api_key in config.toml"
        )
        mock_models.list_openai_models.side_effect = LLMConnectionError(hint_msg)
        result = _list_models_for_backend("openai", "sk-test", None)
        assert result["error"] == hint_msg

    @patch("mcp_coder.llm.providers.langchain.verification._models")
    def test_auth_error_message_preserved(self, mock_models: MagicMock) -> None:
        from mcp_coder.llm.providers.langchain._exceptions import LLMAuthError
        from mcp_coder.llm.providers.langchain.verification import (
            _list_models_for_backend,
        )

        hint_msg = (
            "Authentication to OpenAI API failed: invalid key\n"
            "Check:\n"
            "  1. OPENAI_API_KEY env var is set and valid"
        )
        mock_models.list_openai_models.side_effect = LLMAuthError(hint_msg)
        result = _list_models_for_backend("openai", "sk-test", None)
        assert result["error"] == hint_msg

    @patch("mcp_coder.llm.providers.langchain.verification._models")
    def test_success_has_no_error_type(self, mock_models: MagicMock) -> None:
        from mcp_coder.llm.providers.langchain.verification import (
            _list_models_for_backend,
        )

        mock_models.list_openai_models.return_value = ["gpt-4o", "gpt-3.5-turbo"]
        result = _list_models_for_backend("openai", "sk-test", None)
        assert result["ok"] is True
        assert "error_type" not in result
