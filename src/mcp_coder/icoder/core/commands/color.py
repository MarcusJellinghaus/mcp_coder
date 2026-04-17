"""The /color command — change prompt border color."""

from __future__ import annotations

from typing import TYPE_CHECKING

from mcp_coder.icoder.core.types import Response

if TYPE_CHECKING:
    from mcp_coder.icoder.core.app_core import AppCore
    from mcp_coder.icoder.core.command_registry import CommandRegistry


def register_color(registry: CommandRegistry, app_core: AppCore) -> None:
    """Register the /color command. Captures app_core via closure."""

    @registry.register("/color", "Change prompt border color")
    def handle_color(args: list[str]) -> Response:
        if not args:
            return Response(
                text="red, green, blue, yellow, purple, orange, pink, cyan"
                " (default resets to grey)"
            )
        error = app_core.set_prompt_color(args[0])
        if error:
            return Response(text=error)
        return Response()
