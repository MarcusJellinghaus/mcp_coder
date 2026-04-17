# Step 1: Color validation module and AppCore color state

> See [summary.md](summary.md) for full context (Issue #798).

## Goal

Create `colors.py` with `NAMED_COLORS`, `DEFAULT_PROMPT_COLOR`, and `validate_color()`. Add `_prompt_color` field and `prompt_color` property to `AppCore`, plus `set_prompt_color()` that delegates to `validate_color()`.

## LLM Prompt

```
Implement Step 1 of Issue #798 (see pr_info/steps/summary.md and pr_info/steps/step_1.md).
Create colors.py module and add color state to AppCore following TDD. Write tests first, then implementation.
Run all three code quality checks after changes. Commit as one unit.
```

## WHERE

- `src/mcp_coder/icoder/core/colors.py` — **new file**, `NAMED_COLORS`, `DEFAULT_PROMPT_COLOR`, `validate_color()`
- `tests/icoder/test_colors.py` — **new file**, tests for `validate_color()`
- `src/mcp_coder/icoder/core/app_core.py` — add `_prompt_color`, `prompt_color` property, `set_prompt_color()` delegating to `colors.validate_color()`
- `tests/icoder/test_app_core.py` — thinner integration tests for `set_prompt_color()`

**Note:** The Textual import (`Color`, `ColorParseError`) goes in `colors.py`, NOT `app_core.py`.

## WHAT

### `colors.py` — new module

```python
from textual.color import Color, ColorParseError

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


def validate_color(value: str) -> tuple[str | None, str | None]:
    """Validate a color string and return its hex representation.

    Args:
        value: Named color, 6-char hex (with/without #), 3-digit hex, or CSS color name.

    Returns:
        (hex_color, None) on success, (None, error_msg) on failure.
    """
```

### ALGORITHM (validate_color)

```
1. Strip and lowercase the value
2. If value in NAMED_COLORS → return (mapped hex, None)
3. Strip leading '#', if remaining is 6 hex chars → return ("#" + hex, None)
4. Try Color.parse(value) → return (color.hex6, None)
5. Catch ColorParseError → return (None, "Unknown color '{original}'. Use /color for options.")
```

### On `AppCore.__init__`

```python
from .colors import DEFAULT_PROMPT_COLOR

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
    """Validate and set prompt border color. Delegates to validate_color().

    Returns:
        Error message string on failure, None on success.
    """
    from .colors import validate_color
    hex_color, error = validate_color(value)
    if error:
        return error
    self._prompt_color = hex_color
    return None
```

## DATA

- `validate_color()` returns `tuple[str | None, str | None]` — `(hex, None)` = success, `(None, error)` = failure
- `set_prompt_color()` returns `str | None` — `None` = success, `str` = error message
- `prompt_color` returns `str` — always a valid hex like `"#666666"`

## TESTS

### In `tests/icoder/test_colors.py` (new file)

```python
from mcp_coder.icoder.core.colors import NAMED_COLORS, validate_color

@pytest.mark.parametrize("name,expected_hex", list(NAMED_COLORS.items()))
def test_validate_color_named(name, expected_hex): ...
    # hex_color, error = validate_color(name)
    # assert error is None
    # assert hex_color == expected_hex

# Case-insensitive
def test_validate_color_case_insensitive(): ...
    # hex_color, error = validate_color("Red")
    # assert error is None
    # assert hex_color == "#ef4444"

# Hex with #
def test_validate_color_hex_with_hash(): ...
    # hex_color, error = validate_color("#f59e0b")
    # assert error is None
    # assert hex_color == "#f59e0b"

# Hex without #
def test_validate_color_hex_without_hash(): ...
    # hex_color, error = validate_color("f59e0b")
    # assert error is None
    # assert hex_color == "#f59e0b"

# 3-digit hex falls through to Color.parse() fallback
def test_validate_color_3digit_hex(): ...
    # hex_color, error = validate_color("#f00")
    # assert error is None  # Color.parse handles it

# Color.parse() fallback (CSS name)
def test_validate_color_css_fallback(): ...
    # hex_color, error = validate_color("cornflowerblue")
    # assert error is None
    # assert hex_color is not None  # some valid hex

# Invalid color returns error
def test_validate_color_invalid(): ...
    # hex_color, error = validate_color("notacolor")
    # assert hex_color is None
    # assert "Unknown color" in error
    # assert "notacolor" in error

# "default" maps to grey
def test_validate_color_default(): ...
    # hex_color, error = validate_color("default")
    # assert error is None
    # assert hex_color == "#666666"
```

### In `tests/icoder/test_app_core.py` (thinner integration tests)

```python
# Default state
def test_prompt_color_default(app_core): ...
    # assert app_core.prompt_color == "#666666"

# Set and get
def test_set_prompt_color_and_get(app_core): ...
    # assert app_core.set_prompt_color("red") is None
    # assert app_core.prompt_color == "#ef4444"

# Invalid preserves current
def test_set_prompt_color_invalid_preserves_current(app_core): ...
    # app_core.set_prompt_color("red")
    # app_core.set_prompt_color("notacolor")
    # assert app_core.prompt_color == "#ef4444"
```

## Commit message

```
feat(icoder): add color validation module and prompt color state (#798)
```
