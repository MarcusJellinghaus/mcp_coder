# Step 3 — Migrate `_print_environment_section` and `_print_project_section`

> **Note on line numbers:** all `verify.py:NNN` references in this step
> point at the file at branch HEAD before Step 1 lands. Locate the target
> by function name when implementing.

## LLM Prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_3.md`. Steps 1
> and 2 are already merged. Follow TDD: update or add tests first, then
> migrate the two `_print_*` functions. Produce exactly one commit.

## WHERE

* **Source:** `src/mcp_coder/cli/commands/verify.py`
* **Tests:** `tests/cli/commands/test_verify_command.py` (string-pinned
  assertions on environment/project rows, if any).
  Add a new minimal test class in `test_verify_format_section.py` if no
  unit-level test exists for these `_print_*` functions yet.
* **Shared test helpers (new):** `tests/cli/commands/conftest.py` —
  introduce `_expected_value_column(indent: int, *, label_width: int =
  _LABEL_WIDTH) -> int` and `_assert_value_at_column(line: str,
  expected_col: int) -> None`. Both helpers are reused by Step 6's
  per-formatter and smoke-test layers (introduced here in Step 3 in
  conftest.py; Step 6 reuses).

## WHAT

In `_print_environment_section` (`verify.py:79-102`), replace every
`print(f"  {label:<20s} {value}")` and the package-version loop with
`print(_format_row(label, "", value, indent=2))` — i.e. **no marker**.

The `[ERR] not installed` package-version case currently embeds the marker
inside the value string. Migration: split it — pass `marker=symbols['failure']`
and `value="not installed"` so the marker lands in the marker slot instead
of being part of the value.

```python
try:
    value = version(pkg)
    print(_format_row(pkg, "", value, indent=2))
except PackageNotFoundError:
    print(_format_row(pkg, STATUS_SYMBOLS["failure"], "not installed", indent=2))
```

In `_print_project_section` (`verify.py:104-131`), replace:
* the four top-level `:<20s` rows (`pyproject.toml`, `Language`).
* the four `:<18s` indented rows (`format_code`, `check_type_hints`).

The `[Python]` group header (`print("  [Python]")`) stays unchanged — it is
a header, not a row.

For the `format_code` / `check_type_hints` rows, the second arm currently
spans two lines (`f-string` + continuation inside a single `print()` call).
Migrate to a single `_format_row` call:

```python
if config.format_code:
    print(_format_row("format_code", symbols["success"], "enabled", indent=4))
else:
    print(_format_row("format_code", symbols["warning"],
                      "not configured (default: disabled)", indent=4))
```

## HOW

* `STATUS_SYMBOLS` is already imported at module scope; `_format_row`
  exists from Step 1.
* No signature changes.
* Introduce the shared alignment-test helpers in
  `tests/cli/commands/conftest.py`. Pin these exact implementations —
  Step 6 reuses them as-is (do NOT re-define in step_6.md):

  ```python
  def _expected_value_column(indent: int, *, label_width: int = _LABEL_WIDTH) -> int:
      """Return the 0-indexed column where the value SHOULD begin, derived
      purely from layout constants.

      Layout: [indent][label.ljust(label_width)][space][marker.ljust(_MARKER_SLOT_WIDTH)][space][value]
      The expected value column is indent + label_width + 1 + _MARKER_SLOT_WIDTH + 1.
      For test parametrization, callers should pass the section's label_width
      explicitly when the section uses a dynamic width (e.g. MCP CONFIG WARNINGS).

      NOTE: this does NOT inspect the line — it computes the contract from
      constants only. Use `_assert_value_at_column` to verify a real line
      against this expected column.
      """
      return indent + label_width + 1 + _MARKER_SLOT_WIDTH + 1


  def _assert_value_at_column(line: str, expected_col: int) -> None:
      """Assert that `line` has a non-whitespace character at `expected_col`
      and a whitespace character at `expected_col - 1`. Catches drift in both
      directions."""
      assert expected_col >= 1, f"expected_col must be >= 1; got {expected_col}"
      assert expected_col < len(line), (
          f"line shorter than expected value column {expected_col}: {line!r}"
      )
      assert line[expected_col - 1].isspace(), (
          f"prefix overflowed past col {expected_col - 1} (expected space): {line!r}"
      )
      assert not line[expected_col].isspace(), (
          f"value missing at col {expected_col} (expected non-space): {line!r}"
      )
  ```

  The `assert expected_col >= 1` precondition guards against negative-index
  wraparound in `line[expected_col - 1]` — without it, a caller passing
  `expected_col=0` would silently read the last character of the line via
  Python's negative-index semantics.

## ALGORITHM

Direct substitution.

## DATA

Both functions still return `None` (they `print` directly).

## Tests

* If `test_verify_command.py` (or any other file) has assertions that pin
  the literal `:<20s`/`:<18s` output for environment or project rows,
  update them to the new label width 22 + marker slot 6.
* Add a small unit test exercising `_print_environment_section` via
  `capsys` (or `capfd`) — assert that:
  - the `Python version` row's value column starts at the same index as
    the `mcp-coder` package-version row's value column (cross-row
    alignment within the section),
  - rows without a marker still align with the [ERR] not-installed row.

  Use the shared `_assert_value_at_column(line, expected_col)` and
  `_expected_value_column(indent)` helpers from
  `tests/cli/commands/conftest.py` (introduced here in Step 3; Step 6
  reuses them in its Layer 1 / Layer 2 layers). Derive `expected_col`
  via the helper:

  ```python
  from mcp_coder.cli.commands.verify import (
      _LABEL_WIDTH, _MARKER_SLOT_WIDTH, _VALUE_COLUMN_INDENT,
  )
  from tests.cli.commands.conftest import (
      _assert_value_at_column, _expected_value_column,
  )

  expected_col = _expected_value_column(indent=2)
  # (equivalent to _VALUE_COLUMN_INDENT)
  for line in (python_version_line, mcp_coder_line):
      _assert_value_at_column(line, expected_col)
  ```

  The helper inspects `line[expected_col - 1]` (must be whitespace) and
  `line[expected_col]` (must be non-whitespace), so the test catches
  both prefix-overflow and value-too-short drift on each row.

* Add a small unit test for `_print_project_section` similarly checking
  that `format_code` and `check_type_hints` align (the current code mixes
  18- and 20-wide which this step normalises to 22). Use the same
  `_assert_value_at_column` helper from `conftest.py`, with
  `expected_col = _expected_value_column(indent=4)` for the indent=4
  sub-rows (equivalent to `_VALUE_COLUMN_INDENT + 2`).
* **Pinned exact-string assertion (regression guard).** Add at least one
  assertion that pins the post-migration output for an installed-package
  row, e.g.:

  ```python
  expected = (
      f"  {'mcp-coder'.ljust(_LABEL_WIDTH)} "
      f"{''.ljust(_MARKER_SLOT_WIDTH)} 1.2.3"
  )
  assert _format_row("mcp-coder", "", "1.2.3", indent=2) == expected
  ```

  The point: **derive the expected string from the constants** (don't
  hand-count spaces) and pin it so a future bug that uniformly shifts
  the value column gets caught. Value `"1.2.3"` is non-empty so rstrip
  is a no-op — the assertion stays a deterministic string check.

## Verification

Run pylint, pytest, mypy.
