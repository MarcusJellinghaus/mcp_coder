"""Tests for verify_langchain() on the ollama backend."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from mcp_coder.llm.providers.langchain.verification import verify_langchain


class TestVerifyLangchainOllama:
    """Tests for verify_langchain() on the ollama backend."""

    @patch("mcp_coder.llm.providers.langchain._models.check_ollama_tool_capability")
    @patch("mcp_coder.llm.providers.langchain._models._check_ollama_daemon")
    @patch("mcp_coder.llm.providers.langchain.verification._check_package_installed")
    @patch("mcp_coder.llm.providers.langchain.verification._load_langchain_config")
    def test_ollama_no_api_key_is_optional(
        self,
        mock_config: MagicMock,
        mock_pkg: MagicMock,
        mock_daemon: MagicMock,
        mock_cap: MagicMock,
    ) -> None:
        mock_config.return_value = {
            "provider": "langchain",
            "backend": "ollama",
            "model": "llama3",
            "api_key": None,
            "endpoint": None,
            "api_version": None,
        }
        mock_pkg.return_value = True
        mock_daemon.return_value = {
            "ok": True,
            "value": "local Ollama daemon reachable at http://localhost:11434",
        }
        mock_cap.return_value = {"ok": True, "value": "model 'llama3' supports tools"}
        with patch.dict("os.environ", {}, clear=True):
            result = verify_langchain()
        assert result["api_key"]["ok"] is True
        assert result["api_key"]["value"] == "not set (optional)"
        assert result["api_key"]["source"] is None
        assert result["overall_ok"] is True

    @patch("mcp_coder.llm.providers.langchain._models._check_ollama_daemon")
    @patch("mcp_coder.llm.providers.langchain.verification._check_package_installed")
    @patch("mcp_coder.llm.providers.langchain.verification._load_langchain_config")
    def test_ollama_with_api_key_works_as_before(
        self,
        mock_config: MagicMock,
        mock_pkg: MagicMock,
        mock_daemon: MagicMock,
    ) -> None:
        mock_config.return_value = {
            "provider": "langchain",
            "backend": "ollama",
            "model": "llama3",
            "api_key": "ollama-proxy-key-1234",
            "endpoint": None,
            "api_version": None,
        }
        mock_pkg.return_value = True
        mock_daemon.return_value = {"ok": True, "value": "reachable"}
        with patch.dict("os.environ", {}, clear=True):
            result = verify_langchain()
        assert result["api_key"]["ok"] is True
        assert result["api_key"]["value"] == "olla...1234"
        assert result["api_key"]["source"] == "config.toml"

    @patch("mcp_coder.llm.providers.langchain._models.check_ollama_tool_capability")
    @patch("mcp_coder.llm.providers.langchain._models._check_ollama_daemon")
    @patch("mcp_coder.llm.providers.langchain.verification._check_package_installed")
    @patch("mcp_coder.llm.providers.langchain.verification._load_langchain_config")
    def test_ollama_daemon_reachable(
        self,
        mock_config: MagicMock,
        mock_pkg: MagicMock,
        mock_daemon: MagicMock,
        mock_cap: MagicMock,
    ) -> None:
        mock_config.return_value = {
            "provider": "langchain",
            "backend": "ollama",
            "model": "llama3",
            "api_key": None,
            "endpoint": None,
            "api_version": None,
        }
        mock_pkg.return_value = True
        mock_daemon.return_value = {
            "ok": True,
            "value": "local Ollama daemon reachable at http://localhost:11434",
        }
        mock_cap.return_value = {"ok": True, "value": "model 'llama3' supports tools"}
        with patch.dict("os.environ", {}, clear=True):
            result = verify_langchain()
        assert "ollama_daemon" in result
        assert result["ollama_daemon"]["ok"] is True
        assert result["overall_ok"] is True

    @patch("mcp_coder.llm.providers.langchain._models._check_ollama_daemon")
    @patch("mcp_coder.llm.providers.langchain.verification._check_package_installed")
    @patch("mcp_coder.llm.providers.langchain.verification._load_langchain_config")
    def test_ollama_daemon_unreachable_fails_overall(
        self,
        mock_config: MagicMock,
        mock_pkg: MagicMock,
        mock_daemon: MagicMock,
    ) -> None:
        mock_config.return_value = {
            "provider": "langchain",
            "backend": "ollama",
            "model": "llama3",
            "api_key": None,
            "endpoint": None,
            "api_version": None,
        }
        mock_pkg.return_value = True
        mock_daemon.return_value = {
            "ok": False,
            "value": "local Ollama daemon not reachable — is `ollama serve` running?",
        }
        with patch.dict("os.environ", {}, clear=True):
            result = verify_langchain()
        assert result["ollama_daemon"]["ok"] is False
        assert result["overall_ok"] is False

    @patch("mcp_coder.llm.providers.langchain._models._check_ollama_daemon")
    @patch("mcp_coder.llm.providers.langchain.verification._check_package_installed")
    @patch("mcp_coder.llm.providers.langchain.verification._load_langchain_config")
    def test_ollama_daemon_auth_required_fails_overall(
        self,
        mock_config: MagicMock,
        mock_pkg: MagicMock,
        mock_daemon: MagicMock,
    ) -> None:
        mock_config.return_value = {
            "provider": "langchain",
            "backend": "ollama",
            "model": "llama3",
            "api_key": None,
            "endpoint": None,
            "api_version": None,
        }
        mock_pkg.return_value = True
        mock_daemon.return_value = {
            "ok": False,
            "value": (
                "local Ollama daemon reachable but auth required — "
                "set OLLAMA_API_KEY or api_key in config.toml"
            ),
        }
        with patch.dict("os.environ", {}, clear=True):
            result = verify_langchain()
        assert result["ollama_daemon"]["ok"] is False
        assert "auth required" in result["ollama_daemon"]["value"].lower()
        assert result["overall_ok"] is False

    @patch("mcp_coder.llm.providers.langchain.verification._check_package_installed")
    @patch("mcp_coder.llm.providers.langchain.verification._load_langchain_config")
    def test_non_ollama_backend_has_no_ollama_daemon_entry(
        self, mock_config: MagicMock, mock_pkg: MagicMock
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
        with patch.dict("os.environ", {}, clear=True):
            result = verify_langchain()
        assert "ollama_daemon" not in result

    @patch("mcp_coder.llm.providers.langchain._models._check_ollama_daemon")
    @patch("mcp_coder.llm.providers.langchain.verification._check_package_installed")
    @patch("mcp_coder.llm.providers.langchain.verification._load_langchain_config")
    def test_ollama_api_key_from_env_uses_normal_path(
        self,
        mock_config: MagicMock,
        mock_pkg: MagicMock,
        mock_daemon: MagicMock,
    ) -> None:
        """OLLAMA_API_KEY env var resolves through the normal masked path."""
        mock_config.return_value = {
            "provider": "langchain",
            "backend": "ollama",
            "model": "llama3",
            "api_key": None,
            "endpoint": None,
            "api_version": None,
        }
        mock_pkg.return_value = True
        mock_daemon.return_value = {"ok": True, "value": "reachable"}
        with patch.dict("os.environ", {"OLLAMA_API_KEY": "env-token-1234abcd"}):
            result = verify_langchain()
        assert result["api_key"]["ok"] is True
        assert result["api_key"]["source"] == "OLLAMA_API_KEY env var"
        assert result["api_key"]["value"] == "env-...abcd"

    @patch("mcp_coder.llm.providers.langchain._models.check_ollama_tool_capability")
    @patch("mcp_coder.llm.providers.langchain._models._check_ollama_daemon")
    @patch("mcp_coder.llm.providers.langchain.verification._check_package_installed")
    @patch("mcp_coder.llm.providers.langchain.verification._load_langchain_config")
    def test_ollama_capability_entry_present_when_model_configured(
        self,
        mock_config: MagicMock,
        mock_pkg: MagicMock,
        mock_daemon: MagicMock,
        mock_cap: MagicMock,
    ) -> None:
        mock_config.return_value = {
            "provider": "langchain",
            "backend": "ollama",
            "model": "llama3",
            "api_key": None,
            "endpoint": None,
            "api_version": None,
        }
        mock_pkg.return_value = True
        mock_daemon.return_value = {"ok": True, "value": "reachable"}
        mock_cap.return_value = {"ok": True, "value": "model 'llama3' supports tools"}
        with patch.dict("os.environ", {}, clear=True):
            result = verify_langchain()
        assert "ollama_tools_capability" in result
        assert result["ollama_tools_capability"]["ok"] is True

    @patch("mcp_coder.llm.providers.langchain._models.check_ollama_tool_capability")
    @patch("mcp_coder.llm.providers.langchain._models._check_ollama_daemon")
    @patch("mcp_coder.llm.providers.langchain.verification._check_package_installed")
    @patch("mcp_coder.llm.providers.langchain.verification._load_langchain_config")
    def test_ollama_capability_missing_fails_overall_ok(
        self,
        mock_config: MagicMock,
        mock_pkg: MagicMock,
        mock_daemon: MagicMock,
        mock_cap: MagicMock,
    ) -> None:
        mock_config.return_value = {
            "provider": "langchain",
            "backend": "ollama",
            "model": "llama3",
            "api_key": None,
            "endpoint": None,
            "api_version": None,
        }
        mock_pkg.return_value = True
        mock_daemon.return_value = {"ok": True, "value": "reachable"}
        mock_cap.return_value = {
            "ok": False,
            "value": "model 'llama3' does not advertise the 'tools' capability",
        }
        with patch.dict("os.environ", {}, clear=True):
            result = verify_langchain()
        assert result["ollama_tools_capability"]["ok"] is False
        assert result["overall_ok"] is False

    @patch("mcp_coder.llm.providers.langchain._models.check_ollama_tool_capability")
    @patch("mcp_coder.llm.providers.langchain._models._check_ollama_daemon")
    @patch("mcp_coder.llm.providers.langchain.verification._check_package_installed")
    @patch("mcp_coder.llm.providers.langchain.verification._load_langchain_config")
    def test_ollama_capability_present_does_not_fail_overall_ok(
        self,
        mock_config: MagicMock,
        mock_pkg: MagicMock,
        mock_daemon: MagicMock,
        mock_cap: MagicMock,
    ) -> None:
        mock_config.return_value = {
            "provider": "langchain",
            "backend": "ollama",
            "model": "llama3",
            "api_key": None,
            "endpoint": None,
            "api_version": None,
        }
        mock_pkg.return_value = True
        mock_daemon.return_value = {"ok": True, "value": "reachable"}
        mock_cap.return_value = {"ok": True, "value": "model 'llama3' supports tools"}
        with patch.dict("os.environ", {}, clear=True):
            result = verify_langchain()
        assert result["ollama_tools_capability"]["ok"] is True
        assert result["overall_ok"] is True

    @patch("mcp_coder.llm.providers.langchain._models._check_ollama_daemon")
    @patch("mcp_coder.llm.providers.langchain.verification._check_package_installed")
    @patch("mcp_coder.llm.providers.langchain.verification._load_langchain_config")
    def test_ollama_no_model_omits_capability_entry(
        self,
        mock_config: MagicMock,
        mock_pkg: MagicMock,
        mock_daemon: MagicMock,
    ) -> None:
        mock_config.return_value = {
            "provider": "langchain",
            "backend": "ollama",
            "model": None,
            "api_key": None,
            "endpoint": None,
            "api_version": None,
        }
        mock_pkg.return_value = True
        mock_daemon.return_value = {"ok": True, "value": "reachable"}
        with patch.dict("os.environ", {}, clear=True):
            result = verify_langchain()
        assert "ollama_tools_capability" not in result
        assert result["model"]["ok"] is False
