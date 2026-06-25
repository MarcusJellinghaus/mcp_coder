"""Tests for the DetailModal widget and its pure text builder."""

from __future__ import annotations

from datetime import datetime
from unittest.mock import patch

import pytest
from textual.app import App
from textual.widgets import TextArea

from mcp_coder.icoder.ui.widgets.detail_modal import DetailModal, build_detail_text
from mcp_coder.icoder.ui.widgets.output_log import ContentUnit

_TS = datetime(2026, 6, 24, 12, 30, 45)


def _tool_unit(
    *,
    args: dict[str, object] | None = None,
    output: str | None = "line1\nline2",
    is_error: bool = False,
    duration_ms: int | None = 120,
) -> ContentUnit:
    """Build a tool ContentUnit for tests."""
    return ContentUnit(
        id="t1",
        kind="tool",
        timestamp=_TS,
        tool_name="read_file",
        args={"path": "src/main.py"} if args is None else args,
        output=output,
        total_lines=2,
        duration_ms=duration_ms,
        is_error=is_error,
    )


def _user_unit() -> ContentUnit:
    """Build a user_input ContentUnit for tests."""
    return ContentUnit(
        id="u1",
        kind="user_input",
        timestamp=_TS,
        full_text="hello\nworld",
    )


def _turn_unit() -> ContentUnit:
    """Build an assistant_turn ContentUnit for tests."""
    return ContentUnit(
        id="a1",
        kind="assistant_turn",
        timestamp=_TS,
        full_text="Here is my answer.",
    )


# --------------------------------------------------------------------------- #
# build_detail_text — pure function
# --------------------------------------------------------------------------- #


def test_build_detail_text_tool_has_header_args_output_footer() -> None:
    """A tool unit renders header, args, output and a footer."""
    text = build_detail_text(_tool_unit())

    assert "Tool: read_file" in text
    assert "Args:" in text
    assert "path: src/main.py" in text
    assert "Output:" in text
    assert "Status:" in text
    assert "120ms" in text
    assert "2026-06-24 12:30:45" in text


def test_build_detail_text_tool_no_args() -> None:
    """An empty args dict renders ``Args: (none)``."""
    text = build_detail_text(_tool_unit(args={}))

    assert "Args: (none)" in text


def test_build_detail_text_tool_error_shows_error_status() -> None:
    """An errored tool reports ``Status: error`` in the footer."""
    text = build_detail_text(_tool_unit(is_error=True))

    assert "Status: error" in text


def test_build_detail_text_user_input() -> None:
    """A user_input unit renders its header, full text and footer kind."""
    text = build_detail_text(_user_unit())

    assert "User input" in text
    assert "hello\nworld" in text
    assert "Kind: user_input" in text


def test_build_detail_text_assistant_turn() -> None:
    """An assistant_turn unit renders header, full text and footer kind."""
    text = build_detail_text(_turn_unit())

    assert "Assistant turn" in text
    assert "Here is my answer." in text
    assert "Kind: assistant_turn" in text


def test_build_detail_text_no_box_chars() -> None:
    """The modal body never contains compressed-view box characters."""
    for unit in (_tool_unit(), _user_unit(), _turn_unit()):
        text = build_detail_text(unit)
        for char in ("│", "┌", "└", "├"):
            assert char not in text


# --------------------------------------------------------------------------- #
# DetailModal — Pilot behaviour
# --------------------------------------------------------------------------- #

pytestmark = pytest.mark.textual_integration


class _ModalApp(App[None]):
    """Minimal app that pushes a DetailModal at mount."""

    def __init__(self, unit: ContentUnit) -> None:
        super().__init__()
        self._unit = unit

    def on_mount(self) -> None:
        self.push_screen(DetailModal(self._unit))


async def test_modal_escape_dismisses() -> None:
    """Pressing Escape removes the modal from the screen stack."""
    app = _ModalApp(_tool_unit())
    async with app.run_test() as pilot:
        await pilot.pause()
        assert isinstance(app.screen, DetailModal)
        await pilot.press("escape")
        await pilot.pause()
        assert not isinstance(app.screen, DetailModal)


async def test_modal_enter_dismisses() -> None:
    """Pressing Enter removes the modal from the screen stack."""
    app = _ModalApp(_tool_unit())
    async with app.run_test() as pilot:
        await pilot.pause()
        assert isinstance(app.screen, DetailModal)
        await pilot.press("enter")
        await pilot.pause()
        assert not isinstance(app.screen, DetailModal)


async def test_modal_ctrl_c_copy_selection_calls_clipboard() -> None:
    """Ctrl+C copies the selected text via Textual's clipboard."""
    app = _ModalApp(_tool_unit())
    async with app.run_test() as pilot:
        await pilot.pause()
        text_area = app.screen.query_one(TextArea)
        text_area.select_all()
        await pilot.pause()
        with patch.object(app, "copy_to_clipboard") as mock_copy:
            await pilot.press("ctrl+c")
            await pilot.pause()
    mock_copy.assert_called_once_with(text_area.text)


async def test_modal_textarea_is_read_only() -> None:
    """The modal's TextArea is read-only."""
    app = _ModalApp(_tool_unit())
    async with app.run_test() as pilot:
        await pilot.pause()
        text_area = app.screen.query_one(TextArea)
        assert text_area.read_only is True
