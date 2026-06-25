"""Tests for the command registry and built-in commands."""

from __future__ import annotations

from typing import Any

from mcp_coder.icoder.core.command_registry import (
    CommandRegistry,
    create_default_registry,
)
from mcp_coder.icoder.core.types import (
    ClearOutput,
    Command,
    OutputText,
    Quit,
    ResetSession,
    Response,
)


def _output_text(response: Response | None) -> str:
    """Join the text of all OutputText actions in a response."""
    assert response is not None
    return "\n".join(a.text for a in response.actions if isinstance(a, OutputText))


def test_help_command() -> None:
    """Test /help returns expected output listing all commands."""
    registry = create_default_registry()
    response = registry.dispatch("/help")
    text = _output_text(response)
    assert "/help" in text
    assert "/clear" in text
    assert "/quit" in text


def test_clear_command() -> None:
    """Test /clear returns ClearOutput + ResetSession actions."""
    registry = create_default_registry()
    response = registry.dispatch("/clear")
    assert response is not None
    assert response.actions == (ClearOutput(), ResetSession())


def test_quit_command() -> None:
    """Test /quit returns a Quit action."""
    registry = create_default_registry()
    response = registry.dispatch("/quit")
    assert response is not None
    assert response.actions == (Quit(),)


def test_unknown_command() -> None:
    """Test unknown slash command returns error."""
    registry = create_default_registry()
    response = registry.dispatch("/unknown")
    assert "Unknown command" in _output_text(response)


def test_non_command_returns_none() -> None:
    """Test non-slash input returns None."""
    registry = create_default_registry()
    response = registry.dispatch("hello world")
    assert response is None


def test_exit_command() -> None:
    """Test /exit returns a Quit action."""
    registry = create_default_registry()
    response = registry.dispatch("/exit")
    assert response is not None
    assert response.actions == (Quit(),)


def test_exit_in_help() -> None:
    """Test /exit appears in /help output."""
    registry = create_default_registry()
    response = registry.dispatch("/help")
    assert "/exit" in _output_text(response)


def test_all_commands_registered() -> None:
    """Test all built-in commands are registered."""
    registry = create_default_registry()
    commands = registry.get_all()
    names = {c.name for c in commands}
    assert names == {"/help", "/clear", "/load", "/quit", "/exit"}


def test_dispatch_case_insensitive() -> None:
    """Test command dispatch is case-insensitive."""
    registry = create_default_registry()
    response = registry.dispatch("/HELP")
    assert "/help" in _output_text(response)


def test_empty_input_returns_none() -> None:
    """Test empty and whitespace input returns None."""
    registry = create_default_registry()
    assert registry.dispatch("") is None
    assert registry.dispatch("   ") is None


def test_register_custom_command() -> None:
    """Test registering a custom command via decorator."""
    registry = CommandRegistry()

    @registry.register("/test", "A test command")
    def handle_test(args: list[str]) -> Response:
        return Response(actions=(OutputText(text=f"args: {args}"),))

    response = registry.dispatch("/test foo bar")
    assert _output_text(response) == "args: ['foo', 'bar']"


def test_command_with_args() -> None:
    """Test that args are correctly passed to command handler."""
    registry = create_default_registry()
    # /help ignores args, but dispatch should still pass them
    response = registry.dispatch("/help extra args")
    assert "/help" in _output_text(response)


def test_filter_by_input_slash_returns_all() -> None:
    """filter_by_input('/') returns all registered commands."""
    registry = create_default_registry()
    result = registry.filter_by_input("/")
    names = {c.name for c in result}
    assert names == {"/help", "/clear", "/load", "/quit", "/exit"}


def test_filter_by_input_prefix_match() -> None:
    """filter_by_input('/he') returns [/help]."""
    registry = create_default_registry()
    result = registry.filter_by_input("/he")
    assert len(result) == 1
    assert result[0].name == "/help"


def test_filter_by_input_case_insensitive() -> None:
    """filter_by_input('/HE') returns [/help] (case-insensitive)."""
    registry = create_default_registry()
    result = registry.filter_by_input("/HE")
    assert len(result) == 1
    assert result[0].name == "/help"


def test_filter_by_input_no_match() -> None:
    """filter_by_input('/xyz') returns []."""
    registry = create_default_registry()
    assert registry.filter_by_input("/xyz") == []


def test_filter_by_input_empty_string() -> None:
    """filter_by_input('') returns [] (not a command prefix)."""
    registry = create_default_registry()
    assert registry.filter_by_input("") == []


def test_filter_by_input_no_slash() -> None:
    """filter_by_input('hello') returns [] (doesn't start with '/')."""
    registry = create_default_registry()
    assert registry.filter_by_input("hello") == []


def test_filter_by_input_sorted() -> None:
    """filter_by_input results are sorted by command name."""
    registry = create_default_registry()
    result = registry.filter_by_input("/")
    names = [c.name for c in result]
    assert names == sorted(names)


# --- Step 1: add_command and show_in_help tests ---


def test_add_command() -> None:
    """add_command registers a command that can be dispatched."""
    registry = CommandRegistry()
    cmd = Command(
        name="/skill",
        description="A skill command",
        handler=lambda args: Response(actions=(OutputText(text="skill invoked"),)),
    )
    registry.add_command(cmd)
    result = registry.dispatch("/skill")
    assert _output_text(result) == "skill invoked"


def test_add_command_appears_in_filter() -> None:
    """add_command'd commands appear in filter_by_input."""
    registry = CommandRegistry()
    cmd = Command(
        name="/skill",
        description="A skill command",
        handler=lambda args: Response(),
    )
    registry.add_command(cmd)
    result = registry.filter_by_input("/sk")
    assert len(result) == 1
    assert result[0].name == "/skill"


def test_help_hides_show_in_help_false() -> None:
    """Commands with show_in_help=False are excluded from /help output."""
    registry = create_default_registry()
    hidden = Command(
        name="/hidden-skill",
        description="Should not appear in help",
        handler=lambda args: Response(),
        show_in_help=False,
    )
    registry.add_command(hidden)
    response = registry.dispatch("/help")
    assert "/hidden-skill" not in _output_text(response)


def test_help_shows_show_in_help_true() -> None:
    """Commands with show_in_help=True (default) appear in /help output."""
    registry = create_default_registry()
    visible = Command(
        name="/visible-skill",
        description="Should appear in help",
        handler=lambda args: Response(),
        show_in_help=True,
    )
    registry.add_command(visible)
    response = registry.dispatch("/help")
    assert "/visible-skill" in _output_text(response)


def test_has_command_returns_true_for_existing() -> None:
    """has_command returns True for a registered command."""
    registry = create_default_registry()
    assert registry.has_command("/help") is True


def test_has_command_returns_false_for_missing() -> None:
    """has_command returns False for an unregistered command."""
    registry = create_default_registry()
    assert registry.has_command("/nonexistent") is False


def test_has_command_after_add_command() -> None:
    """has_command returns True after add_command."""
    registry = CommandRegistry()
    assert registry.has_command("/skill") is False
    cmd = Command(
        name="/skill",
        description="A skill",
        handler=lambda args: Response(),
    )
    registry.add_command(cmd)
    assert registry.has_command("/skill") is True


def test_filter_includes_show_in_help_false() -> None:
    """filter_by_input includes commands with show_in_help=False (autocomplete shows all)."""
    registry = CommandRegistry()
    hidden = Command(
        name="/hidden-skill",
        description="Hidden from help",
        handler=lambda args: Response(),
        show_in_help=False,
    )
    registry.add_command(hidden)
    result = registry.filter_by_input("/hid")
    assert len(result) == 1
    assert result[0].name == "/hidden-skill"


# --- Step 2: /color command tests ---


def _make_registry_with_color() -> tuple[CommandRegistry, Any]:
    """Create a registry with /color registered via a real AppCore."""
    from unittest.mock import MagicMock

    from mcp_coder.icoder.core.commands.color import register_color

    registry = CommandRegistry()
    app_core = MagicMock()
    register_color(registry, app_core)
    return registry, app_core


def test_color_no_args_shows_list() -> None:
    """Test /color with no args shows color list."""
    registry, _ = _make_registry_with_color()
    response = registry.dispatch("/color")
    text = _output_text(response)
    assert "red" in text
    assert "default resets to grey" in text


def test_color_valid_returns_empty() -> None:
    """Test /color with valid color returns empty response."""
    registry, app_core = _make_registry_with_color()
    app_core.set_prompt_color.return_value = None
    response = registry.dispatch("/color red")
    assert response is not None
    assert response.actions == ()


def test_color_invalid_returns_error() -> None:
    """Test /color with invalid color returns error."""
    registry, app_core = _make_registry_with_color()
    app_core.set_prompt_color.return_value = (
        "Unknown color 'notacolor'. Use /color for options."
    )
    response = registry.dispatch("/color notacolor")
    assert "Unknown color" in _output_text(response)
