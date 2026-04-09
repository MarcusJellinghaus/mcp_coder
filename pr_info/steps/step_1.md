# Step 1: Foundation — Response.llm_text, Command.show_in_help, Registry.add_command, Help Filter

**Context**: See `pr_info/steps/summary.md` for full issue context.

## Goal

Add the foundational fields and methods that the skill system will use. All changes are to existing files with full backward compatibility (new fields have defaults).

## Prompt

```
Implement Step 1 of issue #720 (see pr_info/steps/summary.md for context).

Add foundation for skill slash commands:
1. Add `llm_text: str | None = None` to Response dataclass in types.py
2. Add `show_in_help: bool = True` to Command dataclass in types.py
3. Add `add_command(command: Command)` method to CommandRegistry
4. Update /help handler to filter on `show_in_help`
5. Write tests first (TDD), then implement.
6. Run all three code quality checks after changes.
```

## Tests First — `tests/icoder/test_types.py`

### WHERE
`tests/icoder/test_types.py` — append new tests

### WHAT — new test functions
```python
@pytest.mark.parametrize("kwargs, expected", [
    ({}, None),
    ({"llm_text": "override"}, "override"),
])
def test_response_llm_text(kwargs: dict, expected: str | None) -> None:
    """Response.llm_text defaults to None, can be set."""

@pytest.mark.parametrize("kwargs, expected", [
    ({}, True),
    ({"show_in_help": False}, False),
])
def test_command_show_in_help(kwargs: dict, expected: bool) -> None:
    """Command.show_in_help defaults to True, can be set to False."""
```

## Tests First — `tests/icoder/test_command_registry.py`

### WHERE
`tests/icoder/test_command_registry.py` — append new tests

### WHAT — new test functions
```python
def test_add_command() -> None:
    """add_command registers a command that can be dispatched."""

def test_add_command_appears_in_filter() -> None:
    """add_command'd commands appear in filter_by_input."""

def test_help_hides_show_in_help_false() -> None:
    """Commands with show_in_help=False are excluded from /help output."""

def test_help_shows_show_in_help_true() -> None:
    """Commands with show_in_help=True (default) appear in /help output."""

def test_filter_includes_show_in_help_false() -> None:
    """filter_by_input includes commands with show_in_help=False (autocomplete shows all)."""
```

## Implementation

### 1. `src/mcp_coder/icoder/core/types.py`

#### WHAT
- Add `llm_text: str | None = None` field to `Response`
- Add `show_in_help: bool = True` field to `Command`

#### DATA
```python
@dataclass(frozen=True)
class Response:
    text: str = ""
    clear_output: bool = False
    quit: bool = False
    send_to_llm: bool = False
    llm_text: str | None = None  # NEW: override text sent to LLM

@dataclass(frozen=True)
class Command:
    name: str
    description: str
    handler: Callable[[list[str]], Response]
    show_in_help: bool = True  # NEW: False hides from /help, still in autocomplete
```

### 2. `src/mcp_coder/icoder/core/command_registry.py`

#### WHAT
Add `add_command` method to `CommandRegistry`

#### HOW
```python
def add_command(self, command: Command) -> None:
    """Register a pre-built Command directly."""
    self._commands[command.name] = command
```

### 3. `src/mcp_coder/icoder/core/commands/help.py`

#### WHAT
Filter `/help` output to only show commands with `show_in_help=True`.

#### HOW
Change the loop in `handle_help`:
```python
# Before:
for cmd in registry.get_all():

# After:
for cmd in registry.get_all():
    if not cmd.show_in_help:
        continue
```

## Commit Message
```
feat(icoder): add Response.llm_text, Command.show_in_help, Registry.add_command
```
