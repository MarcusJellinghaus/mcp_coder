"""The /quit command."""

from __future__ import annotations

from typing import TYPE_CHECKING

from mcp_coder.icoder.core.types import Response

if TYPE_CHECKING:
    from mcp_coder.icoder.core.command_registry import CommandRegistry


def register_quit(registry: CommandRegistry) -> None:
    """Register the /quit command."""

    @registry.register("/quit", "Exit iCoder")
    def handle_quit(args: list[str]) -> Response:  # noqa: ARG001
        return Response(quit=True)
