#!/usr/bin/env python3
"""Tests for the verify CLI command integration."""

import argparse
import sys
from contextlib import ExitStack
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.cli.commands.verify import (
    _looks_like_key,
    _print_environment_section,
    _prompt_source,
    execute_verify,
)
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


class TestEnvironmentSection:
    """Tests for the _print_environment_section helper."""

    def test_section_header_present(self, capsys: pytest.CaptureFixture[str]) -> None:
        _print_environment_section()
        assert "=== ENVIRONMENT" in capsys.readouterr().out

    def test_python_version_row(self, capsys: pytest.CaptureFixture[str]) -> None:
        _print_environment_section()
        out = capsys.readouterr().out
        assert "Python version" in out
        assert f"{sys.version_info.major}.{sys.version_info.minor}" in out

    def test_pythonpath_not_set_when_missing(
        self,
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.delenv("PYTHONPATH", raising=False)
        _print_environment_section()
        assert "(not set)" in capsys.readouterr().out

    def test_missing_package_shows_err_not_installed(
        self,
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        from importlib.metadata import PackageNotFoundError

        def fake_version(pkg: str) -> str:
            if pkg == "mcp-tools-py":
                raise PackageNotFoundError(pkg)
            return "1.2.3"

        monkeypatch.setattr("mcp_coder.cli.commands.verify.version", fake_version)
        _print_environment_section()
        assert "[ERR] not installed" in capsys.readouterr().out

    def test_virtualenv_none_when_not_in_venv(
        self,
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(sys, "prefix", "/usr")
        monkeypatch.setattr(sys, "base_prefix", "/usr")
        _print_environment_section()
        assert "(none)" in capsys.readouterr().out


class TestLooksLikeKey:
    """Tests for the _looks_like_key helper."""

    def test_simple_identifier_matches(self) -> None:
        assert _looks_like_key("token") is True

    def test_underscores_and_digits_match(self) -> None:
        assert _looks_like_key("cache_refresh_minutes") is True
        assert _looks_like_key("server_url") is True
        assert _looks_like_key("_private") is True
        assert _looks_like_key("x2") is True

    def test_starts_with_digit_fails(self) -> None:
        assert _looks_like_key("6") is False
        assert _looks_like_key("123abc") is False

    def test_starts_with_bracket_fails(self) -> None:
        assert _looks_like_key("[OK]") is False
        assert _looks_like_key("[ERR]") is False

    def test_python_keyword_fails(self) -> None:
        # "not configured" should not be rendered as a key column
        assert _looks_like_key("not") is False

    def test_empty_fails(self) -> None:
        assert _looks_like_key("") is False

    def test_contains_space_or_dash_fails(self) -> None:
        # partition returns the first token; but defensively ensure dashes fail
        assert _looks_like_key("server-url") is False


def _run_verify_with_entries(
    entries: list[dict[str, str]],
    capsys: pytest.CaptureFixture[str],
) -> str:
    """Execute execute_verify with entries; return captured stdout."""
    mocks = [
        patch(
            f"{_VERIFY}.verify_config",
            return_value={"entries": entries, "has_error": False},
        ),
        patch(
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
        ),
        patch(f"{_VERIFY}.resolve_llm_method", return_value=("claude", "default")),
        patch(f"{_VERIFY}.verify_claude", return_value=_claude_ok()),
        patch(f"{_VERIFY}.find_claude_executable", return_value=None),
        patch(f"{_VERIFY}.resolve_mcp_config_path", return_value=None),
        patch(f"{_VERIFY}.prompt_llm", return_value=_minimal_llm_response()),
        patch(f"{_VERIFY}.verify_mlflow", return_value={"overall_ok": True}),
    ]
    with ExitStack() as stack:
        for m in mocks:
            stack.enter_context(m)
        execute_verify(_make_args())
    return capsys.readouterr().out


def _config_block(output: str) -> list[str]:
    """Return the lines between '=== CONFIG' and the next header or EOF."""
    lines = output.splitlines()
    start = next(i for i, line in enumerate(lines) if "=== CONFIG" in line)
    end = len(lines)
    for i in range(start + 1, len(lines)):
        if lines[i].startswith("=== "):
            end = i
            break
    return lines[start:end]


class TestConfigGrouping:
    """Tests for TOML-style [section] grouping in the CONFIG section."""

    def _entries(self) -> list[dict[str, str]]:
        return [
            {"label": "Config file", "status": "ok", "value": "/path/config.toml"},
            {
                "label": "[github]",
                "status": "ok",
                "value": "token configured (config.toml)",
            },
            {
                "label": "[github]",
                "status": "ok",
                "value": "test_repo_url configured (config.toml)",
            },
            {
                "label": "[jenkins]",
                "status": "ok",
                "value": "server_url configured (config.toml)",
            },
        ]

    def test_section_header_emitted_once(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Each [section] header appears only once per group."""
        out = _run_verify_with_entries(self._entries(), capsys)
        block = "\n".join(_config_block(out))
        assert block.count("[github]") == 1
        assert block.count("[jenkins]") == 1

    def test_items_indented_under_section(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Items appear indented (4 spaces) under their section header."""
        out = _run_verify_with_entries(self._entries(), capsys)
        lines = _config_block(out)
        assert any(line.startswith("    token") for line in lines)
        assert any(line.startswith("    test_repo_url") for line in lines)
        assert any(line.startswith("    server_url") for line in lines)

    def test_blank_line_between_sections(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """A blank line appears between the [github] group and [jenkins] group."""
        out = _run_verify_with_entries(self._entries(), capsys)
        lines = _config_block(out)
        jenkins_idx = next(i for i, line in enumerate(lines) if "[jenkins]" in line)
        # Line immediately before "  [jenkins]" must be empty
        assert lines[jenkins_idx - 1] == ""

    def test_key_extracted_from_value(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Key is extracted (no '... configured (config.toml)' after the key column)."""
        out = _run_verify_with_entries(self._entries(), capsys)
        lines = _config_block(out)
        token_line = next(line for line in lines if line.startswith("    token"))
        # The line should show: "    token              [OK] configured (config.toml)"
        # The key column stops before configured
        assert "token" in token_line
        # Key column is padded to 18 chars, then the symbol, then the rest
        assert "[OK] configured (config.toml)" in token_line

    def test_config_file_row_outside_groups(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """The 'Config file' row appears as a top-level row, not under a [...] header."""
        out = _run_verify_with_entries(self._entries(), capsys)
        lines = _config_block(out)
        config_idx = next(i for i, line in enumerate(lines) if "Config file" in line)
        github_idx = next(i for i, line in enumerate(lines) if "[github]" in line)
        assert config_idx < github_idx
        # Config file row is 2-space indented (top-level), not 4-space (group item)
        assert lines[config_idx].startswith("  Config file")
        assert not lines[config_idx].startswith("    ")

    def test_info_entry_renders_without_key_split(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """[mcp] + 'not configured' renders as indented line, no nonsensical key split."""
        entries = [
            {"label": "[mcp]", "status": "warning", "value": "not configured"},
        ]
        out = _run_verify_with_entries(entries, capsys)
        block = "\n".join(_config_block(out))
        # Header present once, then an indented line containing the full "not configured"
        assert "[mcp]" in block
        # No split like "not                [WARN] configured"
        assert "not                " not in block
        # "not configured" must still appear together on the indented line
        lines = _config_block(out)
        assert any(
            "not configured" in line and line.startswith("    ") for line in lines
        )

    def test_summary_entry_with_status_prefix_renders_plain(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """[coordinator] + '6 repos configured' renders as a single indented row.

        The real producer in ``user_config.verify_coordinator_config`` emits
        ``value = "6 repos configured"`` (no ``[OK]`` prefix); the renderer
        prepends the ``[OK]`` status symbol itself. The fixture mirrors that
        contract so the assertion proves the rendered line has exactly one
        ``[OK]`` (not a doubled prefix).
        """
        entries = [
            {
                "label": "[coordinator]",
                "status": "ok",
                "value": "6 repos configured",
            },
        ]
        out = _run_verify_with_entries(entries, capsys)
        lines = _config_block(out)
        # Must contain the exact indented line with a single [OK] status symbol
        assert "    [OK] 6 repos configured" in lines
        # Must not be split at "6" (i.e., no "[OK]              <symbol> 6 repos")
        assert not any(line.startswith("    [OK]              ") for line in lines)
        # Must not double the [OK] prefix
        assert not any("[OK] [OK]" in line for line in lines)
