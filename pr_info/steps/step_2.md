# Step 2: Make `status_label` optional and add no-args label listing

> **Reference**: See `pr_info/steps/summary.md` for full context on issue #595.

## Goal

When `set-status` is called without arguments, print available status labels and exit 0. This is the user-facing feature from the issue.

## WHERE

- `src/mcp_coder/cli/parsers.py` — make `status_label` optional
- `src/mcp_coder/cli/commands/set_status.py` — add no-args early return, update docstring
- `tests/cli/commands/test_set_status.py` — add no-args test

## WHAT

### Parser change (parsers.py)

```python
# WAS:
set_status_parser.add_argument(
    "status_label",
    help="Status label to set (e.g., status-05:plan-ready)",
)

# NOW:
set_status_parser.add_argument(
    "status_label",
    nargs="?",
    default=None,
    help="Status label to set (e.g., status-05:plan-ready)",
)
```

### No-args path (set_status.py, inside `execute_set_status`)

Early return block added before existing Step 1 (resolve project dir):

```python
if args.status_label is None:
    # ... load config, print labels, return 0
```

### Docstring update

Add to `execute_set_status()` docstring: "When called without a status_label, prints available labels and exits 0."

## HOW

- `execute_set_status()`: Insert no-args check at top of try block, before `resolve_project_dir`
- Best-effort config loading: try `resolve_project_dir(args.project_dir)` → `get_labels_config_path(project_dir)`, on `ValueError`/`FileNotFoundError`/`OSError` fall back to `get_labels_config_path(None)`
- Uses `format_status_labels()` from Step 1 and `load_labels_config()` (already imported)

## ALGORITHM — no-args path in `execute_set_status`

```
if args.status_label is None:
    try:
        project_dir = resolve_project_dir(args.project_dir)
        config_path = get_labels_config_path(project_dir)
    except (ValueError, FileNotFoundError, OSError):
        config_path = get_labels_config_path(None)
    labels_config = load_labels_config(config_path)
    print(format_status_labels(labels_config))
    return 0
```

## DATA

- **Input**: `args.status_label is None`
- **Output to stdout**: Formatted label table (same as `format_status_labels()` output)
- **Return**: `0`

## Tests (TDD)

### New test

`test_execute_set_status_no_args_shows_labels`:
- Set `args.status_label = None`
- Mock `resolve_project_dir`, `get_labels_config_path`, `load_labels_config`
- Assert returns 0
- Assert stdout contains "Available status labels"
- Assert `is_working_directory_clean` was NOT called (no side effects)
- Assert `IssueManager` was NOT instantiated

### New test

`test_execute_set_status_no_args_fallback_config`:
- Set `args.status_label = None`
- Mock `resolve_project_dir` to raise `ValueError`
- Assert returns 0 (falls back to bundled config)
- Assert `get_labels_config_path` called with `None`

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_2.md for full context.

Implement Step 2 of issue #595: Make status_label optional and add no-args label listing.

1. Write tests first (TDD):
   - In tests/cli/commands/test_set_status.py: add test_execute_set_status_no_args_shows_labels and test_execute_set_status_no_args_fallback_config

2. Implement:
   - In src/mcp_coder/cli/parsers.py: change status_label to nargs="?", default=None
   - In src/mcp_coder/cli/commands/set_status.py: add no-args early return in execute_set_status() with best-effort project dir resolution
   - Update execute_set_status() docstring to mention no-args behavior

3. Run all three code quality checks. Fix any issues.
4. Commit with message: "feat: show available labels when set-status called without args (#595)"
```
