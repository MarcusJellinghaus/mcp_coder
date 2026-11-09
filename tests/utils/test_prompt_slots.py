"""Tests for prompt slot resolution and filling."""

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

from mcp_coder.utils import prompt_slots
from mcp_coder.utils.prompt_slots import (
    DEFAULT_CHECK_INSTRUCTIONS,
    DEFAULT_LANGUAGE_CONTEXT,
    fill_prompt,
    resolve_prompt_slots,
    toolkit_declares_bash_grants,
)

BOTH_SLOTS = "Intro\n[language_context]\nBody\n[check_instructions]\n"


class _FakeToolkit:
    """Toolkit stand-in exposing only prompt_fragments()."""

    def __init__(self, fragments: dict[str, str] | Exception) -> None:
        self._fragments = fragments

    def prompt_fragments(self) -> dict[str, str]:
        if isinstance(self._fragments, Exception):
            raise self._fragments
        return self._fragments


def _patch(
    monkeypatch: pytest.MonkeyPatch,
    fragments: dict[str, str] | Exception,
    permissions: list[str] | Exception | None = None,
) -> MagicMock:
    """Patch load_toolkit and llm_permissions; return the load_toolkit mock."""
    loaded = MagicMock()
    loaded.toolkit = _FakeToolkit(fragments)
    load = MagicMock(return_value=loaded)
    monkeypatch.setattr(prompt_slots, "load_toolkit", load)

    def fake_permissions(*_args: Any, **_kwargs: Any) -> list[str]:
        if isinstance(permissions, Exception):
            raise permissions
        return permissions or []

    monkeypatch.setattr(prompt_slots, "llm_permissions", fake_permissions)
    return load


class TestToolkitDeclaresBashGrants:
    """Tests for toolkit_declares_bash_grants."""

    def test_bash_grants_declared(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        _patch(monkeypatch, {}, ["mcp__x__y", "Bash(make:*)"])
        assert toolkit_declares_bash_grants(tmp_path) is True

    def test_mcp_grants_only(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        _patch(monkeypatch, {}, ["mcp__x__y"])
        assert toolkit_declares_bash_grants(tmp_path) is False

    def test_reads_claude_grants(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        calls: list[tuple[Any, ...]] = []

        def fake_permissions(*args: Any) -> list[str]:
            calls.append(args)
            return []

        monkeypatch.setattr(prompt_slots, "llm_permissions", fake_permissions)
        toolkit_declares_bash_grants(tmp_path)
        assert calls == [(tmp_path, "claude")]


class TestResolvePromptSlots:
    """Tests for resolve_prompt_slots."""

    def test_no_slot_returns_empty_without_loading(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        load = _patch(monkeypatch, {"check_instructions": "x"})
        assert resolve_prompt_slots("no slots here", tmp_path, None, None) == {}
        load.assert_not_called()

    def test_only_present_slots_returned(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        _patch(monkeypatch, {"language_context": "Py", "check_instructions": "x"})
        result = resolve_prompt_slots("[language_context]", tmp_path, None, None)
        assert result == {"language_context": "Py"}

    def test_non_empty_fragment_inserted(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        _patch(
            monkeypatch,
            {"language_context": "Python project", "check_instructions": "Run X"},
        )
        result = resolve_prompt_slots(BOTH_SLOTS, tmp_path, "claude", None)
        assert result == {
            "language_context": "Python project",
            "check_instructions": "Run X",
        }

    def test_empty_fragment_kept_empty(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        _patch(monkeypatch, {"language_context": "", "check_instructions": ""})
        result = resolve_prompt_slots(BOTH_SLOTS, tmp_path, "claude", None)
        assert result == {"language_context": "", "check_instructions": ""}

    def test_missing_fragment_uses_default(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        _patch(monkeypatch, {})
        result = resolve_prompt_slots(BOTH_SLOTS, tmp_path, "claude", None)
        assert result == {
            "language_context": DEFAULT_LANGUAGE_CONTEXT,
            "check_instructions": DEFAULT_CHECK_INSTRUCTIONS,
        }

    def test_load_toolkit_error_uses_defaults(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        load = _patch(monkeypatch, {"check_instructions": "x"})
        load.side_effect = ValueError("bad config")
        result = resolve_prompt_slots(BOTH_SLOTS, tmp_path, "claude", None)
        assert result == {
            "language_context": DEFAULT_LANGUAGE_CONTEXT,
            "check_instructions": DEFAULT_CHECK_INSTRUCTIONS,
        }

    def test_prompt_fragments_error_uses_defaults(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        _patch(monkeypatch, RuntimeError("boom"))
        result = resolve_prompt_slots(BOTH_SLOTS, tmp_path, "claude", None)
        assert result == {
            "language_context": DEFAULT_LANGUAGE_CONTEXT,
            "check_instructions": DEFAULT_CHECK_INSTRUCTIONS,
        }

    def test_llm_permissions_error_uses_defaults(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        _patch(
            monkeypatch,
            {"language_context": "Py", "check_instructions": "x"},
            RuntimeError("boom"),
        )
        result = resolve_prompt_slots(BOTH_SLOTS, tmp_path, "claude", None)
        assert result == {
            "language_context": DEFAULT_LANGUAGE_CONTEXT,
            "check_instructions": DEFAULT_CHECK_INSTRUCTIONS,
        }

    def test_bash_toolkit_non_claude_provider_empties_checks(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        _patch(monkeypatch, {"check_instructions": "Run make"}, ["Bash(make:*)"])
        result = resolve_prompt_slots(
            "[check_instructions]", tmp_path, "copilot", ["Bash(make:*)"]
        )
        assert result == {"check_instructions": ""}

    def test_bash_toolkit_claude_without_grants_empties_checks(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        _patch(monkeypatch, {"check_instructions": "Run make"}, ["Bash(make:*)"])
        result = resolve_prompt_slots("[check_instructions]", tmp_path, "claude", [])
        assert result == {"check_instructions": ""}

    def test_bash_toolkit_claude_with_grants_keeps_fragment(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        _patch(monkeypatch, {"check_instructions": "Run make"}, ["Bash(make:*)"])
        result = resolve_prompt_slots(
            "[check_instructions]", tmp_path, "claude", ["Bash(make:*)"]
        )
        assert result == {"check_instructions": "Run make"}

    def test_non_bash_toolkit_non_claude_keeps_fragment(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        _patch(
            monkeypatch,
            {"check_instructions": "Use run_pylint_check"},
            ["mcp__tools__run_pylint_check"],
        )
        result = resolve_prompt_slots("[check_instructions]", tmp_path, "copilot", [])
        assert result == {"check_instructions": "Use run_pylint_check"}

    def test_provider_none_uses_env(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        _patch(monkeypatch, {"check_instructions": "Run make"}, ["Bash(make:*)"])
        monkeypatch.setenv("MCP_CODER_LLM_PROVIDER", "copilot")
        result = resolve_prompt_slots(
            "[check_instructions]", tmp_path, None, ["Bash(make:*)"]
        )
        assert result == {"check_instructions": ""}

    def test_provider_none_without_env_is_claude(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        _patch(monkeypatch, {"check_instructions": "Run make"}, ["Bash(make:*)"])
        monkeypatch.delenv("MCP_CODER_LLM_PROVIDER", raising=False)
        result = resolve_prompt_slots(
            "[check_instructions]", tmp_path, None, ["Bash(make:*)"]
        )
        assert result == {"check_instructions": "Run make"}


class TestFillPrompt:
    """Tests for fill_prompt."""

    def test_empty_slot_line_removed_and_blank_collapsed(self) -> None:
        template = "A\n\n[check_instructions]\n\nB\n\n\nC"
        result = fill_prompt(template, {}, {"check_instructions": ""})
        assert result == "A\n\nB\n\n\nC"

    def test_empty_slot_line_without_surrounding_blanks(self) -> None:
        template = "A\n[language_context]\nB"
        assert fill_prompt(template, {}, {"language_context": ""}) == "A\nB"

    def test_inline_slot_replaced_in_place(self) -> None:
        template = "Do it. [check_instructions] Done."
        assert (
            fill_prompt(template, {}, {"check_instructions": "Run X."})
            == "Do it. Run X. Done."
        )

    def test_inline_empty_slot_disappears_from_line(self) -> None:
        template = "Do it. [check_instructions]\nNext"
        assert fill_prompt(template, {}, {"check_instructions": ""}) == "Do it. \nNext"

    def test_backslashes_inserted_verbatim(self) -> None:
        value = r"C:\dir \d \1 \\ end"
        assert fill_prompt("x [path] y", {"path": value}, {}) == f"x {value} y"

    def test_substituted_value_not_filled_again(self) -> None:
        result = fill_prompt(
            "[problem_description]\n[check_instructions]",
            {"problem_description": "see [check_instructions]"},
            {"check_instructions": "Run X"},
        )
        assert result == "see [check_instructions]\nRun X"

    def test_fragment_value_not_substituted(self) -> None:
        result = fill_prompt(
            "[check_instructions]",
            {"problem_description": "bug"},
            {"check_instructions": "fix [problem_description]"},
        )
        assert result == "fix [problem_description]"

    def test_checkboxes_and_unknown_placeholders_untouched(self) -> None:
        template = "- [ ] task\n- [x] done\n[unknown] [name]"
        result = fill_prompt(template, {"name": "N"}, {"check_instructions": "x"})
        assert result == "- [ ] task\n- [x] done\n[unknown] N"

    def test_empty_inputs_return_template_unchanged(self) -> None:
        template = "A\n\n\n[check_instructions]\n- [ ] x\n"
        assert fill_prompt(template, {}, {}) == template
