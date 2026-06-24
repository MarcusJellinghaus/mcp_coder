"""The /load command — open the session picker."""

from __future__ import annotations

from typing import TYPE_CHECKING

from mcp_coder.icoder.core.types import OpenPicker, Response

if TYPE_CHECKING:
    from mcp_coder.icoder.core.command_registry import CommandRegistry


def register_load(registry: CommandRegistry) -> None:
    """Register the /load command."""

    @registry.register("/load", "Choose and resume a previous session")
    def handle_load(args: list[str]) -> Response:  # noqa: ARG001
        return Response(actions=(OpenPicker(),))
