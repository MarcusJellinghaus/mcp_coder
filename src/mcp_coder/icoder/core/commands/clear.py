"""The /clear command."""

from __future__ import annotations

from typing import TYPE_CHECKING

from mcp_coder.icoder.core.types import Response

if TYPE_CHECKING:
    from mcp_coder.icoder.core.command_registry import CommandRegistry


def register_clear(registry: CommandRegistry) -> None:
    """Register the /clear command."""

    @registry.register("/clear", "Clear the output log")
    def handle_clear(args: list[str]) -> Response:  # noqa: ARG001
        return Response(clear_output=True)
