"""Tests for verify_langchain() domain function."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.llm.providers.langchain.verification import (
    _check_mcp_adapter_packages,
    _check_model_listed,
    _check_package_installed,
    _mask_api_key,
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
            "base_url": None,
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
            "base_url": None,
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
            "base_url": None,
            "api_version": None,
        }
        with patch.dict("os.environ", {}, clear=True):
            result = verify_langchain()
        assert result["api_key"]["value"] == "sk-a...5678"
        assert result["api_key"]["source"] == "config.toml"

    @patch("mcp_coder.llm.providers.langchain.verification._check_package_installed")
    @patch("mcp_coder.llm.providers.langchain.verification._load_langchain_config")
    def test_no_api_key_fails_the_contract(
        self, mock_config: MagicMock, mock_pkg: MagicMock
    ) -> None:
        """No prompt is sent, but a required-and-missing api_key still fails.

        verify_langchain stopped sending a test prompt long ago; since step 9
        the per-backend contract supplies the verdict instead, so an openai
        config with no credential anywhere is exit-1 with a named cause.
        """
        mock_config.return_value = {
            "provider": "langchain",
            "backend": "openai",
            "model": "gpt-4o",
            "api_key": None,
            "base_url": None,
            "api_version": None,
        }
        mock_pkg.return_value = True
        with patch.dict("os.environ", {}, clear=True):
            result = verify_langchain()
        assert "test_prompt" not in result
        assert result["overall_ok"] is False
        assert "OPENAI_API_KEY" in result["api_key"]["value"]

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
            "base_url": None,
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
            "base_url": None,
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
            "base_url": None,
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
            "base_url": None,
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
            "base_url": None,
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
            "base_url": None,
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
            "base_url": None,
            "api_version": None,
        }
        # langchain_core ok, backend_package ok, mcp_adapters fail, langgraph ok
        mock_pkg.side_effect = [True, True, False, True]
        with patch.dict("os.environ", {}, clear=True):
            result = verify_langchain()
        assert result["mcp_adapters"]["ok"] is False
        assert result["overall_ok"] is False


class TestInstallHints:
    """Tests for install_hint fields in verification results."""

    @patch("mcp_coder.llm.providers.langchain.verification._check_package_installed")
    @patch("mcp_coder.llm.providers.langchain.verification._load_langchain_config")
    def test_langchain_core_missing_has_install_hint(
        self, mock_config: MagicMock, mock_pkg: MagicMock
    ) -> None:
        """When langchain-core is not installed, result includes install_hint."""
        mock_config.return_value = {
            "provider": "langchain",
            "backend": "openai",
            "model": "gpt-4o",
            "api_key": None,
            "base_url": None,
            "api_version": None,
        }
        # langchain_core missing, backend_package ok, mcp_adapters ok, langgraph ok
        mock_pkg.side_effect = [False, True, True, True]
        with patch.dict("os.environ", {}, clear=True):
            result = verify_langchain()
        assert result["langchain_core"]["ok"] is False
        assert result["langchain_core"]["install_hint"] == "pip install langchain-core"

    @patch("mcp_coder.llm.providers.langchain.verification._check_package_installed")
    @patch("mcp_coder.llm.providers.langchain.verification._load_langchain_config")
    def test_backend_package_missing_has_install_hint(
        self, mock_config: MagicMock, mock_pkg: MagicMock
    ) -> None:
        """When backend package is missing, result includes install_hint with correct pip name."""
        mock_config.return_value = {
            "provider": "langchain",
            "backend": "openai",
            "model": "gpt-4o",
            "api_key": None,
            "base_url": None,
            "api_version": None,
        }
        # langchain_core ok, backend_package missing, mcp_adapters ok, langgraph ok
        mock_pkg.side_effect = [True, False, True, True]
        with patch.dict("os.environ", {}, clear=True):
            result = verify_langchain()
        assert result["backend_package"]["ok"] is False
        assert (
            result["backend_package"]["install_hint"] == "pip install langchain-openai"
        )

    @patch("mcp_coder.llm.providers.langchain.verification._check_package_installed")
    def test_mcp_adapters_missing_has_install_hint(self, mock_pkg: MagicMock) -> None:
        """When langchain-mcp-adapters is missing, result includes install_hint."""
        # mcp_adapters missing, langgraph ok
        mock_pkg.side_effect = [False, True]
        result = _check_mcp_adapter_packages()
        assert result["mcp_adapters"]["ok"] is False
        assert (
            result["mcp_adapters"]["install_hint"]
            == "pip install langchain-mcp-adapters"
        )

    @patch("mcp_coder.llm.providers.langchain.verification._check_package_installed")
    def test_langgraph_missing_has_install_hint(self, mock_pkg: MagicMock) -> None:
        """When langgraph is missing, result includes install_hint."""
        # mcp_adapters ok, langgraph missing
        mock_pkg.side_effect = [True, False]
        result = _check_mcp_adapter_packages()
        assert result["langgraph"]["ok"] is False
        assert result["langgraph"]["install_hint"] == "pip install langgraph"

    @patch("mcp_coder.llm.providers.langchain.verification._check_package_installed")
    @patch("mcp_coder.llm.providers.langchain.verification._load_langchain_config")
    def test_installed_packages_have_no_install_hint(
        self, mock_config: MagicMock, mock_pkg: MagicMock
    ) -> None:
        """When packages are installed, no install_hint key is present."""
        mock_config.return_value = {
            "provider": "langchain",
            "backend": "openai",
            "model": "gpt-4o",
            "api_key": None,
            "base_url": None,
            "api_version": None,
        }
        mock_pkg.return_value = True
        with patch.dict("os.environ", {}, clear=True):
            result = verify_langchain()
        assert "install_hint" not in result["langchain_core"]
        assert "install_hint" not in result["backend_package"]
        assert "install_hint" not in result["mcp_adapters"]
        assert "install_hint" not in result["langgraph"]

    @patch("mcp_coder.llm.providers.langchain.verification._check_package_installed")
    @patch("mcp_coder.llm.providers.langchain.verification._load_langchain_config")
    def test_no_backend_configured_no_install_hint(
        self, mock_config: MagicMock, mock_pkg: MagicMock
    ) -> None:
        """When no backend configured, backend_package has no install_hint."""
        mock_config.return_value = {
            "provider": "langchain",
            "backend": None,
            "model": None,
            "api_key": None,
            "base_url": None,
            "api_version": None,
        }
        mock_pkg.return_value = True
        with patch.dict("os.environ", {}, clear=True):
            result = verify_langchain()
        assert result["backend_package"]["ok"] is False
        assert "install_hint" not in result["backend_package"]


class TestListModelsForBackendErrors:
    """Tests for _list_models_for_backend error handling with specific exceptions."""

    @patch("mcp_coder.llm.providers.langchain._models.list_openai_models")
    def test_connection_error_returns_error_type_connection(
        self, mock_list: MagicMock
    ) -> None:
        from mcp_coder.llm.providers.langchain._exceptions import LLMConnectionError
        from mcp_coder.llm.providers.langchain.verification import (
            _list_models_for_backend,
        )

        mock_list.side_effect = LLMConnectionError("Connection to OpenAI API failed")
        result = _list_models_for_backend("openai", "sk-test", None)
        assert result["ok"] is False
        assert result["error_type"] == "connection"

    @patch("mcp_coder.llm.providers.langchain._models.list_openai_models")
    def test_auth_error_returns_error_type_auth(self, mock_list: MagicMock) -> None:
        from mcp_coder.llm.providers.langchain._exceptions import LLMAuthError
        from mcp_coder.llm.providers.langchain.verification import (
            _list_models_for_backend,
        )

        mock_list.side_effect = LLMAuthError("Authentication to OpenAI API failed")
        result = _list_models_for_backend("openai", "sk-test", None)
        assert result["ok"] is False
        assert result["error_type"] == "auth"

    @patch("mcp_coder.llm.providers.langchain._models.list_openai_models")
    def test_unknown_error_returns_error_type_unknown(
        self, mock_list: MagicMock
    ) -> None:
        from mcp_coder.llm.providers.langchain.verification import (
            _list_models_for_backend,
        )

        mock_list.side_effect = RuntimeError("something broke")
        result = _list_models_for_backend("openai", "sk-test", None)
        assert result["ok"] is False
        assert result["error_type"] == "unknown"

    @patch("mcp_coder.llm.providers.langchain._models.list_openai_models")
    def test_connection_error_message_preserved(self, mock_list: MagicMock) -> None:
        from mcp_coder.llm.providers.langchain._exceptions import LLMConnectionError
        from mcp_coder.llm.providers.langchain.verification import (
            _list_models_for_backend,
        )

        hint_msg = (
            "Connection to OpenAI API failed: some error\n"
            "Check:\n"
            "  1. OPENAI_API_KEY env var or api_key in config.toml"
        )
        mock_list.side_effect = LLMConnectionError(hint_msg)
        result = _list_models_for_backend("openai", "sk-test", None)
        assert result["error"] == hint_msg

    @patch("mcp_coder.llm.providers.langchain._models.list_openai_models")
    def test_auth_error_message_preserved(self, mock_list: MagicMock) -> None:
        from mcp_coder.llm.providers.langchain._exceptions import LLMAuthError
        from mcp_coder.llm.providers.langchain.verification import (
            _list_models_for_backend,
        )

        hint_msg = (
            "Authentication to OpenAI API failed: invalid key\n"
            "Check:\n"
            "  1. OPENAI_API_KEY env var is set and valid"
        )
        mock_list.side_effect = LLMAuthError(hint_msg)
        result = _list_models_for_backend("openai", "sk-test", None)
        assert result["error"] == hint_msg

    @patch("mcp_coder.llm.providers.langchain._models.list_openai_models")
    def test_success_has_no_error_type(self, mock_list: MagicMock) -> None:
        from mcp_coder.llm.providers.langchain.verification import (
            _list_models_for_backend,
        )

        mock_list.return_value = ["gpt-4o", "gpt-3.5-turbo"]
        result = _list_models_for_backend("openai", "sk-test", None)
        assert result["ok"] is True
        assert "error_type" not in result

    @patch("mcp_coder.llm.providers.langchain._models.list_openai_models")
    def test_404_with_base_url_returns_error_type_base_url(
        self, mock_list: MagicMock
    ) -> None:
        from mcp_coder.llm.providers.langchain.verification import (
            _list_models_for_backend,
        )

        mock_list.side_effect = Exception("Error code: 404 - {'detail': 'Not Found'}")
        result = _list_models_for_backend("openai", None, "https://h/v1/completions")
        assert result["ok"] is False
        assert result["error_type"] == "base_url"
        assert "base URL" in result["error"]
        assert "/chat/completions" in result["error"]

    @patch("mcp_coder.llm.providers.langchain._models.list_openai_models")
    def test_404_without_base_url_stays_unknown(self, mock_list: MagicMock) -> None:
        from mcp_coder.llm.providers.langchain.verification import (
            _list_models_for_backend,
        )

        mock_list.side_effect = Exception("Error code: 404 - {'detail': 'Not Found'}")
        result = _list_models_for_backend("openai", None, None)
        assert result["ok"] is False
        assert result["error_type"] == "unknown"
        assert "base URL" not in result["error"]

    @patch("mcp_coder.llm.providers.langchain._models.list_openai_models")
    def test_non_404_error_with_base_url_stays_unknown(
        self, mock_list: MagicMock
    ) -> None:
        from mcp_coder.llm.providers.langchain.verification import (
            _list_models_for_backend,
        )

        mock_list.side_effect = Exception("boom")
        result = _list_models_for_backend("openai", None, "https://h/v1/completions")
        assert result["ok"] is False
        assert result["error_type"] == "unknown"


class TestCheckModelListed:
    """Step 11 — cross-check the configured model against a model listing.

    The check is advisory: ``ok`` is ``True`` or ``None``, never ``False``.
    A relay that will not serve ``/models`` says nothing about whether the
    config is right, and a genuinely wrong model still fails the live test
    prompt, which already sets exit 1.
    """

    def test_model_present_in_listing(self) -> None:
        entry = _check_model_listed(
            "Qwen-2.5-72B", {"ok": True, "value": ["Qwen-2.5-72B", "gpt-4o"]}
        )
        assert entry["ok"] is True
        assert entry["value"] == "Qwen-2.5-72B found on server"

    def test_near_miss_is_suggested(self) -> None:
        entry = _check_model_listed(
            "Qwen-2.5-72b", {"ok": True, "value": ["Qwen-2.5-72B", "gpt-4o"]}
        )
        assert entry["ok"] is None
        assert "Qwen-2.5-72b not offered by the server (2 models listed)" in str(
            entry["value"]
        )
        assert "did you mean Qwen-2.5-72B?" in str(entry["value"])

    def test_no_near_miss_omits_suggestion(self) -> None:
        entry = _check_model_listed(
            "llama3.1", {"ok": True, "value": ["gpt-4o", "text-embedding-3-small"]}
        )
        assert entry["ok"] is None
        assert "llama3.1 not offered by the server (2 models listed)" in str(
            entry["value"]
        )
        assert "did you mean" not in str(entry["value"])

    def test_auth_failure_degrades_to_could_not_verify(self) -> None:
        entry = _check_model_listed(
            "gpt-4o",
            {
                "ok": False,
                "value": [],
                "error": "401 Unauthorized",
                "error_type": "auth",
            },
        )
        assert entry["ok"] is None
        assert entry["value"] == "could not verify (server does not expose /models)"

    def test_404_listing_degrades_to_could_not_verify(self) -> None:
        entry = _check_model_listed(
            "gpt-4o",
            {"ok": False, "value": [], "error": "404 Not Found", "error_type": "404"},
        )
        assert entry["ok"] is None
        assert entry["value"] == "could not verify (server does not expose /models)"

    def test_no_model_configured(self) -> None:
        entry = _check_model_listed(None, {"ok": True, "value": ["gpt-4o"]})
        assert entry["ok"] is None
        assert entry["value"] == "no model configured"

    def test_missing_value_key_counts_as_empty_listing(self) -> None:
        entry = _check_model_listed("gpt-4o", {"ok": True})
        assert entry["ok"] is None
        assert "0 models listed" in str(entry["value"])

    def test_never_reports_false(self) -> None:
        """No input shape may produce ok=False — that would move overall_ok."""
        listings: list[dict[str, object]] = [
            {"ok": True, "value": ["gpt-4o"]},
            {"ok": True, "value": []},
            {"ok": False, "value": []},
            {},
        ]
        for listing in listings:
            for model in ("gpt-4o", "nope", None):
                assert _check_model_listed(model, listing)["ok"] is not False


class TestModelCheckInVerify:
    """Wiring of model_check into verify_langchain()."""

    _CONFIG = {
        "provider": "langchain",
        "backend": "openai",
        "model": "gpt-4o",
        "api_key": "sk-test1234test5678",
        "base_url": None,
        "api_version": None,
    }

    @patch("mcp_coder.llm.providers.langchain.verification._list_models_for_backend")
    @patch("mcp_coder.llm.providers.langchain.verification._check_package_installed")
    @patch("mcp_coder.llm.providers.langchain.verification._load_langchain_config")
    def test_model_check_ok_when_listed(
        self,
        mock_config: MagicMock,
        mock_pkg: MagicMock,
        mock_list: MagicMock,
    ) -> None:
        mock_config.return_value = dict(self._CONFIG)
        mock_pkg.return_value = True
        mock_list.return_value = {"ok": True, "value": ["gpt-4o", "gpt-3.5-turbo"]}
        with patch.dict("os.environ", {}, clear=True):
            result = verify_langchain(check_models=True)
        assert result["model_check"]["ok"] is True
        assert result["model_check"]["value"] == "gpt-4o found on server"

    @patch("mcp_coder.llm.providers.langchain.verification._list_models_for_backend")
    @patch("mcp_coder.llm.providers.langchain.verification._check_package_installed")
    @patch("mcp_coder.llm.providers.langchain.verification._load_langchain_config")
    def test_wrong_model_warns_but_keeps_overall_ok(
        self,
        mock_config: MagicMock,
        mock_pkg: MagicMock,
        mock_list: MagicMock,
    ) -> None:
        mock_config.return_value = dict(self._CONFIG)
        mock_pkg.return_value = True
        mock_list.return_value = {"ok": True, "value": ["gpt-4p", "gpt-3.5-turbo"]}
        with patch.dict("os.environ", {}, clear=True):
            result = verify_langchain(check_models=True)
        assert result["model_check"]["ok"] is None
        assert "not offered by the server" in result["model_check"]["value"]
        assert result["overall_ok"] is True

    @patch("mcp_coder.llm.providers.langchain.verification._list_models_for_backend")
    @patch("mcp_coder.llm.providers.langchain.verification._check_package_installed")
    @patch("mcp_coder.llm.providers.langchain.verification._load_langchain_config")
    def test_failed_listing_keeps_overall_ok(
        self,
        mock_config: MagicMock,
        mock_pkg: MagicMock,
        mock_list: MagicMock,
    ) -> None:
        mock_config.return_value = dict(self._CONFIG)
        mock_pkg.return_value = True
        mock_list.return_value = {
            "ok": False,
            "value": [],
            "error": "boom",
            "error_type": "unknown",
        }
        with patch.dict("os.environ", {}, clear=True):
            result = verify_langchain(check_models=True)
        assert result["model_check"]["ok"] is None
        assert "does not expose /models" in result["model_check"]["value"]
        assert result["overall_ok"] is True

    @patch("mcp_coder.llm.providers.langchain.verification._check_package_installed")
    @patch("mcp_coder.llm.providers.langchain.verification._load_langchain_config")
    def test_absent_without_check_models(
        self, mock_config: MagicMock, mock_pkg: MagicMock
    ) -> None:
        mock_config.return_value = dict(self._CONFIG)
        mock_pkg.return_value = True
        with patch.dict("os.environ", {}, clear=True):
            result = verify_langchain()
        assert "model_check" not in result


class TestModelCheckLabel:
    """Without a label entry the row renders as the raw dict key."""

    def test_label_map_entry(self) -> None:
        from mcp_coder.cli.commands.verify_formatting import _LABEL_MAP

        assert _LABEL_MAP["model_check"] == "Model available"
