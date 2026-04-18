# Issue #797: Set session color on human-action startup via /color

## Summary

When vscodeclaude starts a human session, automatically set the Claude Code session color by prepending `/color <color>` to the last interactive prompt. This gives instant visual feedback about which workflow phase the issue is in.

## Architectural / Design Changes

**No new modules, classes, or functions are introduced.** This is a data + template change:

1. **Config layer** (`labels.json`): New optional `"color"` field on vscodeclaude entries that have `commands`. This is pure data — no schema changes needed since configs are plain dicts.

2. **Template layer** (`templates.py`): Two interactive templates gain a `{color_prefix}` placeholder. The placeholder sits inside the quoted string passed to `claude`, before the command. Since templates are raw strings, the actual newline character is injected via the format variable, not embedded in the template.

3. **Script builder** (`workspace.py`): Reads `config.get("color")`, builds a `color_prefix` string (`"/color green\n"` or `""`), and passes it to `.format()`. No conditionals in templates — the empty-string case naturally produces no prefix.

4. **Test fixtures** (`conftest.py`): Mock configs updated to include `color` fields matching the real config, so existing tests exercise the new behavior.

**Design principle**: The `color_prefix` variable absorbs all optionality. Templates stay simple with no conditional logic. Automated steps and intervention mode are unchanged.

## Files Modified

| File | Change |
|------|--------|
| `src/mcp_coder/config/labels.json` | Add `"color"` field to vscodeclaude entries with `commands` |
| `src/mcp_coder/workflows/vscodeclaude/templates.py` | Add `{color_prefix}` to `INTERACTIVE_ONLY_SECTION_WINDOWS` and `INTERACTIVE_RESUME_WITH_COMMAND_WINDOWS` |
| `src/mcp_coder/workflows/vscodeclaude/workspace.py` | Build `color_prefix` from config, pass to `.format()` calls |
| `tests/workflows/vscodeclaude/conftest.py` | Add `"color"` to mock vscodeclaude configs |
| `tests/workflows/vscodeclaude/test_templates.py` | Add tests for `{color_prefix}` placeholder in templates |
| `tests/workflows/vscodeclaude/test_workspace_startup_script.py` | Update assertions for `/color` prefix in generated scripts |

## Files Created

None.

## Color Mapping

| Status | Color |
|--------|-------|
| `status-01:created` | `green` |
| `status-04:plan-review` | `blue` |
| `status-07:code-review` | `yellow` |
| All failure states (`03f*`, `06f*`, `09f`) | `red` |
| `status-10:pr-created` | _(skip — no commands)_ |

## Implementation Steps

- [Step 1](step_1.md) — Config: add `color` to `labels.json` + test fixtures in `conftest.py`
- [Step 2](step_2.md) — Templates + workspace: add `{color_prefix}` placeholder, build prefix, update tests
