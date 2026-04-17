# Step 4: --initial-color CLI parameter

> See [summary.md](summary.md) for full context (Issue #798).

## Goal

Add `--initial-color` argument to the icoder CLI parser and wire it in `execute_icoder()` to set the prompt color at startup.

## LLM Prompt

```
Implement Step 4 of Issue #798 (see pr_info/steps/summary.md and pr_info/steps/step_4.md).
Add --initial-color CLI parameter following TDD. Write tests first, then implementation.
Run all three code quality checks after changes. Commit as one unit.
```

## WHERE

- `src/mcp_coder/cli/parsers.py` — add `--initial-color` argument
- `src/mcp_coder/cli/commands/icoder.py` — apply initial color after app_core creation
- `tests/icoder/test_cli_icoder.py` — add parser and wiring tests
- `docs/icoder/icoder.md` — add `/color` row to Slash Commands table (check if file exists first)
- `docs/cli-reference.md` — add `--initial-color` to icoder Options section (check if file exists first)

## WHAT

### Parser argument in `parsers.py` (`add_icoder_parser`)

```python
icoder_parser.add_argument(
    "--initial-color",
    type=str,
    default=None,
    metavar="COLOR",
    help="Set prompt border color at startup (named color or hex code)",
)
```

### Wiring in `execute_icoder()` (after `app_core` creation, before `ICoderApp`)

```python
initial_color = getattr(args, "initial_color", None)
if initial_color:
    error = app_core.set_prompt_color(initial_color)
    if error:
        logger.warning("Invalid --initial-color '%s': %s", initial_color, error)
```

## ALGORITHM

```
1. Parse --initial-color from args (default None)
2. If value provided, call app_core.set_prompt_color(value)
3. If set_prompt_color returns error string → logger.warning(), color stays default
4. If returns None → color is set, on_mount will apply it
```

## DATA

- `args.initial_color`: `str | None` — raw CLI value
- On invalid: warning logged, `prompt_color` remains `"#666666"`
- On valid: `prompt_color` updated before app starts, `on_mount` picks it up

## TESTS (in `tests/icoder/test_cli_icoder.py`)

```python
# Parser accepts --initial-color
def test_icoder_initial_color_flag(): ...
    # parser = create_parser()
    # args = parser.parse_args(["icoder", "--initial-color", "red"])
    # assert args.initial_color == "red"

# Default is None
def test_icoder_initial_color_default(): ...
    # args = parser.parse_args(["icoder"])
    # assert args.initial_color is None

# Valid --initial-color sets prompt_color on app_core
def test_execute_icoder_initial_color_applied(): ...
    # Capture app_core, verify prompt_color == "#ef4444" after execute_icoder with --initial-color red

# Invalid --initial-color logs warning, keeps default
def test_execute_icoder_initial_color_invalid_warns(): ...
    # Capture app_core + caplog, verify prompt_color == "#666666" and warning logged
```

## DOCUMENTATION

### WHERE

- `docs/icoder/icoder.md` — add `/color` to the Slash Commands table
- `docs/cli-reference.md` — add `--initial-color` to the icoder Options section

**Before editing, verify these files exist** using `mcp__workspace__search_files` or listing the docs directory. If a file doesn't exist, skip that doc update.

### WHAT

- In `icoder.md`: add a row `| /color [name\|hex] | Change prompt border color. No args lists available colors. |` to the Slash Commands table
- In `cli-reference.md`: add `--initial-color COLOR` to the icoder Options section with description: "Set prompt border color at startup (named color or hex code)"

## Commit message

```
feat(icoder): add --initial-color CLI parameter and docs (#798)
```
