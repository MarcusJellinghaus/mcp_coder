# Step 3 — Renderer and `SectionBuilder` (new `verify_render.py`)

## LLM prompt

> Read `pr_info/steps/summary.md` (section 3) and this file. Implement step 3
> only: create `src/mcp_coder/cli/commands/verify_render.py` with
> `_render_rows` and `SectionBuilder`, plus shared test helpers in
> `tests/cli/commands/conftest.py`. Nothing in production uses the new module
> yet. Tests first (new file `tests/cli/commands/test_verify_render.py`), then
> code. Run pylint, pytest (fast unit filter, `-n auto`), mypy,
> lint-imports and vulture; all must pass. One commit.

## WHERE

- new `src/mcp_coder/cli/commands/verify_render.py`
- new `tests/cli/commands/test_verify_render.py`
- `tests/cli/commands/conftest.py`

## WHAT

```python
# verify_render.py
"""Per-section renderer and section builder for the verify command.

Imports from verify_formatting only; verify_formatting never imports this module.
"""
logger = logging.getLogger(__name__)

def _render_rows(lines: Sequence[Line]) -> list[str]: ...

class SectionBuilder:
    def __init__(self) -> None: ...            # self._lines: list[Line] | None = None
    def open(self, title: str) -> None: ...
    def add(self, *lines: Line) -> None: ...
    def close(self) -> None: ...
    def section(self, title: str, lines: Iterable[Line]) -> None: ...
    def __enter__(self) -> "SectionBuilder": ...
    def __exit__(self, exc_type: type[BaseException] | None, *_rest: object) -> None: ...
```

## ALGORITHM

```
_render_rows(lines):
    width = _section_label_width(lines); out = []
    for item in lines:
        if isinstance(item, str): out.append(item); continue
        prefix = _format_row_prefix(item.label, item.marker, indent=item.indent, label_width=width)
        if item.wrap: out += textwrap.wrap(item.value, width=80, initial_indent=prefix, subsequent_indent=" " * len(prefix))
        else: out.append((prefix + item.value).rstrip())
    return out

open(title):  close(); print(_pad(title)); self._lines = []
add(*lines):  if self._lines is not None: extend; else for each: print(item if str else _format_row(item.label, item.marker, item.value, indent=item.indent))
close():      if None: return; lines, self._lines = self._lines, None; for l in _render_rows(lines): print(l)
section(t, lines): open(t); add(*lines); close()
__exit__(exc_type, ...):
    if exc_type is None: close(); return
    try: close()
    except Exception: logger.debug("could not flush verify section", exc_info=True)   # original exception propagates
```

`print` is called at write time (no stored stream), so `capsys` captures it.
`__exit__` returns `None` → exceptions are never suppressed.

## HOW

- Imports: `Line`, `Row`, `_format_row`, `_format_row_prefix`, `_pad`,
  `_section_label_width` from `.verify_formatting`; stdlib `logging`,
  `textwrap`, `collections.abc`.
- Check whether `tach.toml` / `.importlinter` enumerate the
  `mcp_coder.cli.commands.verify*` modules; if they do, register the new module
  the same way. If `run_lint_imports_check` or `run_tach_check` fails because of
  the new module and the fix is not a one-line registration, write one line to
  `pr_info/.blocked.txt` and stop.

## Tests (write first) — `tests/cli/commands/test_verify_render.py`

Renderer (`_render_rows`):
- width = max(22, longest label + indent offset): a 30-char label at indent 2
  puts every row's value at column 40.
- rows at indents 2/4/6 share the marker column and the value column.
- `_hint("-> do x")` starts at the value column (32 default; 40 when widened).
- empty-marker row and label-less row align with marker rows.
- `wrap=True` row: every output line ≤ 80 chars; continuation lines start at the
  value column; the joined text equals the original value.
- `str` items (`""`, `"  [Python]"`, `"  pip install x"`) are returned unchanged
  and do not widen the section.

Builder (`SectionBuilder`, use `capsys`):
- `open("A")` prints the `_pad("A")` header immediately; rows appear only after
  `close()`.
- opening a second section closes (renders) the first one first.
- a section with only `str` lines / no rows uses width 22 (a hint added in it
  starts at column 32).
- `add(Row(...))` with no section open prints immediately, equal to
  `_format_row(...)`; `add("text")` with no section open prints `text`.
- `close()` twice is a no-op the second time.
- `with SectionBuilder() as out: out.open("A"); out.add(row); raise RuntimeError`
  → `pytest.raises(RuntimeError)` and the row is in the captured output.
- flush failure during an exception does not mask it: patch
  `verify_render._render_rows` to raise `ValueError` after adding a row, raise
  `RuntimeError` in the body → the `RuntimeError` propagates.
- normal exit closes the open section.

## Shared test helpers — `tests/cli/commands/conftest.py`

```python
def _render(lines: Sequence[Line]) -> str:
    """Render a section's lines to text (test helper)."""
    return "\n".join(_render_rows(lines))

_MARKER_RE = re.compile("|".join(re.escape(s) for s in STATUS_SYMBOLS.values()))

def _assert_section_aligned(text: str) -> int:
    """All marker-bearing rows share marker column and value column; return row count."""

def _assert_sections_aligned(output: str) -> None:
    """Split by lines starting with '=== ' and apply _assert_section_aligned to each chunk;
    assert at least one row was checked overall."""
```

`_assert_section_aligned` algorithm:
```
first = None; count = 0
for line in text.splitlines():
    m = _MARKER_RE.search(line); rest = line[m.end():] if m else ""
    if m is None or not rest.strip(): continue        # hints, marker-less rows, freeform
    value_col = len(line) - len(rest.lstrip())
    if first is None: first = (m.start(), value_col)
    assert m.start() == first[0]; _assert_value_at_column(line, first[1]); count += 1
return count
```

Add a test in `test_verify_render.py` that `_assert_section_aligned` fails
(`pytest.raises(AssertionError)`) on two rows whose values sit at different
columns.

## DATA

- `_render_rows` → `list[str]`, one entry per output line, no trailing newline.
- `SectionBuilder._lines`: `list[Line]` while a section is open, else `None`.
