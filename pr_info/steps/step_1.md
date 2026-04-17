# Step 1: AppCore color state and validation

> See [summary.md](summary.md) for full context (Issue #798).

## Goal

Add `set_prompt_color()` method and `prompt_color` property to `AppCore`. This is the single source of truth for color validation and state.

## LLM Prompt

```
Implement Step 1 of Issue #798 (see pr_info/steps/summary.md and pr_info/steps/step_1.md).
Add color state and validation to AppCore following TDD. Write tests first, then implementation.
Run all three code quality checks after changes. Commit as one unit.
```

## WHERE

- `src/mcp_coder/icoder/core/app_core.py` — add constant + method + property
- `tests/icoder/test_app_core.py` — add test cases

## WHAT

### Module constant in `app_core.py`

```python
NAMED_COLORS: dict[str, str] = {
    "red": "#ef4444",
    "green": "#22c55e",
    "blue": "#3b82f6",
    "yellow": "#eab308",
    "purple": "#a855f7",
    "orange": "#f97316",
    "pink": "#ec4899",
    "cyan": "#06b6d4",
    "default": "#666666",
}

DEFAULT_PROMPT_COLOR: str = "#666666"
```

### On `AppCore.__init__`

```python
self._prompt_color: str = DEFAULT_PROMPT_COLOR
```

### Property

```python
@property
def prompt_color(self) -> str:
    """Current prompt border color as hex string. Always concrete, never None."""
    return self._prompt_color
```

### Method

```python
def set_prompt_color(self, value: str) -> str | None:
    """Validate and set prompt border color.

    Args:
        value: Named color, 6-char hex (with/without #), or CSS color name.

    Returns:
        Error message string on failure, None on success.
    """
```

## ALGORITHM (set_prompt_color)

```
1. Strip and lowercase the value
2. If value in NAMED_COLORS → set _prompt_color to mapped hex, return None
3. Strip leading '#', if remaining is 6 hex chars → set _prompt_color to "#" + hex, return None
4. Try Color.parse(value) → set _prompt_color to color.hex6, return None
5. Catch ColorParseError → return "Unknown color '{original}'. Use /color for options."
```

## DATA

- `set_prompt_color()` returns `str | None` — `None` = success, `str` = error message
- `prompt_color` returns `str` — always a valid hex like `"#666666"`
- Import needed: `from textual.color import Color, ColorParseError`

## TESTS (in `tests/icoder/test_app_core.py`)

```python
# Default state
def test_prompt_color_default(app_core): ...
    # assert app_core.prompt_color == "#666666"

# Named colors
def test_set_prompt_color_named(app_core): ...
    # assert app_core.set_prompt_color("red") is None
    # assert app_core.prompt_color == "#ef4444"

# "default" resets to grey
def test_set_prompt_color_default_resets(app_core): ...
    # app_core.set_prompt_color("red")
    # app_core.set_prompt_color("default")
    # assert app_core.prompt_color == "#666666"

# Case-insensitive
def test_set_prompt_color_case_insensitive(app_core): ...
    # assert app_core.set_prompt_color("Red") is None
    # assert app_core.prompt_color == "#ef4444"

# Hex with #
def test_set_prompt_color_hex_with_hash(app_core): ...
    # assert app_core.set_prompt_color("#f59e0b") is None
    # assert app_core.prompt_color == "#f59e0b"

# Hex without #
def test_set_prompt_color_hex_without_hash(app_core): ...
    # assert app_core.set_prompt_color("f59e0b") is None
    # assert app_core.prompt_color == "#f59e0b"

# Color.parse() fallback (CSS name)
def test_set_prompt_color_css_fallback(app_core): ...
    # assert app_core.set_prompt_color("cornflowerblue") is None
    # assert app_core.prompt_color  # some valid hex

# Invalid color returns error
def test_set_prompt_color_invalid(app_core): ...
    # result = app_core.set_prompt_color("notacolor")
    # assert "Unknown color" in result
    # assert "notacolor" in result

# Invalid doesn't change existing color
def test_set_prompt_color_invalid_preserves_current(app_core): ...
    # app_core.set_prompt_color("red")
    # app_core.set_prompt_color("notacolor")
    # assert app_core.prompt_color == "#ef4444"
```

## Commit message

```
feat(icoder): add prompt color state and validation to AppCore (#798)
```
