# Step 3: Command Registry + Built-in Commands

## References
- **Summary**: `pr_info/steps/summary.md`
- **Issue**: #617 — iCoder initial setup
- **Depends on**: Step 1 (types)

## Goal
Implement the slash command registry with decorator-based registration and the three built-in commands: `/help`, `/clear`, `/quit`.

## WHERE — Files

### New files
- `src/mcp_coder/icoder/core/command_registry.py`
- `src/mcp_coder/icoder/core/commands/help.py`
- `src/mcp_coder/icoder/core/commands/clear.py`
- `src/mcp_coder/icoder/core/commands/quit.py`
- `tests/icoder/test_command_registry.py`

## WHAT — Main Functions and Signatures

### `core/command_registry.py`

```python
class CommandRegistry:
    """Registry of slash commands. Simple dict + decorator."""

    def __init__(self) -> None:
        self._commands: dict[str, Command] = {}

    def register(self, name: str, description: str) -> Callable:
        """Decorator to register a command handler.
        
        Usage:
            @registry.register("/help", "Show available commands")
            def handle_help(args: list[str]) -> Response:
                ...
        """

    def dispatch(self, text: str) -> Response | None:
        """Parse input and dispatch to registered handler.
        
        Returns Response if input is a slash command, None if not.
        Unrecognized slash commands return an error Response.
        """

    def get_all(self) -> list[Command]:
        """Return all registered commands (for /help display)."""


def create_default_registry() -> CommandRegistry:
    """Create registry with all built-in commands registered."""
```

### `core/commands/help.py`

```python
def register_help(registry: CommandRegistry) -> None:
    """Register the /help command."""
    @registry.register("/help", "Show available commands")
    def handle_help(args: list[str]) -> Response:
        # Build help text from registry.get_all()
        ...
```

### `core/commands/clear.py`

```python
def register_clear(registry: CommandRegistry) -> None:
    """Register the /clear command."""
    @registry.register("/clear", "Clear the output log")
    def handle_clear(args: list[str]) -> Response:
        return Response(clear_output=True)
```

### `core/commands/quit.py`

```python
def register_quit(registry: CommandRegistry) -> None:
    """Register the /quit command."""
    @registry.register("/quit", "Exit iCoder")
    def handle_quit(args: list[str]) -> Response:
        return Response(quit=True)
```

## HOW — Integration Points

- Each command module exposes a `register_*(registry)` function
- `create_default_registry()` calls all three register functions
- `dispatch()` splits input on whitespace: first token is command name, rest are args
- Input not starting with `/` → return `None` (not a command)
- Input starting with `/` but not registered → return `Response(text="Unknown command: /foo")`

## ALGORITHM — Core Logic

```
dispatch(text):
    text = text.strip()
    if not text.startswith("/"):
        return None  # Not a command
    parts = text.split()
    name = parts[0].lower()
    args = parts[1:]
    if name in self._commands:
        return self._commands[name].handler(args)
    return Response(text=f"Unknown command: {name}. Type /help for available commands.")

create_default_registry():
    registry = CommandRegistry()
    register_help(registry)  # passes registry ref so /help can list all commands
    register_clear(registry)
    register_quit(registry)
    return registry
```

## DATA — Return Values

- `dispatch()` returns `Response | None` — `None` means "not a slash command"
- `/help` returns `Response(text="Available commands:\n  /help - ...\n  /clear - ...\n  /quit - ...")`
- `/clear` returns `Response(clear_output=True)`
- `/quit` returns `Response(quit=True)`

## Tests — `tests/icoder/test_command_registry.py`

```python
# Test /help returns expected output listing all commands
def test_help_command():
    registry = create_default_registry()
    response = registry.dispatch("/help")
    assert response is not None
    assert "/help" in response.text
    assert "/clear" in response.text
    assert "/quit" in response.text

# Test /clear returns clear_output=True
def test_clear_command():
    registry = create_default_registry()
    response = registry.dispatch("/clear")
    assert response is not None
    assert response.clear_output is True

# Test /quit returns quit=True
def test_quit_command():
    registry = create_default_registry()
    response = registry.dispatch("/quit")
    assert response is not None
    assert response.quit is True

# Test unknown slash command returns error
def test_unknown_command():
    registry = create_default_registry()
    response = registry.dispatch("/unknown")
    assert response is not None
    assert "Unknown command" in response.text

# Test non-slash input returns None
def test_non_command_returns_none():
    registry = create_default_registry()
    response = registry.dispatch("hello world")
    assert response is None

# Test all built-in commands are registered
def test_all_commands_registered():
    registry = create_default_registry()
    commands = registry.get_all()
    names = {c.name for c in commands}
    assert names == {"/help", "/clear", "/quit"}

# Test command dispatch is case-insensitive
def test_dispatch_case_insensitive():
    registry = create_default_registry()
    response = registry.dispatch("/HELP")
    assert response is not None
    assert "/help" in response.text

# Test empty and whitespace input
def test_empty_input_returns_none():
    registry = create_default_registry()
    assert registry.dispatch("") is None
    assert registry.dispatch("   ") is None
```

## LLM Prompt

```
You are implementing Step 3 of the iCoder TUI feature (#617).
Read pr_info/steps/summary.md for full context, then implement this step.

Tasks:
1. Implement core/command_registry.py with CommandRegistry class + create_default_registry()
2. Implement core/commands/help.py, clear.py, quit.py — each with a register_*() function
3. Write tests in tests/icoder/test_command_registry.py
4. Run pylint, mypy, pytest to verify all checks pass

Key details:
- Registry is a simple dict[str, Command] with a decorator for registration
- dispatch() returns None for non-slash input, Response for slash commands
- Unknown slash commands get an error Response (not None)
- /help lists all registered commands by iterating registry.get_all()
- create_default_registry() wires all three commands

Use MCP tools for all file operations. Run all three code quality checks after changes.
```
