"""Tests for filling toolkit slots in the injected system and project prompts."""

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.llm.interface import prompt_llm, prompt_llm_stream
from mcp_coder.utils import prompt_slots
from mcp_coder.utils.pyproject_config import PromptsConfig

_RESPONSE = {
    "text": "Response",
    "session_id": "test-session",
    "version": "1.0",
    "timestamp": "2025-10-01T10:30:00",
    "provider": "claude",
    "raw_response": {},
}

_COMMAND_CHECKS = "Run `make check` and fix everything it reports."
_PY_CHECKS = "Use the fake check tool and fix all issues."
_PY_CONTEXT = "This is a fake-language project."


class _FakeToolkit:
    """Toolkit stand-in exposing only prompt_fragments()."""

    def __init__(self, fragments: dict[str, str]) -> None:
        self._fragments = fragments

    def prompt_fragments(self) -> dict[str, str]:
        return self._fragments


def _patch_toolkit(
    monkeypatch: pytest.MonkeyPatch,
    fragments: dict[str, str],
    permissions: list[str],
) -> MagicMock:
    """Patch the toolkit seen by prompt_slots; return the load_toolkit mock."""
    loaded = MagicMock()
    loaded.toolkit = _FakeToolkit(fragments)
    load = MagicMock(return_value=loaded)
    monkeypatch.setattr(prompt_slots, "load_toolkit", load)

    def fake_permissions(*_args: Any, **_kwargs: Any) -> list[str]:
        return permissions

    monkeypatch.setattr(prompt_slots, "llm_permissions", fake_permissions)
    return load


def _command_toolkit(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    return _patch_toolkit(
        monkeypatch,
        {"language_context": "", "check_instructions": _COMMAND_CHECKS},
        ["Bash(make check:*)"],
    )


def _python_toolkit(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    return _patch_toolkit(
        monkeypatch,
        {"language_context": _PY_CONTEXT, "check_instructions": _PY_CHECKS},
        ["mcp__fake-tools__run_check"],
    )


def _sent_prompt(mock_ask: MagicMock) -> str:
    """Return the append_system_prompt the Claude provider received."""
    _, kwargs = mock_ask.call_args
    prompt = kwargs["append_system_prompt"]
    assert isinstance(prompt, str)
    return prompt


class TestPromptLlmFillsInjectedPrompts:
    """prompt_llm fills slots in the injected prompts."""

    @patch("mcp_coder.prompts.prompt_loader.load_prompts")
    @patch("mcp_coder.llm.interface.ask_claude_code_cli")
    def test_slot_free_custom_prompts_unchanged(
        self,
        mock_ask: MagicMock,
        mock_load_prompts: MagicMock,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        load = _command_toolkit(monkeypatch)
        mock_load_prompts.return_value = (
            "custom system",
            "custom project",
            PromptsConfig(
                system_prompt=None,
                project_prompt=None,
                claude_system_prompt_mode="append",
            ),
        )
        mock_ask.return_value = _RESPONSE

        prompt_llm("Q", project_dir=tmp_path, inject_prompts=True)

        load.assert_not_called()
        assert _sent_prompt(mock_ask) == (
            "## System Prompt\n\ncustom system\n\n## Project Prompt\n\ncustom project"
        )

    @patch("mcp_coder.llm.interface.ask_claude_code_cli")
    def test_bash_toolkit_without_grants_drops_check_line(
        self,
        mock_ask: MagicMock,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        _command_toolkit(monkeypatch)
        mock_ask.return_value = _RESPONSE

        prompt_llm("Q", project_dir=tmp_path, provider="claude", inject_prompts=True)

        sent = _sent_prompt(mock_ask)
        assert "[check_instructions]" not in sent
        assert "[language_context]" not in sent
        assert _COMMAND_CHECKS not in sent
        assert "No security vulnerabilities should be introduced" in sent

    @patch("mcp_coder.llm.interface.ask_claude_code_cli")
    def test_bash_toolkit_claude_with_grants_inserts_checks(
        self,
        mock_ask: MagicMock,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        _command_toolkit(monkeypatch)
        mock_ask.return_value = _RESPONSE

        prompt_llm(
            "Q",
            project_dir=tmp_path,
            provider="claude",
            inject_prompts=True,
            bash_grants=["Bash(make check:*)"],
        )

        sent = _sent_prompt(mock_ask)
        assert _COMMAND_CHECKS in sent
        assert "[check_instructions]" not in sent

    @patch("mcp_coder.llm.interface.ask_claude_code_cli")
    def test_mcp_toolkit_fragments_inserted(
        self,
        mock_ask: MagicMock,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        _python_toolkit(monkeypatch)
        mock_ask.return_value = _RESPONSE

        prompt_llm("Q", project_dir=tmp_path, provider="claude", inject_prompts=True)

        sent = _sent_prompt(mock_ask)
        assert _PY_CHECKS in sent
        assert _PY_CONTEXT in sent
        assert "[check_instructions]" not in sent
        assert "[language_context]" not in sent


class TestPromptLlmStreamFillsInjectedPrompts:
    """prompt_llm_stream fills slots in the injected prompts."""

    @patch(
        "mcp_coder.llm.providers.claude.claude_code_cli_streaming.ask_claude_code_cli_stream"
    )
    def test_mcp_toolkit_fragments_inserted(
        self,
        mock_stream: MagicMock,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        _python_toolkit(monkeypatch)
        mock_stream.return_value = iter([{"type": "done", "usage": {}}])

        list(
            prompt_llm_stream(
                "Q", project_dir=tmp_path, provider="claude", inject_prompts=True
            )
        )

        sent = _sent_prompt(mock_stream)
        assert _PY_CHECKS in sent
        assert _PY_CONTEXT in sent
        assert "[check_instructions]" not in sent
