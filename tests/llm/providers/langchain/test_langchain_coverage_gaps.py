"""Tests for coverage gaps: empty messages, non-dict servers, forwarding, ImportError."""

import json
import logging
import sys
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from mcp_coder.llm.providers.langchain.agent import _load_mcp_server_config

# ---------------------------------------------------------------------------
# 1. Empty message list in _ask_text
# ---------------------------------------------------------------------------


class TestAskTextEmptyHistory:
    """Verify _ask_text handles empty prior history gracefully."""

    @staticmethod
    def _make_config(backend: str = "openai") -> dict[str, str | None]:
        return {
            "provider": "langchain",
            "backend": backend,
            "model": "gpt-4o",
            "api_key": None,
            "endpoint": None,
            "api_version": None,
        }

    def test_empty_history_produces_valid_response(self) -> None:
        """First-ever question (no prior history) returns a valid response."""
        mock_model = MagicMock()
        mock_ai_msg = MagicMock()
        mock_ai_msg.content = "Hello!"
        mock_ai_msg.model_dump.return_value = {"type": "ai", "content": "Hello!"}
        mock_model.invoke.return_value = mock_ai_msg

        with (
            patch(
                "mcp_coder.llm.providers.langchain._load_langchain_config",
                return_value=self._make_config(),
            ),
            patch(
                "mcp_coder.llm.providers.langchain.load_langchain_history",
                return_value=[],
            ),
            patch("mcp_coder.llm.providers.langchain.store_langchain_history") as store,
            patch(
                "mcp_coder.llm.providers.langchain._create_chat_model",
                return_value=mock_model,
            ),
        ):
            from mcp_coder.llm.providers.langchain import ask_langchain

            result = ask_langchain("Hi")

        assert result["text"] == "Hello!"

        # Model should have been invoked with exactly one message (the new question)
        call_args = mock_model.invoke.call_args[0][0]
        assert len(call_args) == 1

        # Stored history should have human + ai = 2 entries
        stored = store.call_args[0][1]
        assert len(stored) == 2
        assert stored[0]["type"] == "human"
        assert stored[1]["type"] == "ai"


# ---------------------------------------------------------------------------
# 2. Non-dict server entry skipping in _load_mcp_server_config
# ---------------------------------------------------------------------------


class TestNonDictServerEntrySkipping:
    """Verify _load_mcp_server_config skips non-dict server entries."""

    @staticmethod
    def _write_config(tmp_path: Path, config: dict[str, object]) -> str:
        cfg_file = tmp_path / ".mcp.json"
        cfg_file.write_text(json.dumps(config), encoding="utf-8")
        return str(cfg_file)

    def test_skips_string_server_entry(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """String server entry is skipped with a warning."""
        path = self._write_config(
            tmp_path,
            {
                "mcpServers": {
                    "bad": "not-a-dict",
                    "good": {"command": "echo"},
                }
            },
        )
        with caplog.at_level(logging.WARNING):
            result = _load_mcp_server_config(path)

        assert "bad" not in result
        assert "good" in result
        assert "Skipping non-dict server entry" in caplog.text
        assert "'bad'" in caplog.text

    def test_skips_list_server_entry(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """List server entry is skipped with a warning."""
        path = self._write_config(
            tmp_path,
            {
                "mcpServers": {
                    "bad_list": ["not", "a", "dict"],
                    "valid": {"command": "python", "args": ["-m", "server"]},
                }
            },
        )
        with caplog.at_level(logging.WARNING):
            result = _load_mcp_server_config(path)

        assert "bad_list" not in result
        assert "valid" in result
        assert result["valid"]["command"] == "python"

    def test_skips_int_server_entry(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Integer server entry is skipped with a warning."""
        path = self._write_config(
            tmp_path,
            {
                "mcpServers": {
                    "number": 42,
                    "ok": {"command": "node"},
                }
            },
        )
        with caplog.at_level(logging.WARNING):
            result = _load_mcp_server_config(path)

        assert "number" not in result
        assert "ok" in result

    def test_all_non_dict_entries_returns_empty(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Config with only non-dict entries returns empty dict."""
        path = self._write_config(
            tmp_path,
            {
                "mcpServers": {
                    "a": "string",
                    "b": 123,
                    "c": None,
                }
            },
        )
        with caplog.at_level(logging.WARNING):
            result = _load_mcp_server_config(path)

        assert result == {}


# ---------------------------------------------------------------------------
# 3. execution_dir / env_vars forwarding through _ask_agent -> run_agent
# ---------------------------------------------------------------------------


class TestExecutionDirEnvVarsForwarding:
    """Verify execution_dir and env_vars are forwarded to run_agent."""

    @staticmethod
    def _make_config() -> dict[str, str | None]:
        return {
            "provider": "langchain",
            "backend": "openai",
            "model": "gpt-4o",
            "api_key": None,
            "endpoint": None,
            "api_version": None,
        }

    def test_env_vars_forwarded_to_run_agent(self) -> None:
        """env_vars parameter is passed through to run_agent."""
        mock_run_agent = AsyncMock(
            return_value=(
                "answer",
                [{"type": "ai", "content": "answer"}],
                {"agent_steps": 1, "total_tool_calls": 0, "tool_trace": []},
            )
        )
        env = {"MY_VAR": "my_value", "OTHER": "other_value"}

        with (
            patch(
                "mcp_coder.llm.providers.langchain._load_langchain_config",
                return_value=self._make_config(),
            ),
            patch(
                "mcp_coder.llm.providers.langchain.agent._check_agent_dependencies",
            ),
            patch(
                "mcp_coder.llm.providers.langchain.agent.run_agent",
                mock_run_agent,
            ),
            patch(
                "mcp_coder.llm.providers.langchain._create_chat_model",
                return_value=MagicMock(),
            ),
            patch(
                "mcp_coder.llm.providers.langchain.load_langchain_history",
                return_value=[],
            ),
            patch("mcp_coder.llm.providers.langchain.store_langchain_history"),
        ):
            from mcp_coder.llm.providers.langchain import ask_langchain

            ask_langchain(
                "question",
                mcp_config="/path/.mcp.json",
                env_vars=env,
            )

        call_kwargs = mock_run_agent.call_args
        assert call_kwargs.kwargs.get("env_vars") == env or (
            len(call_kwargs.args) > 0 and any(v == env for v in call_kwargs.args)
        )

    def test_execution_dir_forwarded_to_run_agent(self) -> None:
        """execution_dir parameter is passed through to run_agent."""
        mock_run_agent = AsyncMock(
            return_value=(
                "answer",
                [{"type": "ai", "content": "answer"}],
                {"agent_steps": 0, "total_tool_calls": 0, "tool_trace": []},
            )
        )

        with (
            patch(
                "mcp_coder.llm.providers.langchain._load_langchain_config",
                return_value=self._make_config(),
            ),
            patch(
                "mcp_coder.llm.providers.langchain.agent._check_agent_dependencies",
            ),
            patch(
                "mcp_coder.llm.providers.langchain.agent.run_agent",
                mock_run_agent,
            ),
            patch(
                "mcp_coder.llm.providers.langchain._create_chat_model",
                return_value=MagicMock(),
            ),
            patch(
                "mcp_coder.llm.providers.langchain.load_langchain_history",
                return_value=[],
            ),
            patch("mcp_coder.llm.providers.langchain.store_langchain_history"),
        ):
            from mcp_coder.llm.providers.langchain import ask_langchain

            ask_langchain(
                "question",
                mcp_config="/path/.mcp.json",
                execution_dir="/my/exec/dir",
            )

        call_kwargs = mock_run_agent.call_args
        assert call_kwargs.kwargs.get("execution_dir") == "/my/exec/dir" or (
            len(call_kwargs.args) > 0
            and any(v == "/my/exec/dir" for v in call_kwargs.args)
        )

    def test_env_vars_none_forwarded(self) -> None:
        """env_vars=None is forwarded without error."""
        mock_run_agent = AsyncMock(
            return_value=(
                "answer",
                [{"type": "ai", "content": "answer"}],
                {"agent_steps": 0, "total_tool_calls": 0, "tool_trace": []},
            )
        )

        with (
            patch(
                "mcp_coder.llm.providers.langchain._load_langchain_config",
                return_value=self._make_config(),
            ),
            patch(
                "mcp_coder.llm.providers.langchain.agent._check_agent_dependencies",
            ),
            patch(
                "mcp_coder.llm.providers.langchain.agent.run_agent",
                mock_run_agent,
            ),
            patch(
                "mcp_coder.llm.providers.langchain._create_chat_model",
                return_value=MagicMock(),
            ),
            patch(
                "mcp_coder.llm.providers.langchain.load_langchain_history",
                return_value=[],
            ),
            patch("mcp_coder.llm.providers.langchain.store_langchain_history"),
        ):
            from mcp_coder.llm.providers.langchain import ask_langchain

            result = ask_langchain(
                "question",
                mcp_config="/path/.mcp.json",
                env_vars=None,
                execution_dir=None,
            )

        assert result["text"] == "answer"
        call_kwargs = mock_run_agent.call_args
        # Both should be None
        assert call_kwargs.kwargs.get("env_vars") is None or (
            "env_vars" not in call_kwargs.kwargs
        )


# ---------------------------------------------------------------------------
# 4. ImportError for all three backends
# ---------------------------------------------------------------------------


class TestBackendImportErrors:
    """Verify each backend raises ImportError with install instructions."""

    def test_openai_backend_import_error(self) -> None:
        """OpenAI backend raises ImportError when langchain_openai is absent."""
        # Remove cached module so re-import triggers the try/except
        modules_to_remove = [
            k
            for k in sys.modules
            if k.startswith("mcp_coder.llm.providers.langchain.openai_backend")
        ]
        saved: dict[str, Any] = {}
        for mod in modules_to_remove:
            saved[mod] = sys.modules.pop(mod)

        # Block reimport by setting to None (raises ImportError)
        saved_lo = sys.modules.pop("langchain_openai", None)

        try:
            sys.modules["langchain_openai"] = None  # type: ignore[assignment]
            with pytest.raises(ImportError, match="pip install"):
                import importlib

                importlib.import_module(
                    "mcp_coder.llm.providers.langchain.openai_backend"
                )
        finally:
            if saved_lo is not None:
                sys.modules["langchain_openai"] = saved_lo
            else:
                sys.modules.pop("langchain_openai", None)
            for mod, val in saved.items():
                sys.modules[mod] = val

    def test_anthropic_backend_import_error(self) -> None:
        """Anthropic backend raises ImportError when langchain_anthropic absent."""
        modules_to_remove = [
            k
            for k in sys.modules
            if k.startswith("mcp_coder.llm.providers.langchain.anthropic_backend")
        ]
        saved: dict[str, Any] = {}
        for mod in modules_to_remove:
            saved[mod] = sys.modules.pop(mod)

        saved_la = sys.modules.pop("langchain_anthropic", None)

        try:
            sys.modules["langchain_anthropic"] = None  # type: ignore[assignment]
            with pytest.raises(ImportError, match="pip install"):
                import importlib

                importlib.import_module(
                    "mcp_coder.llm.providers.langchain.anthropic_backend"
                )
        finally:
            if saved_la is not None:
                sys.modules["langchain_anthropic"] = saved_la
            else:
                sys.modules.pop("langchain_anthropic", None)
            for mod, val in saved.items():
                sys.modules[mod] = val

    def test_gemini_backend_import_error(self) -> None:
        """Gemini backend raises ImportError when langchain_google_genai absent."""
        modules_to_remove = [
            k
            for k in sys.modules
            if k.startswith("mcp_coder.llm.providers.langchain.gemini_backend")
        ]
        saved: dict[str, Any] = {}
        for mod in modules_to_remove:
            saved[mod] = sys.modules.pop(mod)

        saved_lg = sys.modules.pop("langchain_google_genai", None)

        try:
            sys.modules["langchain_google_genai"] = None  # type: ignore[assignment]
            with pytest.raises(ImportError, match="pip install"):
                import importlib

                importlib.import_module(
                    "mcp_coder.llm.providers.langchain.gemini_backend"
                )
        finally:
            if saved_lg is not None:
                sys.modules["langchain_google_genai"] = saved_lg
            else:
                sys.modules.pop("langchain_google_genai", None)
            for mod, val in saved.items():
                sys.modules[mod] = val

    def test_openai_import_error_message_mentions_langchain(self) -> None:
        """OpenAI ImportError message references mcp-coder[langchain] extra."""
        modules_to_remove = [
            k
            for k in sys.modules
            if k.startswith("mcp_coder.llm.providers.langchain.openai_backend")
        ]
        saved: dict[str, Any] = {}
        for mod in modules_to_remove:
            saved[mod] = sys.modules.pop(mod)

        saved_lo = sys.modules.pop("langchain_openai", None)

        try:
            sys.modules["langchain_openai"] = None  # type: ignore[assignment]
            with pytest.raises(ImportError, match=r"mcp-coder\[langchain\]"):
                import importlib

                importlib.import_module(
                    "mcp_coder.llm.providers.langchain.openai_backend"
                )
        finally:
            if saved_lo is not None:
                sys.modules["langchain_openai"] = saved_lo
            else:
                sys.modules.pop("langchain_openai", None)
            for mod, val in saved.items():
                sys.modules[mod] = val
