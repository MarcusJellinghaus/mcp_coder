# Step 2 — Migrate `_format_mcp_section` and `_format_claude_mcp_section`

## LLM Prompt

> Read `pr_info/steps/summary.md` for context and `pr_info/steps/step_2.md`
> for this step. Step 1 is already merged; the helpers `_format_row` and
> `_format_freeform_row` exist. Follow TDD: update tests first, then
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
`textwrap.wrap` as `initial_indent`. The replacement must:

1. Build the labeled row WITHOUT the value via `_format_row(name, symbol, "", indent=2)`,
2. Strip the trailing whitespace from the helper output to get the prefix
   (the helper `rstrip`s — call it with a placeholder value, or build the
   prefix manually).

Simplest: keep this prefix construction inline since textwrap needs the
exact column-width string with trailing space. Pseudocode:

```
prefix = _format_row(name, symbol, "", indent=2) + " "
# Compute value (tools text), then textwrap.wrap as before.
```

Alternatively: format a one-liner via `_format_row(name, symbol, tools_text, indent=2)`
first, then split/wrap it. The first approach is closer to the existing logic
and keeps wrap behaviour identical.

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

* **`TestFormatMcpSection.test_tool_names_wrap_at_80_columns`** — wrap is
  bounded by `width=80`; the prefix is now wider (22 label + 6 marker = 28
  vs old 20 + variable). Re-verify the test still passes given the wider
  prefix; if `<= 80 chars` is now infeasible, update the test or accept that
  wrapped lines may include the wider prefix.

## Verification

Run pylint, pytest, mypy. All must pass.
