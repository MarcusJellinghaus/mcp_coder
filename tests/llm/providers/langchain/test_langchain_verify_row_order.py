"""Pin the row order verify_langchain() returns.

``mcp-coder verify`` prints rows in dict insertion order, and install hints
follow that order. Only targets that do not move during refactoring are
patched; the package rows exist whether a package is installed or not, so the
key order does not depend on the environment.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

import pytest

from mcp_coder.llm.providers.langchain.verification import verify_langchain

_VERIFICATION = "mcp_coder.llm.providers.langchain.verification"
_MODELS = "mcp_coder.llm.providers.langchain._models"
_OLLAMA = "mcp_coder.llm.providers.langchain.ollama_backend"


def test_row_order_ollama_with_probe_rows(monkeypatch: pytest.MonkeyPatch) -> None:
    """Every optional row present: redirect, override, ollama probes, listing."""
    pytest.importorskip("langchain_ollama")
    monkeypatch.setenv("OLLAMA_HOST", "http://box:11434")
    monkeypatch.setenv("OLLAMA_API_KEY", "env-key-12345678")
    config = {
        "default_provider": None,
        "backend": "ollama",
        "model": "llama3",
        "api_key": "cfg-key-12345678",
        "base_url": None,
        "api_version": None,
    }
    probe_ok = {"ok": True, "value": "ok"}
    with (
        patch(f"{_VERIFICATION}._load_langchain_config", return_value=config),
        # A real string, not a MagicMock: dialed_url() must yield a URL or the
        # redirect row disappears.
        patch(
            f"{_OLLAMA}.create_ollama_model",
            return_value=SimpleNamespace(base_url="http://box:11434"),
        ),
        patch(f"{_MODELS}._check_ollama_daemon", return_value=probe_ok),
        patch(f"{_MODELS}.check_ollama_tool_capability", return_value=probe_ok),
        patch(f"{_MODELS}.list_ollama_models", return_value=["llama3"]),
    ):
        result = verify_langchain(check_models=True)

    assert "base_url_redirect" in result
    assert "api_key_override" in result
    assert list(result) == [
        "backend",
        "model",
        "api_key",
        "effective_config",
        "langchain_core",
        "backend_package",
        "base_url_redirect",
        "api_key_override",
        "mcp_adapters",
        "langgraph",
        "ollama_daemon",
        "ollama_tools_capability",
        "available_models",
        "model_check",
        "overall_ok",
    ]


def test_row_order_without_probe_rows(monkeypatch: pytest.MonkeyPatch) -> None:
    """No probe rows: the MCP rows sit directly before overall_ok."""
    for var in ("GEMINI_API_KEY", "GOOGLE_API_KEY", "GOOGLE_GENAI_USE_VERTEXAI"):
        monkeypatch.delenv(var, raising=False)
    config = {
        "default_provider": None,
        "backend": "gemini",
        "model": "gemini-2.5-flash",
        "api_key": "cfg-key-12345678",
        "base_url": None,
        "api_version": None,
    }
    with patch(f"{_VERIFICATION}._load_langchain_config", return_value=config):
        result = verify_langchain(check_models=False)

    assert list(result) == [
        "backend",
        "model",
        "api_key",
        "effective_config",
        "langchain_core",
        "backend_package",
        "mcp_adapters",
        "langgraph",
        "overall_ok",
    ]
