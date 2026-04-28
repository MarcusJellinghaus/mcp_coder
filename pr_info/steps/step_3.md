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
* Add a small unit test for `_print_project_section` similarly checking
  that `format_code` and `check_type_hints` align (the current code mixes
  18- and 20-wide which this step normalises to 22).

## Verification

Run pylint, pytest, mypy.
