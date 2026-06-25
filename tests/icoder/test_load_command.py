"""Tests for the /load command (returns Response(actions=(OpenPicker(),)))."""

from __future__ import annotations

from mcp_coder.icoder.core.command_registry import (
    CommandRegistry,
    create_default_registry,
)
from mcp_coder.icoder.core.commands.load import register_load
from mcp_coder.icoder.core.types import OpenPicker, Response


def test_load_command_returns_open_picker() -> None:
    """`/load` returns a single OpenPicker action and nothing else."""
    registry = CommandRegistry()
    register_load(registry)
    response = registry.dispatch("/load")
    assert isinstance(response, Response)
    assert response.actions == (OpenPicker(),)


def test_load_registered_in_default_registry() -> None:
    """`/load` is registered by create_default_registry()."""
    registry = create_default_registry()
    assert registry.has_command("/load")
    response = registry.dispatch("/load")
    assert response is not None
    assert response.actions == (OpenPicker(),)


def test_load_command_appears_in_help_listing() -> None:
    """`/load` is part of the get_all() output and is described."""
    registry = create_default_registry()
    names = [c.name for c in registry.get_all()]
    assert "/load" in names
    cmd = next(c for c in registry.get_all() if c.name == "/load")
    assert "previous" in cmd.description.lower() or "session" in cmd.description.lower()
