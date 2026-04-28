# Step 2 — Migrate `_format_mcp_section` and `_format_claude_mcp_section`

> **Note on line numbers:** all `verify.py:NNN` references in this step
> point at the file at branch HEAD before Step 1 lands. Locate the target
> by function name when implementing.

## LLM Prompt

> Read `pr_info/steps/summary.md` for context and `pr_info/steps/step_2.md`
> for this step. Step 1 is already merged; the helpers `_format_row_prefix`
> and `_format_row` exist (label-less rows pass `label=""` — there is no
> separate `_format_freeform_row`). Follow TDD: update tests first, then
> migrate the two formatters. Produce exactly one commit.

## WHERE

* **Source:** `src/mcp_coder/cli/commands/verify.py`
* **Tests:** `tests/cli/commands/test_verify_format_section.py`
  (classes `TestFormatMcpSection`, `TestFormatClaudeMcpSection`,
  `TestFormatMcpSectionForCompleteness`).

## WHAT

In `_format_mcp_section`, replace every line that currently uses
`f"  {name:<20s} {symbol} ..."` with a `_format_row(name, symbol, value, indent=2)`
call (or, when value is computed, pass the computed string).

Affected lines (current line numbers):
* `verify.py:293` — list mode header per server (`f"  {name:<20s} {symbol} {len(tool_names)} tools available"`).
* `verify.py:301` — list mode no-tool fallback.
* `verify.py:309` — wrap mode prefix (the `prefix` variable feeding `textwrap.wrap`).
  This one is special — see below.
* `verify.py:320` — wrap mode no-tool fallback.

In `_format_claude_mcp_section`, line `verify.py:344`:
* `f"  {status.name:<20s} {symbol} {status.status_text}"` → `_format_row(...)`.

### Special case: `textwrap.wrap` prefix

The wrap-mode branch currently builds a `prefix` string and feeds it to
`textwrap.wrap` as `initial_indent`. Use `_format_row_prefix` directly —
it returns the column-aligned prefix WITH trailing space and WITHOUT
rstrip, which is exactly what `textwrap.wrap` needs:

```python
prefix = _format_row_prefix(name, symbol, indent=2)
# No need to append "+ ' '"; the helper already includes the trailing space.
# No interaction with _format_row.rstrip() — that's only on _format_row.
# Then compute value (tools text) and textwrap.wrap as before.
```

This was a Q1 design decision (round-1 plan review): we chose composition
over duplicating the layout formula in two places. `_format_row` is now
defined as
`(_format_row_prefix(...) + value).rstrip()`, which means the prefix and
the labeled row share a single source of truth for indent/label/marker
geometry. The wrap-prefix site simply consumes the same primitive.

## HOW

* No new imports.
* `_format_row` was added in Step 1.
* No signature changes for either function.

## ALGORITHM

Direct substitution; no algorithmic change.

## DATA

Both functions still return `str` (joined multi-line).

## Tests

Update `tests/cli/commands/test_verify_format_section.py`:

* **`TestFormatMcpSection`** — `test_no_tool_names_falls_back_to_value`,
  `test_failed_server_shows_value_not_tools`,
  `test_empty_tool_names_falls_back_to_value`,
  `test_list_mcp_tools_shows_per_tool_lines`,
  `test_list_mcp_tools_failed_server_shows_error`,
  `test_list_mcp_tools_false_still_shows_comma_format`,
  `test_list_mcp_tools_all_servers_failed`: any assertion that pins a string
  containing `"<name>      [OK]"` (with old 20-wide alignment) must use the
  new 22+6 spacing. Most assertions use `in` substrings — verify those still
  hold; tweak counts/positions if needed.

* **`TestFormatClaudeMcpSection.test_server_names_left_aligned`** — currently
  asserts `"mcp-tools-py      "` (padded to 20). Update to padded-to-22.

* **`TestFormatMcpSection.test_tool_names_wrap_at_80_columns`** — the
  prefix is now exactly **32 chars** (`indent=2 + label_width=22 + ` `+
  marker_slot=6 + ` `). With `width=80`, that leaves a budget of **48
  chars per wrapped line** for the comma-joined tool names. Sample
  fixture has ~7 tool-name slots averaging ~22 chars + `, ` separators;
  this fits comfortably. Keep the test fixture at `width=80` and keep
  the assertion `len(line) <= 80`. If a future tool name pushes a single
  comma-joined token past the 48-char budget, **raise the test fixture's
  width** — do NOT weaken the `<= 80` assertion. (The assertion is what
  guards user-visible wrap behaviour; relaxing it would defeat the test.)

## Verification

Run pylint, pytest, mypy. All must pass.
