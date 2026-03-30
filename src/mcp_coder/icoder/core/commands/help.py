"""The /help command."""

from __future__ import annotations

from typing import TYPE_CHECKING

from mcp_coder.icoder.core.types import Response

if TYPE_CHECKING:
    from mcp_coder.icoder.core.command_registry import CommandRegistry


def register_help(registry: CommandRegistry) -> None:
    """Register the /help command."""

    @registry.register("/help", "Show available commands")
    def handle_help(args: list[str]) -> Response:  # noqa: ARG001
        lines = ["Available commands:"]
        for cmd in registry.get_all():
            lines.append(f"  {cmd.name} - {cmd.description}")
        return Response(text="\n".join(lines))
