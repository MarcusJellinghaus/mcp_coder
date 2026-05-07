"""Tests for SessionPickerScreen and format_picker_row."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import pytest
from textual.app import App
from textual.widgets import OptionList

from mcp_coder.icoder.core.types import LogSummary
from mcp_coder.icoder.ui.widgets.session_picker import (
    SessionPickerScreen,
    format_picker_row,
)


def _make_summary(
    *,
    path: Path = Path("/tmp/icoder_2026-05-01T10-00-00.jsonl"),
    timestamp: datetime = datetime(2026, 5, 1, 10, 0, 0, tzinfo=timezone.utc),
    provider: Optional[str] = "claude",
    n_turns: int = 3,
    first_prompt: str = "hello world",
) -> LogSummary:
    return LogSummary(
        path=path,
        timestamp=timestamp,
        provider=provider,
        n_turns=n_turns,
        first_prompt=first_prompt,
    )


# --- format_picker_row pure-function tests (no Textual) ---


def test_format_picker_row_typical() -> None:
    summary = _make_summary(
        timestamp=datetime(2026, 5, 1, 14, 30, 0, tzinfo=timezone.utc),
        provider="claude",
        n_turns=5,
        first_prompt="hello world",
    )
    assert format_picker_row(summary) == (
        '2026-05-01 14:30 · claude · 5 turns · "hello world"'
    )


def test_format_picker_row_missing_provider() -> None:
    summary = _make_summary(provider=None)
    row = format_picker_row(summary)
    assert "· ? ·" in row


def test_format_picker_row_eighty_char_prompt_unchanged() -> None:
    eighty = "x" * 80
    summary = _make_summary(first_prompt=eighty)
    row = format_picker_row(summary)
    assert eighty in row
    assert f'"{eighty}"' in row


# --- Modal screen integration tests ---

pytestmark = pytest.mark.textual_integration


class _PickerHostApp(App[None]):
    """Test harness app that pushes SessionPickerScreen and stores its result."""

    def __init__(self, summaries: list[LogSummary]) -> None:
        super().__init__()
        self._summaries = summaries
        self.result: Optional[Path] = None
        self.dismissed = False

    def on_mount(self) -> None:
        def _on_dismiss(value: Optional[Path]) -> None:
            self.result = value
            self.dismissed = True

        self.push_screen(SessionPickerScreen(self._summaries), _on_dismiss)


async def test_screen_renders_two_rows() -> None:
    """Two summaries → OptionList shows two rows."""
    summaries = [
        _make_summary(path=Path("/tmp/a.jsonl"), first_prompt="alpha prompt"),
        _make_summary(path=Path("/tmp/b.jsonl"), first_prompt="bravo prompt"),
    ]
    app = _PickerHostApp(summaries)
    async with app.run_test() as pilot:
        await pilot.pause()
        option_list = app.screen.query_one(OptionList)
        assert option_list.option_count == 2
        prompts = [str(option_list.get_option_at_index(i).prompt) for i in range(2)]
        assert "alpha prompt" in prompts[0]
        assert "bravo prompt" in prompts[1]


async def test_down_then_enter_dismisses_with_second_path() -> None:
    """Press Down then Enter → dismisses with summaries[1].path."""
    summaries = [
        _make_summary(path=Path("/tmp/first.jsonl"), first_prompt="first"),
        _make_summary(path=Path("/tmp/second.jsonl"), first_prompt="second"),
    ]
    app = _PickerHostApp(summaries)
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("down")
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()
        assert app.dismissed
        assert app.result == Path("/tmp/second.jsonl")


async def test_escape_dismisses_with_none() -> None:
    """Press Esc → dismisses with None."""
    summaries = [_make_summary()]
    app = _PickerHostApp(summaries)
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("escape")
        await pilot.pause()
        assert app.dismissed
        assert app.result is None


async def test_empty_summaries_optionlist_empty_escape_returns_none() -> None:
    """Empty summaries → OptionList is empty; Esc still dismisses with None."""
    app = _PickerHostApp([])
    async with app.run_test() as pilot:
        await pilot.pause()
        option_list = app.screen.query_one(OptionList)
        assert option_list.option_count == 0
        await pilot.press("escape")
        await pilot.pause()
        assert app.dismissed
        assert app.result is None
