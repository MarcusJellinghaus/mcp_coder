"""Command registry with decorator-based registration."""

from __future__ import annotations

from typing import Any, Callable

from mcp_coder.icoder.core.types import Command, Response


class CommandRegistry:
    """Registry of slash commands. Simple dict + decorator."""

    def __init__(self) -> None:
        self._commands: dict[str, Command] = {}

    def register(self, name: str, description: str) -> Callable[..., Any]:
        """Decorator to register a command handler.

        Usage:
            @registry.register("/help", "Show available commands")
            def handle_help(args: list[str]) -> Response:
                ...

        Returns:
            Decorator that registers the handler function.
        """

        def decorator(
            func: Callable[[list[str]], Response],
        ) -> Callable[[list[str]], Response]:
            self._commands[name] = Command(
                name=name, description=description, handler=func
            )
            return func

        return decorator

    def dispatch(self, text: str) -> Response | None:
        """Parse input and dispatch to registered handler.

        Unrecognized slash commands return an error Response.

        Returns:
            Response if input is a slash command, None if not.
        """
        text = text.strip()
        if not text or not text.startswith("/"):
            return None

        parts = text.split()
        name = parts[0].lower()
        args = parts[1:]

        if name in self._commands:
            return self._commands[name].handler(args)

        return Response(
            text=f"Unknown command: {name}. Type /help for available commands."
        )

    def get_all(self) -> list[Command]:
        """Return all registered commands (for /help display)."""
        return list(self._commands.values())


def create_default_registry() -> CommandRegistry:
    """Create registry with all built-in commands registered.

    Returns:
        CommandRegistry with help, clear, and quit commands.
    """
    # Import here to avoid circular imports
    from mcp_coder.icoder.core.commands.clear import register_clear
    from mcp_coder.icoder.core.commands.help import register_help
    from mcp_coder.icoder.core.commands.quit import register_quit

    registry = CommandRegistry()
    register_help(registry)
    register_clear(registry)
    register_quit(registry)
    return registry
