# Step 1: `--from-status` Flag on `gh-tool set-status`

**Commit message:** `feat: add --from-status precondition flag to gh-tool set-status (#713)`

> **LLM Prompt:** Read `pr_info/steps/summary.md` for context. Implement Step 1: add the `--from-status LABEL` flag to `gh-tool set-status`. This flag makes set-status a conditional operation — it only applies the new label if the issue's current status matches `--from-status`. On mismatch, it exits 0 with an OUTPUT-level skip message. The flag value is validated against `labels.json`. Write tests first (TDD), then implement. Run all three code quality checks after changes.

## WHERE

- `tests/cli/commands/test_set_status.py` — new test class `TestFromStatusFlag`
- `src/mcp_coder/cli/gh_parsers.py` — add `--from-status` argument
- `src/mcp_coder/cli/commands/set_status.py` — validation + precondition check

## WHAT

### Parser change (`gh_parsers.py`)

Add one argument to the existing `set_status_parser`:

```python
set_status_parser.add_argument(
    "--from-status",
    type=str,
    default=None,
    help="Only update if current status matches this label (precondition guard)",
)
```

### Logic changes (`set_status.py`)

**Modified function — `_update_issue_labels`:**

```python
def _update_issue_labels(
    manager: IssueManager,
    issue_number: int,
    status_label: str,
    status_labels: set[str],
    from_status: Optional[str] = None,   # NEW parameter
) -> Tuple[bool, Optional[str]]:
```

**Modified function — `execute_set_status`:**

Add validation of `args.from_status` (after existing label validation in Step 2), and pass it through to `_update_issue_labels`.

### No new functions needed.

## HOW

### Integration points

- `args.from_status` is populated by argparse (defaults to `None`)
- Validation reuses existing `validate_status_label()` — same approach as the positional arg
- Precondition check reuses the existing `manager.get_issue()` call inside `_update_issue_labels` — no extra API round-trip
- Skip message uses `logger.log(OUTPUT, ...)` — same channel as success message

## ALGORITHM

### Precondition check (inside `_update_issue_labels`, after `get_issue()`):

```
if from_status is not None:
    current_status_labels = current_labels & status_labels
    current = next(iter(current_status_labels), None)
    current_display = current if current else "<none>"
    if current != from_status:
        logger.log(OUTPUT, skip_message)
        return (True, None)  # success, no error — caller exits 0
# ... proceed with existing label update logic
```

### Validation (inside `execute_set_status`, after Step 2 existing validation):

```
if args.from_status is not None:
    is_valid, error_msg = validate_status_label(args.from_status, labels_config)
    if not is_valid:
        logger.error(error_msg)
        return 1
```

## DATA

### Skip message format (OUTPUT level)

```
Skipped set-status to 'status-06f:implementing-failed': current label is 'status-07:implemented', expected 'status-06:implementing'
```

No-status-label case:

```
Skipped set-status to 'status-06f:implementing-failed': current label is '<none>', expected 'status-06:implementing'
```

### Return values — unchanged

`_update_issue_labels` still returns `Tuple[bool, Optional[str]]`. On precondition skip, it returns `(True, None)` — treated as success by the caller.

## TESTS (`tests/cli/commands/test_set_status.py`)

New class `TestFromStatusFlag` with these test methods:

1. **`test_from_status_matching_updates_label`** — current label matches `--from-status` → update proceeds, exit 0
2. **`test_from_status_mismatch_skips_with_message`** — current label differs → no `set_labels` call, OUTPUT skip message, exit 0
3. **`test_from_status_no_current_label_skips`** — issue has no status label → no-op, `<none>` in skip message, exit 0
4. **`test_from_status_invalid_value_returns_error`** — `--from-status` value not in `labels.json` → exit 1
5. **`test_from_status_combined_with_force_and_issue`** — `--from-status` + `--force` + `--issue` all work together
6. **`test_from_status_no_extra_api_call`** — verify `get_issue` is called exactly once (reuses existing fetch)

All tests follow the existing pattern: `@patch` decorators on external dependencies, `argparse.Namespace` for args, `caplog` for log assertions.
