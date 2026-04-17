# Step 2: /color command handler

> See [summary.md](summary.md) for full context (Issue #798).

## Goal

Create the `/color` command handler in `commands/color.py` and register it in `execute_icoder()`.

## LLM Prompt

```
Implement Step 2 of Issue #798 (see pr_info/steps/summary.md and pr_info/steps/step_2.md).
Create the /color command handler following TDD. Write tests first, then implementation.
Run all three code quality checks after changes. Commit as one unit.
```

## WHERE

- `src/mcp_coder/icoder/core/commands/color.py` — **new file**, command handler
- `src/mcp_coder/cli/commands/icoder.py` — wire `register_color()` call
- `tests/icoder/test_command_registry.py` — add /color dispatch tests
- `tests/icoder/test_cli_icoder.py` — add /color registration wiring test

## WHAT

### `register_color(registry, app_core)` in `commands/color.py`

```python
def register_color(registry: CommandRegistry, app_core: AppCore) -> None:
    """Register the /color command. Captures app_core via closure."""

    @registry.register("/color", "Change prompt border color")
    def handle_color(args: list[str]) -> Response:
        ...
```

### Wiring in `execute_icoder()` (in `cli/commands/icoder.py`)

```python
from ...icoder.core.commands.color import register_color
# ... after app_core creation:
register_color(registry, app_core)
```

## ALGORITHM (handle_color)

```
1. If no args → return Response(text="red, green, blue, yellow, purple, orange, pink, cyan (default resets to grey)")
2. Call app_core.set_prompt_color(args[0])
3. If error returned → return Response(text=error)
4. If None → return Response()  # silent success
```

## DATA

- No-arg: `Response(text="red, green, blue, yellow, purple, orange, pink, cyan (default resets to grey)")`
- Success: `Response()` (empty — border change is the feedback)
- Error: `Response(text="Unknown color 'X'. Use /color for options.")`

## HOW

- Follows exact pattern of `register_info()` and `register_clear()`
- `AppCore` imported with `TYPE_CHECKING` guard (same as other commands)
- Registration call placed next to `register_info()` call in `execute_icoder()`

## TESTS

### In `tests/icoder/test_command_registry.py`

```python
# /color with no args shows color list
def test_color_no_args_shows_list(): ...
    # registry + app_core with /color registered
    # response = registry.dispatch("/color")
    # assert "red" in response.text and "default resets to grey" in response.text

# /color with valid color returns empty response
def test_color_valid_returns_empty(): ...
    # response = registry.dispatch("/color red")
    # assert response.text == ""

# /color with invalid color returns error
def test_color_invalid_returns_error(): ...
    # response = registry.dispatch("/color notacolor")
    # assert "Unknown color" in response.text
```

### In `tests/icoder/test_cli_icoder.py`

```python
# /color is registered in execute_icoder wiring
def test_color_command_registered_in_icoder(): ...
    # Same pattern as test_info_command_registered_in_icoder
    # assert "/color" in command_names
```

## Commit message

```
feat(icoder): add /color slash command (#798)
```
