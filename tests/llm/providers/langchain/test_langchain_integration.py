"""Integration tests for mcp_coder.llm.providers.langchain.

These tests send real API requests to the configured backend.
They are skipped automatically when no credentials are configured.

Run with:
    pytest tests/llm/providers/langchain/test_langchain_integration.py \
           -m langchain_integration -v -s

For CI secrets configuration see .github/workflows/langchain-integration.yml.
Config can be provided via config.toml or MCP_CODER_LLM_LANGCHAIN_* env vars.
"""

import importlib.util
import json
import os
import sys
from pathlib import Path

import pytest

from mcp_coder.llm.providers.langchain import _load_langchain_config

pytestmark = pytest.mark.langchain_integration


def _require_langchain_config() -> None:
    """Skip the test if LangChain is not configured with valid credentials."""
    try:
        spec = importlib.util.find_spec("langchain_core")
    except (ValueError, ModuleNotFoundError):
        spec = None
    if spec is None:
        pytest.skip("langchain-core not installed")
    try:
        cfg = _load_langchain_config()
    except Exception as exc:  # pylint: disable=broad-except
        pytest.skip(f"Could not load langchain config: {exc}")

    if not cfg.get("backend"):
        pytest.skip("llm.langchain.backend not set in config.toml")
    if not cfg.get("model"):
        pytest.skip("llm.langchain.model not set in config.toml")

    backend = cfg["backend"]
    if backend == "openai":
        if not os.getenv("OPENAI_API_KEY") and not cfg.get("api_key"):
            pytest.skip(
                "No OpenAI credentials: set OPENAI_API_KEY or [llm.langchain] api_key"
            )
    elif backend == "gemini":
        if not os.getenv("GEMINI_API_KEY") and not cfg.get("api_key"):
            pytest.skip(
                "No Gemini credentials: set GEMINI_API_KEY or [llm.langchain] api_key"
            )
    elif backend == "anthropic":
        if not os.getenv("ANTHROPIC_API_KEY") and not cfg.get("api_key"):
            pytest.skip(
                "No Anthropic credentials: set ANTHROPIC_API_KEY "
                "or [llm.langchain] api_key"
            )


class TestLangchainIntegration:
    """Real API integration tests. Skipped unless [llm.langchain] is configured."""

    def test_ask_langchain_returns_valid_response(self) -> None:
        """ask_langchain sends a real question and returns a valid LLMResponseDict."""
        _require_langchain_config()
        from mcp_coder.llm.providers.langchain import ask_langchain

        result = ask_langchain("Reply with exactly the word: hello")

        assert result["provider"] == "langchain"
        assert isinstance(result["text"], str)
        assert len(result["text"].strip()) > 0
        assert result["session_id"] is not None
        assert "raw_response" in result

    def test_session_continuity(self) -> None:
        """Second call with session_id remembers context from the first call."""
        _require_langchain_config()
        from mcp_coder.llm.providers.langchain import ask_langchain

        result1 = ask_langchain("My favourite colour is purple. Acknowledge with OK.")
        session_id = result1["session_id"]

        result2 = ask_langchain(
            "What colour did I just mention?", session_id=session_id
        )
        assert "purple" in result2["text"].lower()
        assert result2["session_id"] == session_id


# ---------------------------------------------------------------------------
# Agent mode integration tests (mirrors tools/test_prompt.bat)
# ---------------------------------------------------------------------------


def _find_mcp_workspace() -> str:
    """Return the path to mcp-workspace, or skip if not installed."""
    venv_scripts = Path(sys.executable).parent
    for name in ("mcp-workspace.exe", "mcp-workspace"):
        candidate = venv_scripts / name
        if candidate.exists():
            return str(candidate)
    pytest.skip("mcp-workspace not installed in venv")
    return ""  # unreachable, keeps mypy happy


def _create_agent_mcp_config(tmp_path: Path) -> tuple[str, Path]:
    """Create a temp .mcp.json with the filesystem server.

    Returns ``(config_path, project_dir)`` where *project_dir* is the
    directory the filesystem server manages (for file-write assertions).
    """
    fs_server = _find_mcp_workspace()
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    config = {
        "mcpServers": {
            "filesystem": {
                "command": fs_server,
                "args": [
                    "--project-dir",
                    str(project_dir),
                    "--log-level",
                    "INFO",
                ],
            }
        }
    }
    config_path = tmp_path / ".mcp.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")
    return str(config_path), project_dir


class TestAgentModeIntegration:
    """End-to-end agent mode tests with real MCP servers and LLM API.

    Mirrors the manual tests in ``tools/test_prompt.bat``.
    Skipped when credentials or MCP server are unavailable.
    """

    def test_agent_simple_prompt(self, tmp_path: Path) -> None:
        """Agent answers a simple math question."""
        _require_langchain_config()
        from mcp_coder.llm.providers.langchain import ask_langchain

        mcp_config, _ = _create_agent_mcp_config(tmp_path)

        result = ask_langchain(
            "What is 1 + 1? Reply with just the number.",
            mcp_config=mcp_config,
            timeout=60,
        )

        assert result["provider"] == "langchain"
        assert "2" in result["text"]
        assert result["session_id"] is not None

    def test_agent_session_continuity(self, tmp_path: Path) -> None:
        """Agent remembers context across continued session."""
        _require_langchain_config()
        from mcp_coder.llm.providers.langchain import ask_langchain

        mcp_config, _ = _create_agent_mcp_config(tmp_path)

        result1 = ask_langchain(
            "What is 1 + 1? Reply with just the number.",
            mcp_config=mcp_config,
            timeout=60,
        )
        session_id = result1["session_id"]

        result2 = ask_langchain(
            "Multiply the result by two. Reply with just the number.",
            session_id=session_id,
            mcp_config=mcp_config,
            timeout=60,
        )

        assert "4" in result2["text"]
        assert result2["session_id"] == session_id

    def test_agent_mcp_tool_discovery(self, tmp_path: Path) -> None:
        """Agent can list the MCP tools available to it."""
        _require_langchain_config()
        from mcp_coder.llm.providers.langchain import ask_langchain

        mcp_config, _ = _create_agent_mcp_config(tmp_path)

        result = ask_langchain(
            "List the tools you have available. Be brief.",
            mcp_config=mcp_config,
            timeout=60,
        )

        text_lower = result["text"].lower()
        # The filesystem server exposes these tools
        assert "read_file" in text_lower or "read" in text_lower
        assert (
            "save_file" in text_lower or "save" in text_lower or "write" in text_lower
        )

    def test_agent_file_write_via_mcp(self, tmp_path: Path) -> None:
        """Agent creates a file using the MCP filesystem tool."""
        _require_langchain_config()
        from mcp_coder.llm.providers.langchain import ask_langchain

        mcp_config, project_dir = _create_agent_mcp_config(tmp_path)

        ask_langchain(
            "Create a file called test.md with the content: Hello World",
            mcp_config=mcp_config,
            timeout=120,
        )

        created_file = project_dir / "test.md"
        assert created_file.exists(), "test.md was not created by the agent"
        content = created_file.read_text(encoding="utf-8")
        assert "Hello World" in content
