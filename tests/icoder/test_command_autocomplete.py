"""Tests for CommandAutocomplete widget."""

from __future__ import annotations

import pytest
from textual.app import App, ComposeResult

from mcp_coder.icoder.core.types import Command, Response
from mcp_coder.icoder.ui.widgets.command_autocomplete import CommandAutocomplete

pytestmark = pytest.mark.textual_integration


def _noop(args: list[str]) -> Response:
    return Response()


def _make_commands() -> list[Command]:
    return [
        Command(name="/help", description="Show help", handler=_noop),
        Command(name="/clear", description="Clear screen", handler=_noop),
        Command(name="/quit", description="Quit app", handler=_noop),
    ]


class AutocompleteTestApp(App[None]):
    """Minimal test app hosting CommandAutocomplete."""

    CSS = """
    CommandAutocomplete {
        display: none;
        height: auto;
        max-height: 8;
    }
    """

    def compose(self) -> ComposeResult:
        yield CommandAutocomplete()


@pytest.mark.asyncio
async def test_dropdown_hidden_by_default() -> None:
    """CommandAutocomplete is not displayed initially (display=False)."""
    app = AutocompleteTestApp()
    async with app.run_test():
        dropdown = app.query_one(CommandAutocomplete)
        assert not dropdown.is_visible


@pytest.mark.asyncio
async def test_show_hide_toggles_display() -> None:
    """show_dropdown/hide_dropdown toggle display + is_visible reflects it."""
    app = AutocompleteTestApp()
    async with app.run_test():
        dropdown = app.query_one(CommandAutocomplete)
        assert not dropdown.is_visible
        dropdown.show_dropdown()
        assert dropdown.is_visible
        dropdown.hide_dropdown()
        assert not dropdown.is_visible


@pytest.mark.asyncio
async def test_update_matches_shows_commands() -> None:
    """update_matches populates options with '/name — description' labels and id=name."""
    app = AutocompleteTestApp()
    async with app.run_test():
        dropdown = app.query_one(CommandAutocomplete)
        commands = _make_commands()
        dropdown.update_matches(commands)
        assert dropdown.option_count == 3
        opt = dropdown.get_option_at_index(0)
        assert opt.id == "/help"
        assert "/help" in str(opt.prompt)
        assert "Show help" in str(opt.prompt)


@pytest.mark.asyncio
async def test_update_matches_empty_shows_no_matching() -> None:
    """Empty matches list shows a single disabled '(no matching commands)' row."""
    app = AutocompleteTestApp()
    async with app.run_test():
        dropdown = app.query_one(CommandAutocomplete)
        dropdown.update_matches([])
        assert dropdown.option_count == 1
        opt = dropdown.get_option_at_index(0)
        assert opt.disabled is True
        assert "(no matching commands)" in str(opt.prompt)


@pytest.mark.asyncio
async def test_select_highlighted_returns_command_name() -> None:
    """select_highlighted returns the option id (command name) of the highlighted row."""
    app = AutocompleteTestApp()
    async with app.run_test():
        dropdown = app.query_one(CommandAutocomplete)
        commands = _make_commands()
        dropdown.update_matches(commands)
        assert dropdown.select_highlighted() == "/help"


@pytest.mark.asyncio
async def test_update_matches_marks_disabled_command() -> None:
    """A blocked command shows its (disabled: <reason>) marker in the label."""
    app = AutocompleteTestApp()
    async with app.run_test():
        dropdown = app.query_one(CommandAutocomplete)
        cmd = Command(
            name="/broken",
            description="Broken skill",
            handler=_noop,
            disabled_reason="tools: malformed",
        )
        dropdown.update_matches([cmd])
        assert dropdown.option_count == 1
        opt = dropdown.get_option_at_index(0)
        assert "/broken" in str(opt.prompt)
        assert "Broken skill" in str(opt.prompt)
        assert "(disabled: tools: malformed)" in str(opt.prompt)


@pytest.mark.asyncio
async def test_update_matches_disabled_command_stays_selectable() -> None:
    """A blocked command's Option stays enabled and can be selected."""
    app = AutocompleteTestApp()
    async with app.run_test():
        dropdown = app.query_one(CommandAutocomplete)
        cmd = Command(
            name="/broken",
            description="Broken skill",
            handler=_noop,
            disabled_reason="tools: malformed",
        )
        dropdown.update_matches([cmd])
        opt = dropdown.get_option_at_index(0)
        assert opt.disabled is False
        assert dropdown.select_highlighted() == "/broken"


@pytest.mark.asyncio
async def test_highlight_navigation() -> None:
    """highlight_next / highlight_previous move the highlight through the options."""
    app = AutocompleteTestApp()
    async with app.run_test():
        dropdown = app.query_one(CommandAutocomplete)
        commands = _make_commands()
        dropdown.update_matches(commands)
        assert dropdown.highlighted == 0
        dropdown.highlight_next()
        assert dropdown.highlighted == 1
        dropdown.highlight_next()
        assert dropdown.highlighted == 2
        dropdown.highlight_previous()
        assert dropdown.highlighted == 1
