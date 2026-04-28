# Step 1 — Add Helpers, Bump `_pad`, Migrate `_format_section`

> **Note on line numbers:** all `verify.py:NNN` references in this step
> point at the file at branch HEAD before Step 1 lands. When implementing,
> locate the target by function name rather than relying on the line
> number — Step 1's own edits will shift everything below.

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
_LABEL_WIDTH: int = 22  # global minimum label slot; sections may widen via label_width=


def _format_row_prefix(
    label: str, marker: str, *, indent: int, label_width: int = _LABEL_WIDTH
) -> str:
    """Render the column-aligned prefix portion of a tabular row.

    Returns ``indent + label_field + " " + marker_field + " "`` WITHOUT
    rstrip — the trailing space and the full marker-slot padding are
    preserved. Used directly by callers that need the prefix without a
    value (e.g. `textwrap.wrap` continuation indent).

    Empty marker is padded to ``_MARKER_SLOT_WIDTH`` so the value column
    starts at the same horizontal position regardless of marker presence.
    Labels longer than ``label_width`` overrun (no truncation) — keep
    labels concise, or pass a wider ``label_width`` for sections whose
    labels are known to exceed the default.
    """
    return f"{' ' * indent}{label:<{label_width}s} {marker:<{_MARKER_SLOT_WIDTH}s} "


def _format_row(
    label: str, marker: str, value: str, *, indent: int, label_width: int = _LABEL_WIDTH
) -> str:
    """Render a tabular row (labeled or label-less).

    Composed on top of ``_format_row_prefix``; appends the value and
    rstrips trailing whitespace. ``value`` is expected to be non-empty
    for tabular rows; the rstrip is intentional to drop any incidental
    trailing whitespace from ``value``. For prefix-only use cases (e.g.
    `textwrap.wrap` continuation), call ``_format_row_prefix`` directly
    instead — calling ``_format_row`` with ``value=""`` would rstrip the
    trailing space the prefix needs.

    Label-less rows (CONFIG section free-form hints / parse errors /
    multi-word values that don't split into key/value) pass ``label=""``.
    The empty label is padded to ``label_width`` so the value column
    aligns with neighbouring labeled rows — this is the issue's central
    invariant.
    """
    return (
        _format_row_prefix(label, marker, indent=indent, label_width=label_width)
        + value
    ).rstrip()


# Derived constant — position of the first value-column character at indent=2.
# Used by free-form continuation lines (e.g. install-hint) so they line up
# under the value column without hand-counting spaces.
_VALUE_COLUMN_INDENT: int = len(_format_row_prefix("", "", indent=2))
```

Update existing `_pad`: change the padding target from **60** to **75**.

Migrate `_format_section` to use `_format_row` for:
* top-level rows (current `f"  {label:<20s} {symbol} {value}"`),
* branch-protection child rows (current 4-space indent),
* `strict_mode` no-marker branch (currently passes empty marker via raw f-string).

The install-hint continuation line currently sits at column 27 (matching
the old 20+marker layout). Update it to align under the new value column.
Use the derived `_VALUE_COLUMN_INDENT` constant defined above — never
hard-code the integer (single source of truth wins; if `_LABEL_WIDTH`
or `_MARKER_SLOT_WIDTH` ever changes, the install-hint follows along
for free):

```python
lines.append(f"{' ' * _VALUE_COLUMN_INDENT}-> {entry['install_hint']}")
```

Note: preserves the existing list-builder pattern in `_format_section`;
do not switch to `print`.

For `indent=2, _LABEL_WIDTH=22, _MARKER_SLOT_WIDTH=6`, the resulting
indent is `2 + 22 + 1 + 6 + 1 = 32`. This is a deliberate cosmetic
update tied to the wider value column — not a separate refactor. The
install-hint line itself remains a freeform continuation, not a
tabular row.

## HOW

* No new imports required; helpers are pure string formatting.
* Helpers are private (`_`-prefixed); no `__all__` change.
* Branch-protection children indent is `4`; top-level rows is `2`.

## ALGORITHM (`_format_row_prefix`)

```
return f"{' ' * indent}{label:<{label_width}s} {marker:<{_MARKER_SLOT_WIDTH}s} "
# NO rstrip; trailing space and full marker-slot padding preserved.
```

## ALGORITHM (`_format_row`)

```
return (_format_row_prefix(label, marker, indent=indent, label_width=label_width)
        + value).rstrip()
```

`_format_row` handles both labeled and label-less rows — call it with
`label=""` for the latter. Verification: with `label="", marker="[WARN]",
indent=2`, `_format_row_prefix` produces
`"  " + "".ljust(22) + " " + "[WARN]".ljust(6) + " "`, putting the value
character at column `2 + 22 + 1 + 6 + 1 = 32` — identical to a labeled
row's value column.

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
* **Add new test class `TestFormatRowHelpers`** with cases. **Important:**
  expected strings in alignment tests should be constructed via
  `f"{indent_pad}{label.ljust(_LABEL_WIDTH)} {marker.ljust(_MARKER_SLOT_WIDTH)} {value}".rstrip()`
  (or an equivalent helper) rather than hard-coded with hand-counted
  spaces — this keeps the tests aligned with whatever the constants
  evaluate to and prevents off-by-one bugs when reading the diff.
  - `_format_row("api_key", "[OK]", "configured", indent=2)` — derive the
    expected string from the constants and assert equality (do NOT
    hand-count spaces); also assert the value substring `"configured"`
    starts at column `2 + _LABEL_WIDTH + 1 + _MARKER_SLOT_WIDTH + 1 = 32`.
  - `_format_row("endpoint", "", "not configured", indent=2)` — value column
    starts at the same index as the previous case (32).
  - `_format_row` with `[WARN]` and `[ERR]` — value columns identical.
  - **Label-less row (parametrized)** —
    `_format_row("", "[WARN]", "value", indent=2)` produces a row whose
    value substring `"value"` starts at index `32`. Parameterize over
    `[OK]`, `[WARN]`, `[ERR]` and assert each lands at the same column.
    This is the central invariant that fulfills the issue title — a
    label-less row aligns at the same value column as a labeled row.
  - **Prefix length invariant** — derive expected length from constants:

    ```python
    assert len(_format_row_prefix("x", "[OK]", indent=2)) == 2 + _LABEL_WIDTH + 1 + _MARKER_SLOT_WIDTH + 1
    # equivalently: == _VALUE_COLUMN_INDENT
    ```

    `[WARN]`/`[ERR]` produce equal-length prefixes; the test should
    parameterize over the three markers and assert the lengths match.
    Note: expected lengths derive from the layout formula; do not
    hand-count spaces in the test.
  - **Composition contract** — for any non-empty `value` not starting/ending
    with whitespace,
    `_format_row(label, marker, value, indent=2)` ==
    `(_format_row_prefix(label, marker, indent=2) + value).rstrip()`.
  - **Custom `label_width`** — derive expected length from constants:

    ```python
    assert len(_format_row_prefix("x", "[OK]", indent=2, label_width=30)) == 2 + 30 + 1 + _MARKER_SLOT_WIDTH + 1
    ```

    `_format_row("very long label name", "[OK]", "v", indent=2, label_width=30)`
    produces a value column at index `2 + 30 + 1 + _MARKER_SLOT_WIDTH + 1`.
    Note: expected lengths derive from the layout formula; do not
    hand-count spaces in the test.

## Verification

Run all three checks; all must pass before commit:

```
mcp__tools-py__run_pylint_check
mcp__tools-py__run_mypy_check
mcp__tools-py__run_pytest_check  (extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration and not langchain_integration"])
```
