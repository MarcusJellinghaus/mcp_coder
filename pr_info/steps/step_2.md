# Step 2: Rewrite get_help_text() and Remove get_usage_examples()

> **Reference**: See `pr_info/steps/summary.md` for overall design.

## Goal

Rewrite `get_help_text()` to render detailed output from the shared `CATEGORIES` data. Remove `get_usage_examples()` (now dead code). Update `execute_help()` to use the new signature. Update tests.

## WHERE

- `src/mcp_coder/cli/commands/help.py`
- `tests/cli/commands/test_help.py`

## WHAT

### Rewritten function (renders from `COMMAND_CATEGORIES`)

```python
def get_help_text() -> str:
    """Render detailed help: category headers + descriptions + aligned commands."""
```

Note: the `include_examples` parameter is removed — the new output format doesn't include examples.

### Removed function

```python
# REMOVE: get_usage_examples() — no longer used
```

### Updated function

```python
def execute_help(_args: argparse.Namespace) -> int:
    """Execute help command."""
    help_text = get_help_text()  # no more include_examples param
    print(help_text)
    return 0
```

## ALGORITHM (get_help_text)

```
max_width = max command name length across all categories
lines = [header, blank, usage line, blank]
for each category:
    lines += [blank, category.name]
    lines += ["  " + category.description]     # <-- only difference from compact
    lines += [blank]
    for each command:
        lines += [f"  {name:<{max_width}}  {description}"]
lines += [blank, "Run 'mcp-coder <command> --help' for command-specific options."]
lines += [blank, "For more information, visit: https://github.com/MarcusJellinghaus/mcp_coder"]
return "\n".join(lines)
```

## DATA

- `get_help_text()` returns `str` — no parameters
- Same `COMMAND_CATEGORIES` data as step 1

## HOW (Integration)

- `execute_help()` calls `get_help_text()` (simplified, no parameter)
- `get_usage_examples()` is deleted
- `main.py` still imports `get_help_text` — it still exists, just with a new signature. Since `main.py` calls `get_help_text(include_examples=False)`, we need to ensure the old call still works OR update main.py simultaneously. **Simplest approach**: update the `handle_no_command()` call in main.py in this step too, to avoid a broken intermediate state. Change it to call `get_help_text()` temporarily (step 3 will switch to `get_compact_help_text()`).

## Tests to Update/Write

In `tests/cli/commands/test_help.py`:

1. **`test_detailed_help_has_category_descriptions`** — output contains all 4 category description strings
2. **`test_detailed_help_has_all_category_headers`** — output contains all category headers
3. **`test_detailed_help_has_all_commands`** — output contains all command names
4. **`test_detailed_help_column_alignment`** — descriptions align to same column
5. **`test_detailed_help_has_footer`** — contains "Run 'mcp-coder <command> --help'..."
6. **`test_execute_help_returns_success`** — update: check for new header text
7. **Remove**: `test_get_usage_examples_has_examples`, `test_help_text_consistency`, `test_prompt_command_documentation`, `test_get_help_text_without_examples`, tests referencing `include_examples` param or `"COMMANDS:"` section

## LLM Prompt

```
Implement Step 2 of issue #565 (see pr_info/steps/summary.md and pr_info/steps/step_2.md).

TDD approach:
1. Read the current test_help.py and help.py files
2. Remove tests for get_usage_examples() and the include_examples parameter
3. Add/update tests for the new get_help_text() (detailed output with category descriptions)
4. Rewrite get_help_text() to render from CATEGORIES (with category descriptions)
5. Remove get_usage_examples()
6. Update execute_help() to call get_help_text() without parameters
7. Update the get_help_text() call in main.py handle_no_command() to use no parameters (temporary — step 3 switches to compact)
8. Run all three code quality checks (pylint, pytest, mypy) and fix any issues
9. Commit when all checks pass
```
