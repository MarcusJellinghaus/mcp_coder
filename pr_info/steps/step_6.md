# Step 6 — Alignment-Invariant Tests

> **Note on line numbers:** all `verify.py:NNN` references in this step
> point at the file at branch HEAD before Step 1 lands. Locate the target
> by function name when implementing.

## LLM Prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_6.md`. Steps
> 1-5 are merged; every tabular row in `verify.py` is now routed through
> `_format_row` (label-less rows pass `label=""`). Add the
> alignment-invariant tests that lock in the new behaviour. Produce
> exactly one commit.

## WHERE

* **New file:** `tests/cli/commands/test_verify_alignment.py` — dedicated
  to invariant assertions. Does not duplicate the string-pinned tests
  already in `test_verify_format_section.py` and friends.
* **Shared fixture (new):** `tests/cli/commands/conftest.py` — create a
  **new** `_make_verify_mocks()` helper. This helper does not exist in
  `test_verify_orchestration.py` today — Step 6 introduces it fresh. The
  helper must mirror the `@patch` decorator stack currently used in
  `test_verify_orchestration.py` so a single call sets up the full mock
  surface that `execute_verify` interacts with. At minimum:

  - `verify_github`
  - `verify_mcp_servers`
  - `verify_mlflow`
  - `verify_claude`
  - `prepare_llm_environment`
  - `parse_claude_mcp_list`
  - `prompt_llm`
  - `_run_mcp_edit_smoke_test`
  - `resolve_llm_method`

  The implementer must verify this list against the current decorators
  on `test_verify_orchestration.py` when implementing Step 6 and add any
  that have been introduced since. **Adopt-not-rewrite:** existing tests
  in `test_verify_orchestration.py` are NOT migrated to use the helper
  in this commit; only the new smoke test consumes it.

## WHAT

Following the Q3 design decision (round-1 plan review), the test plan
splits into two layers: parameterized per-formatter invariants (the
workhorse — fast, no `execute_verify` mocking burden) plus one
end-to-end smoke test.

### Layer 1 — `TestPerFormatterAlignment` (workhorse, parameterized)

For each formatter helper that emits tabular rows, assert the value-column
invariant on the assembled output with stub inputs. These are unit tests:
they don't drive `execute_verify`, so they run fast and don't require
mocks beyond the stub data each formatter consumes.

Cover at minimum:

* `_format_section` — result mixing `[OK]`, `[ERR]`, `[WARN]`, and the
  no-marker `strict_mode` branch.
* `_format_mcp_section` — one `[OK]` and one `[WARN]` server, in both
  wrap mode and per-tool list mode.
* `_format_claude_mcp_section` — one connected and one failed server.
* `_print_environment_section` — capture stdout via `capsys`, assert the
  value column on Python version / Executable / Virtualenv / package
  versions all match.
* `_print_project_section` — same, mixed `format_code` / `check_type_hints`.
* MCP CONFIG WARNINGS render path (inline in `execute_verify`,
  post-Step-4 migration) — exercise with a long synthetic label like
  `langchain-mcp-adapters / VERY_LONG_VAR` to trigger the per-section
  dynamic `label_width`. Assert per-row column equality within the
  section using the dynamic width formula
  `2 + section_label_width + 1 + _MARKER_SLOT_WIDTH + 1`. This bullet
  is a per-section invariant (not a per-formatter Layer-1 case): the
  MCP warnings path uses a per-section `label_width` and is asserted
  with that section's specific expected column, not the global
  `_VALUE_COLUMN_INDENT`.

Parameterize over marker presence and marker type so a regression in any
single branch fails a specific case.

Helper for the assertions (pinned definition — implementer must use
this exact form, not a sketch):

```python
def _value_column_index(line: str, *, label_width: int = _LABEL_WIDTH) -> int:
    """Return the 0-indexed column where the value begins on a tabular row.

    Layout: [indent][label.ljust(label_width)][space][marker.ljust(_MARKER_SLOT_WIDTH)][space][value]
    The value column is at indent + label_width + 1 + _MARKER_SLOT_WIDTH + 1.
    For test parametrization, callers should pass the section's label_width
    explicitly when the section uses a dynamic width (e.g. MCP CONFIG WARNINGS).
    """
    indent = len(line) - len(line.lstrip(" "))
    return indent + label_width + 1 + _MARKER_SLOT_WIDTH + 1
```

Note: this returns the *expected* column based on layout constants;
tests assert that the actual value substring appears at this expected
position; if it does not, the assertion fails and identifies the
misaligned row.

### Layer 2 — `TestExecuteVerifyAlignmentSmoke` (one end-to-end)

Drive `execute_verify` exactly **once** with the shared
`_make_verify_mocks()` fixture (extracted to `conftest.py`). Capture
stdout. Assert: every emitted tabular row has its value column at the
expected position. This catches regressions where a maintainer adds a raw
`print(...)` directly in `execute_verify` (or anywhere else) instead of
going through a helper.

**Filter using an explicit allow-list, not "lines that look tabular":**

1. Skip lines that start with `"=== "` — section headers from `_pad`.
2. Skip group-header lines — match any line of the form `"  [name]"`:

   ```python
   import re
   if re.match(r"^  \[[A-Za-z][A-Za-z0-9_.\-]*\]\s*$", line):
       continue
   ```

   Note: matches both Project section's `[Python]` and CONFIG section's
   `[mcp]`, `[github]`, `[jenkins]`, etc. The pattern requires the
   bracketed name to be the entire line content (after the leading
   2-space indent), which distinguishes it from tabular rows that may
   include `[OK]`/`[WARN]`/`[ERR]` markers.
3. **Skip pre-existing freeform notice lines** that are intentionally
   not tabular rows. After Q4=C drops the freeform helper, these
   remain plain `print` calls (they are not migrated by Step 5):

   - `verify.py:575` — `"  Claude CLI: available at ..."` (and any
     sibling `"  Claude CLI:"` lines)
   - `verify.py:599` — `"  (uses Claude CLI — see Basic Verification above)"`
   - `verify.py:737` — `"  Run with --debug for detailed diagnostics."`
   - `verify.py:759` — `"  pip install <packages>"`

   **Choose approach (a) — explicit prefix patterns** for this plan:
   after stripping the leading two-space indent, skip lines whose
   stripped prefix starts with `"Claude CLI:"`, `"(uses Claude CLI"`,
   `"Run with --debug"`, or `"pip install "`. This is the
   simpler/clearer of the two options the planner offered (the other
   was a tighter positive filter that only asserts on lines whose
   marker slot contains `[OK]`/`[WARN]`/`[ERR]`); approach (a) keeps
   the assertion direct and the skip-list auditable.

4. For remaining non-empty lines, parse the leading-whitespace count.
   Accept `2` or `4` as the indent. Anything else → skip (it's a
   freeform continuation, e.g. the `-> install_hint` line at indent 32).
5. For each accepted line, compute the value-column index (first
   non-whitespace character after the marker slot, or use the helper
   above).

**Assertion (post Q2=B per-section dynamic width):**

The value column index for a row is
`indent + label_width + 1 + _MARKER_SLOT_WIDTH + 1`. Derive expected
from constants — never hard-code `32` / `34`:

```python
expected = _VALUE_COLUMN_INDENT + (indent - 2)
# equivalently: indent + _LABEL_WIDTH + 1 + _MARKER_SLOT_WIDTH + 1
```

With the defaults this resolves to `32` at indent=2 and `34` at indent=4,
but the test must read the value off the constant — if `_LABEL_WIDTH`
or `_MARKER_SLOT_WIDTH` ever changes, the assertion follows along for
free.

* For lines emitted in the MCP CONFIG WARNINGS section: value column
  index `>= expected` at indent=2 (the section may shift right when the
  longest label exceeds `_LABEL_WIDTH`).
* For all other indent=2 lines: value column index `== expected`
  (= `_VALUE_COLUMN_INDENT`).
* For all indent=4 lines: value column index `== expected`
  (= `_VALUE_COLUMN_INDENT + 2`).

Identifying "this line came from the MCP CONFIG WARNINGS section" is
straightforward: track the most recent `=== ` header seen during the
scan.

## HOW

* Create a new `_make_verify_mocks()` helper in
  `tests/cli/commands/conftest.py` so the new smoke test can import it.
  This helper does not exist in `test_verify_orchestration.py` today —
  Step 6 introduces it fresh. It must mirror the `@patch` decorator
  stack on the orchestration test class so a single call sets up the
  full mock surface (see the WHERE section above for the list).
  Existing tests in `test_verify_orchestration.py` are NOT migrated to
  use the helper in this commit (adopt-not-rewrite).
* Importing private helpers (`_format_row`, `_format_row_prefix`,
  `_format_section`, etc.) from `verify.py` is fine — these are tests
  of internal contracts.
* Use `capsys` for stdout capture in the smoke test and in the
  per-formatter tests that exercise `_print_*` functions.
* Keep `test_verify_alignment.py` under ~200 lines. KISS — Layer 1
  parameterized cases compress to a few `pytest.param(...)` entries.

## ALGORITHM

### Layer 1 — per-formatter (return-string formatters)

Group lines by indent before asserting equality. Formatters like
`_format_section` (top-level indent=2 + branch-protection children
indent=4 including `strict_mode`) and `_print_project_section` (top-level
indent=2 + sub-rows indent=4) emit mixed indents, so a single
`len(set(...)) == 1` across all content lines would fail. The invariant
is one shared value column **per indent level**.

```
from collections import defaultdict

def _value_column_index(line: str, *, label_width: int = _LABEL_WIDTH) -> int:
    # column where the value begins; for label-less rows the marker is at label_width+1
    indent = len(line) - len(line.lstrip(" "))
    return indent + label_width + 1 + _MARKER_SLOT_WIDTH + 1

lines = formatter(...).split("\n")
# the indent allow-list `(2, 4)` excludes continuation lines like the
# install-hint at indent=32, which are intentionally not tabular.
content_lines = [
    l for l in lines
    if l                                                     # not blank
    and not l.startswith("=== ")                             # section header
    and not re.match(r"^  \[[A-Za-z0-9_.\-]+\]\s*$", l)      # group header (see F3)
    and (len(l) - len(l.lstrip(" "))) in (2, 4)              # tabular indent only
]

by_indent: dict[int, list[int]] = defaultdict(list)
for line in content_lines:
    indent = len(line) - len(line.lstrip(" "))
    by_indent[indent].append(_value_column_index(line))

for indent, indices in by_indent.items():
    expected = _VALUE_COLUMN_INDENT + (indent - 2)
    # equivalently: indent + _LABEL_WIDTH + 1 + _MARKER_SLOT_WIDTH + 1
    assert len(set(indices)) == 1, f"value column drifts within indent={indent}"
    assert indices[0] == expected, f"indent={indent}: got {indices[0]}, expected {expected}"
```

The assertion now runs once per (formatter, indent-level) pair instead
of once per formatter. The "Cover at minimum" bullets that mix indent=2
and indent=4 (`_format_section`, `_print_project_section`) become
naturally compatible with the test rather than failure cases.

### Layer 1 — per-formatter (`_print_*` functions)
```
formatter(...)            # writes to stdout via print()
captured = capsys.readouterr().out
# same indent-grouped filter + per-indent assertion as above
```

### Layer 2 — end-to-end smoke
```
import re

NOTICE_PREFIXES = (
    "Claude CLI:",
    "(uses Claude CLI",
    "Run with --debug",
    "pip install ",
)
GROUP_HEADER_RE = re.compile(r"^  \[[A-Za-z][A-Za-z0-9_.\-]*\]\s*$")

captured = run_execute_verify_with_mocks()  # uses _make_verify_mocks()
section = None
for line in captured.split("\n"):
    if line.startswith("=== "):
        section = line.strip("= ").strip()
        continue
    if not line:
        continue
    if GROUP_HEADER_RE.match(line):
        # matches Project section's [Python] and CONFIG section's [mcp],
        # [github], [jenkins], etc.
        continue
    stripped = line.lstrip(" ")
    if any(stripped.startswith(p) for p in NOTICE_PREFIXES):
        continue
    indent = len(line) - len(stripped)
    if indent not in (2, 4):
        continue
    col = _value_column_index(line)
    expected = _VALUE_COLUMN_INDENT + (indent - 2)
    # equivalently: indent + _LABEL_WIDTH + 1 + _MARKER_SLOT_WIDTH + 1
    if section == "MCP CONFIG WARNINGS" and indent == 2:
        assert col >= expected, (line, col, section)
    else:
        assert col == expected, (line, col, section)
```

## DATA

* New test functions return `None` (standard pytest).
* No production code changes in this step.

## Tests

This step **is** the test addition. No further updates to existing tests.

If the invariant tests reveal a row that was missed in Steps 1-5, fix that
row in the same commit (it is the bug the invariant test exists to catch).
Document the fix in the commit message.

## Verification

Run pylint, pytest, mypy. After this step, the issue's acceptance criteria
are met:

* Every tabular row in `verify` output has a stable value column.
* Marker presence/absence and marker type no longer shift values.
* The `_pad` header reaches 75 chars so long titles still terminate in `=`.
