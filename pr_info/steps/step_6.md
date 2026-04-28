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
* **Shared fixture (new):** `tests/cli/commands/conftest.py` —
  introduces a **new** `_make_verify_mocks()` helper. The shared
  alignment-test helpers `_expected_value_column(indent, *,
  label_width)` and `_assert_value_at_column(line, expected_col)` are
  introduced in Step 3 (`tests/cli/commands/conftest.py`); Step 6
  reuses them. `_make_verify_mocks()` does not exist in
  `test_verify_orchestration.py` today — Step 6 introduces it fresh.
  The helper must mirror the `@patch` decorator stack currently used in
  `test_verify_orchestration.py` so a single call sets up the full mock
  surface that `execute_verify` interacts with.

  Note: `tests/cli/commands/conftest.py` already provides autouse
  fixtures `_mock_verify_config` and `_mock_verify_github` that patch
  `verify_config` and `verify_github` to default-OK results.
  `_make_verify_mocks()` should NOT re-patch those — instead, compose
  with the existing fixtures by patching only the *additional* surface:

  - `verify_mcp_servers`
  - `verify_mlflow`
  - `verify_claude`
  - `prepare_llm_environment`
  - `parse_claude_mcp_list`
  - `prompt_llm`
  - `_run_mcp_edit_smoke_test`
  - `resolve_llm_method`
  - `_collect_mcp_warnings` — patched to return an empty list so the
    dynamic-width MCP CONFIG WARNINGS section is excluded from the
    captured output (per-section invariant lives in step_4.md tests).

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

> Note: MCP CONFIG WARNINGS uses a per-section dynamic `label_width`;
> that invariant is asserted in `step_4.md` Tests, not here. Layer 1's
> helpers default to `label_width=_LABEL_WIDTH=22`, which is the wrong
> contract for the dynamic-width section.

Parameterize over marker presence and marker type so a regression in any
single branch fails a specific case.

Layer 1 uses two helpers, deliberately split so the test can compare
what the layout *should* produce against what the line *does* produce:
`_expected_value_column(indent)` returns the column from layout
constants (it does NOT inspect the line); `_assert_value_at_column(line,
expected_col)` inspects the actual line content and asserts the value
lands at `expected_col` (with whitespace at `expected_col - 1`). A
producer that drifts from the helper signature (e.g. a hand-rolled
`f-string` with wrong widths) is detected.

These helpers are introduced in Step 3
(`tests/cli/commands/conftest.py`); Step 6 reuses them.

The two helpers together form an actual alignment check: the expected
column comes from constants, the assertion inspects the line. If
production code rendered with a wrong `label_width` or `marker_slot`,
the boundary characters at `expected_col - 1` / `expected_col` would be
wrong and the assertion fires. This is the contract Round 5 hardens —
the previous single helper was tautological because it derived the
expected column from the same formula the assertion compared against.

### Layer 2 — `TestExecuteVerifyAlignmentSmoke` (one end-to-end)

Drive `execute_verify` exactly **once** with the shared
`_make_verify_mocks()` fixture (extracted to `conftest.py`). Capture
stdout. Assert: every emitted tabular row has its value column at the
expected position, using the same `_expected_value_column` /
`_assert_value_at_column` pair as Layer 1. This catches regressions
where a maintainer adds a raw `print(...)` directly in `execute_verify`
(or anywhere else) instead of going through a helper.

**MCP CONFIG WARNINGS exemption.** The smoke test fixture mocks
`_collect_mcp_warnings` to return an empty list — no MCP warnings are
emitted, so the dynamic-width section never appears in the asserted
output. This avoids false failures: Layer 2's helpers default to
`label_width=_LABEL_WIDTH=22`, but the dynamic-width section may use a
larger value (e.g. ~45 chars for `langchain-mcp-adapters / VERY_LONG_VAR`),
and the boundary check would fail at the default. The per-section
dynamic-width invariant lives in `step_4.md`'s unit tests where the
expected column is computed from the section-specific `label_width`.
This is the simplest fix — Layer 2 is a smoke test, not a comprehensive
coverage tool, and per-section invariants belong in their unit tests.

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
5. For each accepted line, compute the expected value column from
   constants via `_expected_value_column(indent)` and assert with
   `_assert_value_at_column(line, expected_col)`.

**Assertion:**

For each accepted line, the expected value column is
`_expected_value_column(indent)` — i.e.
`indent + _LABEL_WIDTH + 1 + _MARKER_SLOT_WIDTH + 1`. With the defaults
this resolves to `32` at indent=2 and `34` at indent=4, but the test
must read the value off the constant — if `_LABEL_WIDTH` or
`_MARKER_SLOT_WIDTH` ever changes, the assertion follows along for free.

`_assert_value_at_column(line, expected_col)` then inspects the line:
it requires whitespace at `expected_col - 1` and a non-whitespace
character at `expected_col`. The assertion is no longer tautological —
the expected column is formula-derived, but the boundary check actually
reads the line's content.

The Layer 2 fixture mocks `_collect_mcp_warnings` to return an empty
list, so MCP CONFIG WARNINGS rows (which use a per-section dynamic
`label_width`) never appear in the captured output. No section-aware
exemption is needed in the loop. The dynamic-width invariant is
asserted in `step_4.md`'s unit tests.

## HOW

* Create a new `_make_verify_mocks()` helper in
  `tests/cli/commands/conftest.py` so the new smoke test can import it.
  This helper does not exist in `test_verify_orchestration.py` today —
  Step 6 introduces it fresh. It must mirror the `@patch` decorator
  stack on the orchestration test class so a single call sets up the
  full mock surface (see the WHERE section above for the list). The
  helper must additionally patch `_collect_mcp_warnings` to return an
  empty list so the dynamic-width MCP CONFIG WARNINGS section does not
  appear in the captured output (Layer 2 cannot describe the
  per-section dynamic `label_width`; that invariant lives in
  step_4.md's unit tests). Existing tests in
  `test_verify_orchestration.py` are NOT migrated to use the helper in
  this commit (adopt-not-rewrite).

  Note: `tests/cli/commands/conftest.py` already provides autouse
  fixtures `_mock_verify_config` and `_mock_verify_github` that patch
  `verify_config` and `verify_github` to default-OK results.
  `_make_verify_mocks()` should NOT re-patch those — instead, compose
  with the existing fixtures by patching only the *additional* surface
  listed above (drop `verify_github` from the patch list; it is already
  covered).
* `_assert_value_at_column(line, expected_col)` and
  `_expected_value_column(indent, *, label_width)` are introduced in
  Step 3 (`tests/cli/commands/conftest.py`). Step 6 imports them from
  there; do NOT redefine.
* Importing private helpers (`_format_row`, `_format_row_prefix`,
  `_format_section`, etc.) from `verify.py` is fine — these are tests
  of internal contracts.
* Use `capsys` for stdout capture in the smoke test and in the
  per-formatter tests that exercise `_print_*` functions.
* Keep `test_verify_alignment.py` under ~200 lines. KISS — Layer 1
  parameterized cases compress to a few `pytest.param(...)` entries.

## ALGORITHM

### Layer 1 — per-formatter (return-string formatters)

Group lines by indent, then assert each line lands its value at the
expected column for that indent. Formatters like `_format_section`
(top-level indent=2 + branch-protection children indent=4 including
`strict_mode`) and `_print_project_section` (top-level indent=2 +
sub-rows indent=4) emit mixed indents, so a single equality across all
content lines would fail. The invariant is one shared value column
**per indent level**, derived from constants and asserted against the
actual line content.

```
from collections import defaultdict
import re

GROUP_HEADER_RE = re.compile(r"^  \[[A-Za-z][A-Za-z0-9_.\-]*\]\s*$")

def _content_lines(output: str) -> list[str]:
    return [
        l for l in output.splitlines()
        if l
        and not l.startswith("=== ")
        and not GROUP_HEADER_RE.match(l)
        and (len(l) - len(l.lstrip(" "))) in (2, 4)
    ]

# For each formatter under test:
lines = _content_lines(formatter_output)
by_indent: dict[int, list[str]] = defaultdict(list)
for line in lines:
    indent = len(line) - len(line.lstrip(" "))
    by_indent[indent].append(line)

for indent, lines_at_indent in by_indent.items():
    expected_col = _expected_value_column(indent)
    for line in lines_at_indent:
        _assert_value_at_column(line, expected_col)
```

The assertion is no longer tautological: `_expected_value_column` is
formula-derived, but `_assert_value_at_column` actually inspects
`line[expected_col-1]` and `line[expected_col]`. If production code
rendered with a wrong `label_width` or `marker_slot`, the boundary
characters would be wrong and the assertion fires. The "Cover at
minimum" bullets that mix indent=2 and indent=4 (`_format_section`,
`_print_project_section`) work naturally — each indent level is
checked against its own expected column.

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

# IMPORTANT: the Layer 2 fixture mocks `_collect_mcp_warnings` to return
# an empty list. MCP CONFIG WARNINGS uses a per-section dynamic
# `label_width` that the Layer 2 helpers (which use the default
# `_LABEL_WIDTH=22`) cannot describe; the per-section invariant is
# asserted in step_4.md's unit tests, not here.

captured = run_execute_verify_with_mocks()  # uses _make_verify_mocks()
for line in captured.split("\n"):
    if line.startswith("=== "):
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
    expected_col = _expected_value_column(indent)
    _assert_value_at_column(line, expected_col)
```

The smoke test mirrors Layer 1's pattern: `_expected_value_column` for
the contract, `_assert_value_at_column` for the actual inspection. By
mocking `_collect_mcp_warnings` to return an empty list, the
dynamic-width MCP CONFIG WARNINGS rows never appear in the output, so
no per-section exemption is needed. Layer 2 is a smoke test, not a
comprehensive coverage tool — per-section invariants belong in their
unit tests.

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
