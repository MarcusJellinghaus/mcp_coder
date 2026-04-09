"""Tests for the command registry and built-in commands."""

from __future__ import annotations

from mcp_coder.icoder.core.command_registry import (
    CommandRegistry,
    create_default_registry,
)
from mcp_coder.icoder.core.types import Command, Response


def test_help_command() -> None:
    """Test /help returns expected output listing all commands."""
    registry = create_default_registry()
    response = registry.dispatch("/help")
    assert response is not None
    assert "/help" in response.text
    assert "/clear" in response.text
    assert "/quit" in response.text


def test_clear_command() -> None:
    """Test /clear returns clear_output=True."""
    registry = create_default_registry()
    response = registry.dispatch("/clear")
    assert response is not None
    assert response.clear_output is True


def test_quit_command() -> None:
    """Test /quit returns quit=True."""
    registry = create_default_registry()
    response = registry.dispatch("/quit")
    assert response is not None
    assert response.quit is True


def test_unknown_command() -> None:
    """Test unknown slash command returns error."""
    registry = create_default_registry()
    response = registry.dispatch("/unknown")
    assert response is not None
    assert "Unknown command" in response.text


def test_non_command_returns_none() -> None:
    """Test non-slash input returns None."""
    registry = create_default_registry()
    response = registry.dispatch("hello world")
    assert response is None


def test_exit_command() -> None:
    """Test /exit returns quit=True."""
    registry = create_default_registry()
    response = registry.dispatch("/exit")
    assert response is not None
    assert response.quit is True


def test_exit_in_help() -> None:
    """Test /exit appears in /help output."""
    registry = create_default_registry()
    response = registry.dispatch("/help")
    assert response is not None
    assert "/exit" in response.text


def test_all_commands_registered() -> None:
    """Test all built-in commands are registered."""
    registry = create_default_registry()
    commands = registry.get_all()
    names = {c.name for c in commands}
    assert names == {"/help", "/clear", "/quit", "/exit"}


def test_dispatch_case_insensitive() -> None:
    """Test command dispatch is case-insensitive."""
    registry = create_default_registry()
    response = registry.dispatch("/HELP")
    assert response is not None
    assert "/help" in response.text


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
        return Response(text=f"args: {args}")

    response = registry.dispatch("/test foo bar")
    assert response is not None
    assert response.text == "args: ['foo', 'bar']"


def test_command_with_args() -> None:
    """Test that args are correctly passed to command handler."""
    registry = create_default_registry()
    # /help ignores args, but dispatch should still pass them
    response = registry.dispatch("/help extra args")
    assert response is not None
    assert "/help" in response.text


def test_filter_by_input_slash_returns_all() -> None:
    """filter_by_input('/') returns all registered commands."""
    registry = create_default_registry()
    result = registry.filter_by_input("/")
    names = {c.name for c in result}
    assert names == {"/help", "/clear", "/quit", "/exit"}


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
        handler=lambda args: Response(text="skill invoked"),
    )
    registry.add_command(cmd)
    result = registry.dispatch("/skill")
    assert result is not None
    assert result.text == "skill invoked"


def test_add_command_appears_in_filter() -> None:
    """add_command'd commands appear in filter_by_input."""
    registry = CommandRegistry()
    cmd = Command(
        name="/skill",
        description="A skill command",
        handler=lambda args: Response(text="ok"),
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
    assert response is not None
    assert "/hidden-skill" not in response.text


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
    assert response is not None
    assert "/visible-skill" in response.text


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
