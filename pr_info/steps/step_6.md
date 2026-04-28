# Step 6 — Alignment-Invariant Tests

> **Note on line numbers:** all `verify.py:NNN` references in this step
> point at the file at branch HEAD before Step 1 lands. Locate the target
> by function name when implementing.

## LLM Prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_6.md`. Steps
> 1-5 are merged; every tabular row in `verify.py` is now routed through
> `_format_row` or `_format_freeform_row`. Add the alignment-invariant
> tests that lock in the new behaviour. Produce exactly one commit.

## WHERE

* **New file:** `tests/cli/commands/test_verify_alignment.py` — dedicated
  to invariant assertions. Does not duplicate the string-pinned tests
  already in `test_verify_format_section.py` and friends.
* **Shared fixture (new or extended):** `tests/cli/commands/conftest.py`
  — extracts `_make_verify_mocks()` (currently inlined in
  `test_verify_orchestration.py` and similar files) so both the new
  end-to-end smoke test and existing tests can import it.
  **Adopt-not-rewrite:** existing tests don't need to migrate to the
  shared fixture in this commit; the goal is just to make it importable.

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
* `_format_mcp_section` (warnings render path) — long label
  (`langchain-mcp-adapters / PYTHONPATH`) and short label in the same
  section; assert the value column matches across both rows AND equals
  `2 + max_label_len + 1 + _MARKER_SLOT_WIDTH + 1`.

Parameterize over marker presence and marker type so a regression in any
single branch fails a specific case.

Helper for the assertions:

```python
def _value_column_index(line: str) -> int:
    """Index where the value text begins (after marker slot + 1 space)."""
    # Use a regex or fixed offset based on _LABEL_WIDTH + _MARKER_SLOT_WIDTH.
```

Or, even simpler: pick a known-distinct value substring per row (e.g. a
UUID or a marker word) and assert `line.index(value)` is identical across
rows.

### Layer 2 — `TestExecuteVerifyAlignmentSmoke` (one end-to-end)

Drive `execute_verify` exactly **once** with the shared
`_make_verify_mocks()` fixture (extracted to `conftest.py`). Capture
stdout. Assert: every emitted tabular row has its value column at the
expected position. This catches regressions where a maintainer adds a raw
`print(...)` directly in `execute_verify` (or anywhere else) instead of
going through a helper.

**Filter using an explicit allow-list, not "lines that look tabular":**

1. Skip lines that start with `"=== "` — section headers from `_pad`.
2. Skip lines that match `^  \[` — Environment group headers like
   `"  [Python]"`.
3. For remaining non-empty lines, parse the leading-whitespace count.
   Accept `2` or `4` as the indent. Anything else → skip (it's a
   freeform continuation, e.g. the `-> install_hint` line at indent 32).
4. For each accepted line, compute the value-column index (first
   non-whitespace character after the marker slot, or use the helper
   above).

**Assertion (post Q2=B per-section dynamic width):**

* For lines emitted in the MCP CONFIG WARNINGS section: value column
  index `>= 31` (the section may shift right when the longest label
  exceeds `_LABEL_WIDTH`).
* For all other indent=2 lines: value column index `== 31`
  (`indent=2 + label_width=22 + ` `+ marker_slot=6 + ` ` = 31, so first
  value char at index 31).
* For all indent=4 lines: value column index `== 33` (`indent=4 + 22 +
  1 + 6 + 1`).

Identifying "this line came from the MCP CONFIG WARNINGS section" is
straightforward: track the most recent `=== ` header seen during the
scan.

## HOW

* Extract `_make_verify_mocks()` to `tests/cli/commands/conftest.py`
  so the new smoke test (and any future test) can import it without
  copy-pasting the mock setup. Existing tests in
  `test_verify_orchestration.py` keep working as-is — the function
  is just relocated and re-exported, not rewritten.
* Importing private helpers (`_format_row`, `_format_row_prefix`,
  `_format_section`, etc.) from `verify.py` is fine — these are tests
  of internal contracts.
* Use `capsys` for stdout capture in the smoke test and in the
  per-formatter tests that exercise `_print_*` functions.
* Keep `test_verify_alignment.py` under ~200 lines. KISS — Layer 1
  parameterized cases compress to a few `pytest.param(...)` entries.

## ALGORITHM

### Layer 1 — per-formatter (return-string formatters)
```
lines = formatter(...).split("\n")
content_lines = [l for l in lines if l and not l.startswith("=== ")
                                       and not re.match(r"^  \[", l)]
value_indices = [_value_column_index(l) for l in content_lines]
assert len(set(value_indices)) == 1
```

### Layer 1 — per-formatter (`_print_*` functions)
```
formatter(...)            # writes to stdout via print()
captured = capsys.readouterr().out
# same filter + assertion as above
```

### Layer 2 — end-to-end smoke
```
captured = run_execute_verify_with_mocks()  # uses _make_verify_mocks()
section = None
for line in captured.split("\n"):
    if line.startswith("=== "):
        section = line.strip("= ").strip()
        continue
    if not line or re.match(r"^  \[", line):
        continue
    indent = len(line) - len(line.lstrip(" "))
    if indent not in (2, 4):
        continue
    col = _value_column_index(line)
    expected = 31 if indent == 2 else 33
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
