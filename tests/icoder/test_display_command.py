"""Tests for the /display slash command."""

from __future__ import annotations

from mcp_coder.icoder.core.app_core import AppCore
from mcp_coder.icoder.core.command_registry import CommandRegistry
from mcp_coder.icoder.core.commands.display import register_display
from mcp_coder.icoder.core.event_log import EventLog
from mcp_coder.icoder.core.types import OutputText, RebuildOutput, Response


def _registry(app_core: AppCore) -> CommandRegistry:
    """Build a fresh registry with /display registered against app_core."""
    registry = CommandRegistry()
    register_display(registry, app_core)
    return registry


def test_display_oneline_returns_rebuild_action(app_core: AppCore) -> None:
    """/display oneline returns a single RebuildOutput action."""
    result = _registry(app_core).dispatch("/display oneline")
    assert result == Response(actions=(RebuildOutput(),))


def test_display_compressed_returns_rebuild_action(app_core: AppCore) -> None:
    """/display compressed returns a single RebuildOutput action."""
    result = _registry(app_core).dispatch("/display compressed")
    assert result == Response(actions=(RebuildOutput(),))


def test_display_no_args_returns_usage_message(app_core: AppCore) -> None:
    """/display without args returns a usage OutputText, no rebuild."""
    result = _registry(app_core).dispatch("/display")
    assert result == Response(
        actions=(OutputText(text="Usage: /display oneline|compressed"),)
    )


def test_display_invalid_arg_returns_usage_message(app_core: AppCore) -> None:
    """/display with an unknown arg returns the usage message."""
    result = _registry(app_core).dispatch("/display verbose")
    assert result == Response(
        actions=(OutputText(text="Usage: /display oneline|compressed"),)
    )


def test_display_updates_app_core_tool_display(app_core: AppCore) -> None:
    """A valid /display mutates AppCore.tool_display."""
    assert app_core.tool_display == "compressed"
    _registry(app_core).dispatch("/display oneline")
    assert app_core.tool_display == "oneline"


def test_display_invalid_arg_does_not_change_tool_display(app_core: AppCore) -> None:
    """An invalid /display arg leaves the current tier unchanged."""
    _registry(app_core).dispatch("/display oneline")
    _registry(app_core).dispatch("/display bogus")
    assert app_core.tool_display == "oneline"


def test_display_emits_display_mode_changed_event(
    app_core: AppCore, event_log: EventLog
) -> None:
    """A valid /display emits a display_mode_changed event with the new tier."""
    _registry(app_core).dispatch("/display oneline")
    matching = [e for e in event_log.entries if e.event == "display_mode_changed"]
    assert len(matching) == 1
    assert matching[0].data.get("to") == "oneline"
