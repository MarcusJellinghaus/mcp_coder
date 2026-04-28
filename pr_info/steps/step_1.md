# Step 1 — Add Helpers, Bump `_pad`, Migrate `_format_section`

## LLM Prompt

> Read `pr_info/steps/summary.md` for context. Then implement Step 1 as
> described in `pr_info/steps/step_1.md`. Follow TDD: update/add the tests
> listed under **Tests** first, watch them fail, then make them pass by
> implementing the production changes. Produce exactly one commit.

## WHERE

* **Source:** `src/mcp_coder/cli/commands/verify.py`
* **Tests:** `tests/cli/commands/test_verify_format_section.py`

## WHAT

Add to `verify.py` (near the existing `STATUS_SYMBOLS` block):

```python
_MARKER_SLOT_WIDTH: int = max(len(v) for v in STATUS_SYMBOLS.values())
_LABEL_WIDTH: int = 22  # exact fit for "workspace / PYTHONPATH"; longer labels overrun


def _format_row(label: str, marker: str, value: str, *, indent: int) -> str:
    """Render a labeled tabular row.

    Empty marker is padded to the marker slot width so the value column
    starts at the same horizontal position regardless of marker presence.
    Labels longer than _LABEL_WIDTH overrun (no truncation) — this is
    accepted; keep labels concise.
    """


def _format_freeform_row(marker: str, value: str, *, indent: int) -> str:
    """Render a label-less row (CONFIG section free-form hints/values).

    Used when the row has no key/label component; avoids wasting 22 chars
    of leading whitespace.
    """
```

Update existing `_pad`: change the padding target from **60** to **75**.

Migrate `_format_section` to use `_format_row` for:
* top-level rows (current `f"  {label:<20s} {symbol} {value}"`),
* branch-protection child rows (current 4-space indent),
* `strict_mode` no-marker branch (currently passes empty marker via raw f-string).

The install-hint continuation line (`-> {hint}` at column 27) stays as-is —
it is not a tabular row.

## HOW

* No new imports required; helpers are pure string formatting.
* Helpers are private (`_`-prefixed); no `__all__` change.
* Branch-protection children indent is `4`; top-level rows is `2`.

## ALGORITHM (`_format_row`)

```
prefix = " " * indent
label_field = f"{label:<{_LABEL_WIDTH}s}"
marker_field = f"{marker:<{_MARKER_SLOT_WIDTH}s}"
return f"{prefix}{label_field} {marker_field} {value}".rstrip()
```

## ALGORITHM (`_format_freeform_row`)

```
prefix = " " * indent
if marker:
    return f"{prefix}{marker:<{_MARKER_SLOT_WIDTH}s} {value}".rstrip()
return f"{prefix}{value}".rstrip()
```

## DATA

Both helpers return `str` (a single line, no trailing newline).
`_format_section` continues to return `str` (joined multi-line).
`_pad` continues to return `str`.

## Tests

In `tests/cli/commands/test_verify_format_section.py`:

* **Update `TestPadHeader`** — change `60` to `75` in the three assertions
  (`test_short_title_padded_to_60`, `test_exact_60_title_no_extra_padding`,
  `test_long_title_not_truncated`). Rename the methods to reflect 75 if
  desired (optional).
* **Update `TestFormatSection`** — string assertions like
  `"Claude CLI Found     [OK] YES"` become `"Claude CLI Found       [OK]   YES"`
  (label padded to 22, then a space, marker padded to 6, then a space, then
  value). Recompute the spacing for every pinned string.
* **Update `TestBranchProtectionNesting`** — assertions like
  `"  Auto-delete branches [OK] enabled"` become the new form. Strict-mode
  test now expects the value column to align with sibling rows even though
  no marker is rendered.
* **Add new test class `TestFormatRowHelpers`** with cases:
  - `_format_row("api_key", "[OK]", "configured", indent=2)` →
    `"  api_key                 [OK]   configured"` (verify exact spacing).
  - `_format_row("endpoint", "", "not configured", indent=2)` — value column
    starts at the same index as the previous case.
  - `_format_row` with `[WARN]` and `[ERR]` — value columns identical.
  - `_format_freeform_row("[WARN]", "stuff", indent=4)` — no label slot.
  - `_format_freeform_row("", "free text", indent=4)` — pure indented value.

## Verification

Run all three checks; all must pass before commit:

```
mcp__tools-py__run_pylint_check
mcp__tools-py__run_mypy_check
mcp__tools-py__run_pytest_check  (extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration and not langchain_integration"])
```
