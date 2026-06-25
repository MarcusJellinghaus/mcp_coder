"""The /display command — set the default tool-display tier."""

from __future__ import annotations

from typing import TYPE_CHECKING

from mcp_coder.icoder.core.types import OutputText, RebuildOutput, Response

if TYPE_CHECKING:
    from mcp_coder.icoder.core.app_core import AppCore
    from mcp_coder.icoder.core.command_registry import CommandRegistry


def register_display(registry: CommandRegistry, app_core: AppCore) -> None:
    """Register the /display command. Captures app_core via closure."""

    @registry.register("/display", "Set default tool display tier (oneline|compressed)")
    def handle_display(args: list[str]) -> Response:
        if not args or args[0] not in ("oneline", "compressed"):
            return Response(
                actions=(OutputText(text="Usage: /display oneline|compressed"),)
            )
        app_core.set_tool_display(args[0])  # type: ignore[arg-type]
        return Response(actions=(RebuildOutput(),))
