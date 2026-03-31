"""Tests for the command registry and built-in commands."""

from __future__ import annotations

from mcp_coder.icoder.core.command_registry import (
    CommandRegistry,
    create_default_registry,
)
from mcp_coder.icoder.core.types import Response


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
