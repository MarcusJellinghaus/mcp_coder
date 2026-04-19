# Step 2: Add `{color_prefix}` to templates and workspace, update tests

> **Context**: See [summary.md](summary.md) for full issue context (#797).

## Goal

Add the `{color_prefix}` placeholder to the two interactive templates, build the prefix string in `workspace.py`, and update all affected tests.

## WHERE

| File | Action |
|------|--------|
| `src/mcp_coder/workflows/vscodeclaude/templates.py` | Modify — add `{color_prefix}` to two templates |
| `src/mcp_coder/workflows/vscodeclaude/workspace.py` | Modify — build `color_prefix`, pass to `.format()` |
| `tests/workflows/vscodeclaude/test_templates.py` | Modify — add tests for `{color_prefix}` placeholder |
| `tests/workflows/vscodeclaude/test_workspace_startup_script.py` | Modify — update assertions for `/color` in generated scripts |
| `tests/cli/commands/coordinator/test_vscodeclaude_cli.py` | No changes needed — existing placeholder tests won't break, and `test_templates.py` covers the new `{color_prefix}` placeholder |

## WHAT

### Templates (`templates.py`)

Two templates need `{color_prefix}` added inside the quoted `claude` argument:

**`INTERACTIVE_ONLY_SECTION_WINDOWS`** — change:
```
claude "{command} {issue_number}"
```
to:
```
claude "{color_prefix}{command} {issue_number}"
```

**`INTERACTIVE_RESUME_WITH_COMMAND_WINDOWS`** — change:
```
claude --resume %SESSION_ID% "{command}"
```
to:
```
claude --resume %SESSION_ID% "{color_prefix}{command}"
```

**Important**: These are raw strings (`r""`). The `{color_prefix}` placeholder is just text — the actual newline comes from the variable value at `.format()` time.

### Workspace (`workspace.py`)

In `create_startup_script()`, after reading `commands` and `emoji` from config (~line 526):

```python
# Build color prefix for interactive templates
color = config.get("color") if config else None
color_prefix = f"/color {color}\n" if color else ""
```

Then pass `color_prefix=color_prefix` to the two `.format()` calls:

1. `INTERACTIVE_ONLY_SECTION_WINDOWS.format(...)` (~line 580) — add `color_prefix=color_prefix`
2. `INTERACTIVE_RESUME_WITH_COMMAND_WINDOWS.format(...)` (~line 608) — add `color_prefix=color_prefix`

No changes to automated templates or intervention mode.

## HOW

- `config.get("color")` returns the color string or `None` (no plumbing changes needed)
- `color_prefix` uses a real `\n` (Python string, not raw) so the batch file gets a literal newline
- Empty string `""` when no color → no prefix line, existing behavior preserved

## ALGORITHM

```
config = get_vscodeclaude_config(status)
color = config.get("color") if config else None
color_prefix = f"/color {color}\n" if color else ""
# ... later in template formatting:
INTERACTIVE_ONLY_SECTION_WINDOWS.format(command=cmd, issue_number=num, color_prefix=color_prefix)
INTERACTIVE_RESUME_WITH_COMMAND_WINDOWS.format(command=cmd, step_number=step, color_prefix=color_prefix)
```

## DATA

- `color_prefix`: `str` — either `"/color green\n"` (with literal newline) or `""`
- Generated batch output for single command:
  ```batch
  claude "/color yellow
  /implementation_review_supervisor 123"
  ```
- Generated batch output for multi-command last step:
  ```batch
  claude --resume %SESSION_ID% "/color green
  /discuss"
  ```

## Tests to add/update

### New tests in `test_templates.py`

1. **`test_interactive_only_section_has_color_prefix_placeholder`** — assert `{color_prefix}` is in `INTERACTIVE_ONLY_SECTION_WINDOWS`
2. **`test_interactive_resume_section_has_color_prefix_placeholder`** — assert `{color_prefix}` is in `INTERACTIVE_RESUME_WITH_COMMAND_WINDOWS`

### Updated assertions in `test_workspace_startup_script.py`

Tests that assert on exact `claude "..."` strings need updating:

- **`test_creates_script_with_claude_resume`**: Tests single-command flow (status-07). Assertion `claude "/implementation_review_supervisor 123"` becomes `claude "/color yellow\n/implementation_review_supervisor 123"` (literal newline in file)
- **`test_single_command_uses_interactive_only`**: Same single-command flow (status-07). Same assertion update as above.
- **`test_multi_command_has_automated_and_interactive_sections`**: Tests multi-command flow (status-01). The `claude --resume` assertion for `/discuss` now includes `/color green\n` before `/discuss`.

### New test in `test_workspace_startup_script.py`

- **`test_no_color_config_produces_no_prefix`** — parameterized test verifying no `/color` appears in output: (1) config dict with `commands` but without `"color"` key, (2) `get_vscodeclaude_config` returns `None` (unknown status)

## Verification

1. Run `mcp__tools-py__run_pytest_check` — all tests pass including new ones
2. Run `mcp__tools-py__run_pylint_check` and `mcp__tools-py__run_mypy_check`

## Commit

```
feat(vscodeclaude): prepend /color to interactive prompts (#797)
```

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_2.md, then implement Step 2.

1. Add {color_prefix} placeholder to INTERACTIVE_ONLY_SECTION_WINDOWS and INTERACTIVE_RESUME_WITH_COMMAND_WINDOWS in templates.py.
2. In workspace.py's create_startup_script(), build color_prefix from config.get("color") and pass it to the two interactive template .format() calls.
3. Add two new tests in test_templates.py verifying the placeholder exists in both templates.
4. Update existing test assertions in test_workspace_startup_script.py for the new /color prefix lines, and add a test for the no-color case.

Run all three code quality checks after making changes. Commit with the message from the step file.
```
