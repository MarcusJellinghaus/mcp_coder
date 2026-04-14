#!/usr/bin/env python3
"""Tests for the verify CLI command integration."""

import argparse
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.cli.commands.verify import _prompt_source, execute_verify
from mcp_coder.cli.main import main
from mcp_coder.utils.pyproject_config import PromptsConfig


class TestVerifyCommandIntegration:
    """Test the verify command CLI integration."""

    @patch("mcp_coder.cli.main.execute_verify")
    @patch("sys.argv", ["mcp-coder", "verify"])
    def test_verify_command_calls_verification_function(
        self, mock_verify: MagicMock
    ) -> None:
        """Test that the verify CLI command calls the verification function."""
        mock_verify.return_value = 0  # Success

        result = main()

        assert result == 0
        mock_verify.assert_called_once()

        # Check that the function was called with proper arguments
        call_args = mock_verify.call_args[0][0]  # First positional argument (args)
        assert isinstance(call_args, argparse.Namespace)

    @patch("mcp_coder.cli.main.execute_verify")
    @patch("sys.argv", ["mcp-coder", "verify"])
    def test_verify_command_propagates_return_code(
        self, mock_verify: MagicMock
    ) -> None:
        """Test that the verify CLI command propagates the return code from verification."""
        mock_verify.return_value = 1  # Error

        result = main()

        assert result == 1
        mock_verify.assert_called_once()


# ── Prompt section tests ────────────────────────────────────────────

_VERIFY = "mcp_coder.cli.commands.verify"


def _make_args(**kwargs: Any) -> argparse.Namespace:
    """Create a Namespace with defaults for execute_verify."""
    defaults: dict[str, Any] = {
        "check_models": False,
        "mcp_config": None,
        "llm_method": None,
        "project_dir": None,
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def _minimal_llm_response() -> dict[str, Any]:
    return {
        "version": "1.0",
        "timestamp": "2026-01-01T00:00:00",
        "text": "OK",
        "session_id": None,
        "provider": "claude",
        "raw_response": {},
    }


def _claude_ok() -> dict[str, Any]:
    return {
        "cli_found": {"ok": True, "value": "YES"},
        "cli_works": {"ok": True, "value": "YES"},
        "api_integration": {"ok": True, "value": "OK", "error": None},
        "overall_ok": True,
    }


class TestPromptSource:
    """Tests for the _prompt_source helper."""

    def test_configured_path_returned(self) -> None:
        assert (
            _prompt_source("prompts/system.md", "shipped default")
            == "prompts/system.md"
        )

    def test_none_returns_default_label(self) -> None:
        assert _prompt_source(None, "shipped default") == "(shipped default)"


class TestVerifyShowsPromptSection:
    """Tests for the PROMPTS section in verify output."""

    @patch(f"{_VERIFY}.verify_mlflow", return_value={"overall_ok": True})
    @patch(f"{_VERIFY}.prompt_llm", return_value=_minimal_llm_response())
    @patch(f"{_VERIFY}.find_claude_executable", return_value=None)
    @patch(f"{_VERIFY}.verify_claude", return_value=_claude_ok())
    @patch(f"{_VERIFY}.verify_config", return_value={"entries": [], "has_error": False})
    @patch(f"{_VERIFY}.resolve_llm_method", return_value=("claude", "default"))
    @patch(
        f"{_VERIFY}.load_prompts",
        return_value=(
            "sys content",
            "proj content",
            PromptsConfig(
                system_prompt=None,
                project_prompt=None,
                claude_system_prompt_mode="append",
            ),
        ),
    )
    def test_verify_shows_prompt_section_defaults(
        self,
        _mock_load: MagicMock,
        _mock_resolve: MagicMock,
        _mock_config: MagicMock,
        _mock_claude: MagicMock,
        _mock_find: MagicMock,
        _mock_prompt: MagicMock,
        _mock_mlflow: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """When no custom config, shows '(shipped default)'."""
        execute_verify(_make_args())
        output = capsys.readouterr().out
        assert "=== PROMPTS ===" in output
        assert "(shipped default)" in output
        assert "append" in output

    @patch(f"{_VERIFY}.verify_mlflow", return_value={"overall_ok": True})
    @patch(f"{_VERIFY}.prompt_llm", return_value=_minimal_llm_response())
    @patch(f"{_VERIFY}.find_claude_executable", return_value=None)
    @patch(f"{_VERIFY}.verify_claude", return_value=_claude_ok())
    @patch(f"{_VERIFY}.verify_config", return_value={"entries": [], "has_error": False})
    @patch(f"{_VERIFY}.resolve_llm_method", return_value=("claude", "default"))
    @patch(
        f"{_VERIFY}.load_prompts",
        return_value=(
            "sys content",
            "proj content",
            PromptsConfig(
                system_prompt="prompts/system.md",
                project_prompt="prompts/project.md",
                claude_system_prompt_mode="replace",
            ),
        ),
    )
    def test_verify_shows_custom_prompt_paths(
        self,
        _mock_load: MagicMock,
        _mock_resolve: MagicMock,
        _mock_config: MagicMock,
        _mock_claude: MagicMock,
        _mock_find: MagicMock,
        _mock_prompt: MagicMock,
        _mock_mlflow: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """When custom config is provided, shows the configured paths."""
        execute_verify(_make_args())
        output = capsys.readouterr().out
        assert "prompts/system.md" in output
        assert "prompts/project.md" in output
        assert "replace" in output

    @patch(f"{_VERIFY}.verify_mlflow", return_value={"overall_ok": True})
    @patch(f"{_VERIFY}.prompt_llm", return_value=_minimal_llm_response())
    @patch(f"{_VERIFY}.find_claude_executable", return_value=None)
    @patch(f"{_VERIFY}.verify_claude", return_value=_claude_ok())
    @patch(f"{_VERIFY}.verify_config", return_value={"entries": [], "has_error": False})
    @patch(f"{_VERIFY}.resolve_llm_method", return_value=("claude", "default"))
    @patch(f"{_VERIFY}.is_claude_md", return_value=True)
    @patch(f"{_VERIFY}.get_project_prompt_path", return_value="some/path")
    @patch(
        f"{_VERIFY}.load_prompts",
        return_value=(
            "sys content",
            "proj content",
            PromptsConfig(
                system_prompt=None,
                project_prompt=".claude/CLAUDE.md",
                claude_system_prompt_mode="append",
            ),
        ),
    )
    def test_verify_shows_redundancy_warning(
        self,
        _mock_load: MagicMock,
        _mock_path: MagicMock,
        _mock_is_claude: MagicMock,
        _mock_resolve: MagicMock,
        _mock_config: MagicMock,
        _mock_claude: MagicMock,
        _mock_find: MagicMock,
        _mock_prompt: MagicMock,
        _mock_mlflow: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """When project prompt is CLAUDE.md and provider is claude, show redundancy warning."""
        execute_verify(_make_args())
        output = capsys.readouterr().out
        assert "Redundancy" in output
        assert "CLAUDE.md" in output
