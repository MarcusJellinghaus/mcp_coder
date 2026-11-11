# Step 2 — Row model and per-section width formula in `verify_formatting`

## LLM prompt

> Read `pr_info/steps/summary.md` (sections 1 and 2) and this file. Implement
> step 2 only: add the `Row` / `Line` types, `_hint`, `_section_label_width`,
> and change `_format_row_prefix` / `_format_row` to the new column rule.
> Do not create `verify_render.py` yet and do not change any formatter's return
> type. Tests first, then code. Run pylint, pytest (fast unit filter,
> `-n auto`), mypy; all must pass. One commit.

## WHERE

- `src/mcp_coder/cli/commands/verify_formatting.py`
- `tests/cli/commands/conftest.py`
- `tests/cli/commands/test_verify_format_pad.py`
- callers of `_expected_value_column`: `test_verify.py` (lines ~399, ~424,
  ~740–741), `test_verify_alignment.py`, `test_verify_orchestration_env.py`
  (~195), `test_verify_sections_config.py` (~200, ~309)

## WHAT

```python
class Row(NamedTuple):
    """One tabular row; label and/or marker may be empty."""
    label: str
    marker: str
    value: str
    indent: int = 2
    wrap: bool = False

Line = Row | str   # str = freeform line (group header, blank, notice), printed as-is

def _hint(text: str) -> Row:
    """Hint/continuation line: starts at the section's value column."""
    return Row("", "", text)

def _section_label_width(lines: Iterable[Line]) -> int:
    """max(_LABEL_WIDTH, len(label) + indent - 2) over the Row items."""

def _format_row_prefix(label: str, marker: str, *, indent: int,
                       label_width: int = _LABEL_WIDTH) -> str: ...

def _format_row(label: str, marker: str, value: str, *, indent: int,
                label_width: int = _LABEL_WIDTH) -> str: ...
```

`label_width` on `_format_row` stays **for this step only** (three callers
still pass it; step 6 removes it).

## ALGORITHM

```
_section_label_width(lines):
    return max([_LABEL_WIDTH, *(len(r.label) + r.indent - 2 for r in lines if isinstance(r, Row))])
_format_row_prefix(label, marker, indent, label_width):
    field = label_width - (indent - 2)
    return " " * indent + label.ljust(field) + " " + marker.ljust(_MARKER_SLOT_WIDTH) + " "
_format_row(label, marker, value, indent, label_width):
    width = max(label_width, _section_label_width([Row(label, marker, value, indent)]))
    return (_format_row_prefix(label, marker, indent=indent, label_width=width) + value).rstrip()
```

`_VALUE_COLUMN_INDENT` keeps its definition (still 32) until step 5.
Update the `_LABEL_WIDTH` comment ("minimum label width; sections widen
automatically") and the `_format_row_prefix` docstring (no more overrun).

## Tests (write first)

`test_verify_format_pad.py`:
- `_expected_prefix` helper uses the new rule (field = `label_width - (indent - 2)`).
- `_format_row(..., indent=4)` and `indent=6` with a short label put the value
  at column 32 (same as indent 2).
- A label longer than the field widens instead of overrunning:
  `_format_row("x" * 30, "[OK]", "v", indent=2).index("v") == 2 + 30 + 1 + 6 + 1`;
  at indent 4 a 21-char label gives value column 33.
- Prefix length is `label_width + 10` for indents 2, 4, 6.
- `_section_label_width`: `[]` → 22; ignores `str` items; `Row("a"*21, "", "", 4)` → 23.
- `_hint("-> x")` rendered via `_format_row(*_hint(...)[:3], indent=2)` starts the
  text at column 32.
- Keep the existing `label_width=30` tests (parameter still exists).

`conftest.py`:
- `_expected_value_column(*, label_width: int = _LABEL_WIDTH) -> int` — drop the
  `indent` parameter; returns `2 + label_width + 1 + _MARKER_SLOT_WIDTH + 1`.
  Update the docstring layout comment.
- Update every caller: `_expected_value_column(indent=2)` →
  `_expected_value_column()`; `_expected_value_column(2, label_width=X)` →
  `_expected_value_column(label_width=X)`; in `test_verify.py` the
  `assert expected_col == _VALUE_COLUMN_INDENT + 2` becomes
  `assert expected_col == _VALUE_COLUMN_INDENT` (indent 4 now shares column 32).
  In `test_verify_alignment.py` replace `_expected_value_column(indent)` with
  `_expected_value_column()`.

## DATA

- `Row` is a `NamedTuple` (immutable, cheap, unpackable).
- `Line` is a module-level type alias usable at runtime (Python ≥ 3.11).
