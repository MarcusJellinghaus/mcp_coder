# Step 6 — Alignment-Invariant Tests

## LLM Prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_6.md`. Steps
> 1-5 are merged; every tabular row in `verify.py` is now routed through
> `_format_row` or `_format_freeform_row`. Add the alignment-invariant
> tests that lock in the new behaviour. Produce exactly one commit.

## WHERE

* **New file:** `tests/cli/commands/test_verify_alignment.py`

This file is dedicated to invariant assertions. It does not duplicate the
string-pinned tests that already exist in `test_verify_format_section.py`
and the others.

## WHAT

Add two test classes:

### `TestWithinSectionAlignment`

For each of the migrated formatter functions, render a section that mixes
marker types, then assert the value column starts at the same horizontal
index on every labeled row.

* `_format_section` with a result containing `[OK]`, `[ERR]`, `[WARN]`, and
  the no-marker `strict_mode` branch.
* `_format_mcp_section` with one `[OK]` and one `[WARN]` server.
* `_format_claude_mcp_section` with one connected and one failed server.

Helper for the assertions:

```python
def _value_column_index(line: str) -> int:
    """Index where the value text begins (after marker slot + 1 space)."""
    # Use a regex or fixed offset based on _LABEL_WIDTH + _MARKER_SLOT_WIDTH.
```

Or, even simpler: pick a known-distinct value substring per row (e.g. a UUID
or a marker word) and assert `line.index(value)` is identical across rows.

Parameterize over marker presence and marker type so a regression in any
single branch fails a specific case.

### `TestCrossSectionAlignment`

Run `execute_verify` end-to-end (with the existing mock fixtures from
`test_verify_command.py` — copy or import the fixture style). Capture
stdout, then:

1. Filter to lines that look like tabular rows (start with `"  "` or
   `"    "` and contain at least one `[OK]`/`[ERR]`/`[WARN]` OR a
   non-empty value at the expected column).
2. For each filtered line, compute the index of the first non-whitespace
   character after the marker slot.
3. Assert all such indices are equal (or fall into a small known set:
   indent=2 vs indent=4 produce two distinct columns; both should be
   internally consistent).

If asserting a single global column is too brittle, weaken to: "every
labeled row at indent=2 has the same value column; every labeled row at
indent=4 has the same value column; the indent=4 column is exactly 2 chars
right of the indent=2 column."

## HOW

* Reuse mocks from `test_verify_command.py` (or extract a shared
  fixture). Importing private helpers (`_format_row`,
  `_format_section`, etc.) is fine — these are tests of internal
  contracts.
* Use `capsys` for stdout capture in the cross-section test.
* Keep the file under ~150 lines. KISS.

## ALGORITHM

Within-section invariant:
```
lines = formatter(...).split("\n")
content_lines = [l for l in lines if l and not l.startswith("===")]
value_indices = [_value_column_index(l) for l in content_lines]
assert len(set(value_indices)) == 1
```

Cross-section invariant:
```
captured = run_execute_verify_with_mocks()
rows_at_2 = [l for l in captured.split("\n") if l.startswith("  ") and not l.startswith("    ")]
rows_at_4 = [l for l in captured.split("\n") if l.startswith("    ")]
assert len({_value_column_index(l) for l in rows_at_2}) == 1
assert len({_value_column_index(l) for l in rows_at_4}) == 1
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
