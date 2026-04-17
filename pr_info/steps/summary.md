# Issue #798: Add /color CLI command with colored prompt bar frame

## Summary

Add a `/color` slash command to the iCoder TUI that changes the InputArea border color at runtime, plus a `--initial-color` CLI parameter to set it at startup. The border defaults to medium grey (`#666666`) with a `round` style.

## Architectural / Design Changes

### State: `AppCore` gains color state + validation
- `AppCore` gets a `_prompt_color` field (default `"#666666"`) with a `prompt_color` property
- `AppCore.set_prompt_color(value: str) -> str | None` is the **single validation point** — validates named colors, hex codes, and `Color.parse()` fallback. Returns error string or `None` on success
- Named color map (`NAMED_COLORS` dict) lives as a module constant in `app_core.py`

### Command: new `commands/color.py`
- Thin `register_color(registry, app_core)` following the `register_info` pattern
- No-arg shows color list, with-arg delegates to `app_core.set_prompt_color()`
- Silent on success (empty `Response()`), error text on failure

### UI: border applied after every input
- `ICoderApp` gains a `_apply_prompt_border()` helper that reads `app_core.prompt_color` and sets `input_area.styles.border = ("round", Color.parse(value))`
- Called from `on_mount()` (initial border) and `on_input_area_input_submitted()` (after every input)
- Default grey border also declared in `styles.py` CSS

### CLI: `--initial-color` parameter
- Added to icoder argparse in `parsers.py`
- Applied in `execute_icoder()` after `app_core` creation via `app_core.set_prompt_color()`
- Invalid values: `logger.warning()` + fall back to default

## Files Modified

| File | Change |
|------|--------|
| `src/mcp_coder/icoder/core/app_core.py` | Add `NAMED_COLORS`, `_prompt_color`, `prompt_color` property, `set_prompt_color()` |
| `src/mcp_coder/icoder/core/commands/color.py` | **New file** — `register_color()` command handler |
| `src/mcp_coder/icoder/ui/styles.py` | Add `border: round #666666;` to InputArea CSS |
| `src/mcp_coder/icoder/ui/app.py` | Add `_apply_prompt_border()`, call from `on_mount()` and `on_input_area_input_submitted()` |
| `src/mcp_coder/cli/parsers.py` | Add `--initial-color` to icoder parser |
| `src/mcp_coder/cli/commands/icoder.py` | Wire `register_color()`, apply `--initial-color` |

## Test Files Modified

| File | Change |
|------|--------|
| `tests/icoder/test_app_core.py` | Tests for `set_prompt_color()` and `prompt_color` property |
| `tests/icoder/test_command_registry.py` | Tests for `/color` command registration and dispatch |
| `tests/icoder/test_cli_icoder.py` | Tests for `--initial-color` parser flag and wiring |

## Implementation Steps

1. **Step 1** — `AppCore.set_prompt_color()` + `prompt_color` property (state + validation logic, with tests)
2. **Step 2** — `/color` command handler in `commands/color.py` (command registration + dispatch, with tests)
3. **Step 3** — UI wiring: default border CSS + `_apply_prompt_border()` in app.py
4. **Step 4** — `--initial-color` CLI parameter (parser + wiring in execute_icoder, with tests)
