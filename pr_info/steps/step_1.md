# Step 1: `--from-status` Flag on `gh-tool set-status`

**Commit message:** `feat(set-status): add --from-status precondition flag to gh-tool set-status (#713)`

> **LLM Prompt:** Read `pr_info/steps/summary.md` for context. Implement Step 1: add the `--from-status LABEL` flag to `gh-tool set-status`. This flag makes set-status a conditional operation — it only applies the new label if the issue's current status matches `--from-status`. On mismatch, it exits 0 with an OUTPUT-level skip message. The flag value is validated against `labels.json`. Write tests first (TDD), then implement. Run all five code quality checks (pylint, pytest, mypy, lint-imports, vulture) after changes.

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
) -> Tuple[bool, Optional[str], bool]:
    # NEW: 3-tuple — (success, error, skipped)
    # `skipped=True` means the precondition did not match and no label change
    # was made. The caller must NOT emit the "Updated issue" log line in that case.
```

**Modified function — `execute_set_status`:**

1. Add validation of `args.from_status` against the same `labels.json` used for the positional `status_label` (reuse the existing `validate_status_label` helper and load path).
2. Reject `--from-status` when the positional `status_label` is missing. Because `nargs="?"`, argparse will NOT naturally reject `set-status --from-status foo`; add an explicit post-parse check that errors out (argparse-style error / non-zero exit) when `args.from_status is not None and args.status_label is None`.
3. Pass `from_status` through to `_update_issue_labels`.
4. On the returned `skipped=True` path, do NOT log the "Updated issue #X to Y" success message — only the OUTPUT-level skip message emitted inside `_update_issue_labels` should appear.

### No new functions needed.

## HOW

### Integration points

- `args.from_status` is populated by argparse (defaults to `None`)
- Validation reuses existing `validate_status_label()` — same approach as the positional arg
- Precondition check reuses the existing `manager.get_issue()` call inside `_update_issue_labels` — no extra API round-trip
- Skip message uses `logger.log(OUTPUT, ...)` — same channel as success message

## ALGORITHM

### Precondition check (inside `_update_issue_labels`)

**Placement:** the precondition check goes inside `_update_issue_labels` **after** the existing `issue_data["number"] == 0` error check and **after** `current_labels = set(issue_data["labels"])` is computed. It reuses the existing single `get_issue()` call — no extra GitHub API round-trip.

```
if from_status is not None:
    # Note: compute_new_labels already enforces the single-status-label
    # invariant (at most one status-* label on an issue at a time), so
    # current_status_labels has 0 or 1 element.
    current_status_labels = current_labels & status_labels
    current = next(iter(current_status_labels), None)
    current_display = current if current else "<none>"
    if current != from_status:
        logger.log(OUTPUT, skip_message)
        # On the rescue path the watchdog passes --force; the skip path
        # therefore never warns about a dirty working directory. This is
        # intentional — --from-status is a rescue-only flag.
        return (True, None, True)  # success, no error, skipped=True
# ... proceed with existing label update logic, returning (True, None, False) on success
```

### Validation (inside `execute_set_status`)

`--from-status` is validated against the same project `labels.json` that the positional `status_label` uses — reuse the same `validate_status_label` helper / load path:

```
if args.from_status is not None and args.status_label is None:
    # Positional is nargs="?" so argparse does not catch this combo.
    parser.error("--from-status requires a positional status_label")

if args.from_status is not None:
    is_valid, error_msg = validate_status_label(args.from_status, labels_config)
    if not is_valid:
        logger.error(error_msg)
        return 1
```

### Caller handling of the skip path

```
success, error, skipped = _update_issue_labels(...)
if success and not skipped:
    logger.log(OUTPUT, f"Updated issue #{issue_number} to {status_label}")
# On skipped=True the OUTPUT-level skip message was already logged inside
# _update_issue_labels; do NOT log "Updated" here.
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

### Return values — updated

`_update_issue_labels` now returns `Tuple[bool, Optional[str], bool]` — `(success, error, skipped)`. On precondition skip, it returns `(True, None, True)` — treated as success by the caller, but the caller suppresses the "Updated issue" log line. On normal success it returns `(True, None, False)`. Existing tests that assert on the success path must be updated to unpack the 3-tuple.

## TESTS (`tests/cli/commands/test_set_status.py`)

New class `TestFromStatusFlag` with these test methods:

1. **`test_from_status_matching_updates_label`** — current label matches `--from-status` → update proceeds, exit 0
2. **`test_from_status_mismatch_skips_with_message`** — current label differs → no `set_labels` call, OUTPUT skip message, exit 0
3. **`test_from_status_no_current_label_skips`** — issue has no status label → no-op, `<none>` in skip message, exit 0
4. **`test_from_status_invalid_value_returns_error`** — `--from-status` value not in `labels.json` → exit 1
5. **`test_from_status_combined_with_force_and_issue`** — `--from-status` + `--force` + `--issue` all work together
6. **`test_from_status_no_extra_api_call`** — verify `get_issue` is called exactly once (reuses existing fetch)
7. **`test_skip_does_not_log_updated_message`** — on the skip path, capture stdout/log (`caplog` + the OUTPUT level) and assert the "Updated issue #X to Y" line is NOT emitted, only the skip message is
8. **`test_from_status_without_positional_label_errors`** — invoking `set-status --from-status foo` with no positional `status_label` exits non-zero with an argparse-style error
9. **`test_from_status_force_dirty_wd_mismatch_skips_silently`** — `--from-status` + `--force` + dirty working directory + mismatched current label → exit 0, skip message printed, and NO dirty-working-directory warning is emitted (the skip path short-circuits before any dirty-wd check)

Existing tests that exercise the success path of `_update_issue_labels` must be updated for the new 3-tuple return shape (`success, error, skipped`).

All tests follow the existing pattern: `@patch` decorators on external dependencies, `argparse.Namespace` for args, `caplog` for log assertions.
