# Step 1 — Label renames

## LLM prompt

> Read `pr_info/steps/summary.md` (section "Label renames") and this file.
> Implement step 1 only: rename three verify labels so every fixed label we
> define fits the default 22-character label width. Write/adjust the tests
> first, then change the code. Run pylint, pytest (fast unit filter, `-n auto`)
> and mypy; all must pass. Produce exactly one commit.

## WHERE

- `src/mcp_coder/cli/commands/verify_formatting.py`
- new `tests/cli/commands/test_verify_label_map.py`
- `tests/cli/commands/test_verify_alignment.py`

## WHAT

| Location | Old | New |
|---|---|---|
| `_LABEL_MAP["signing_consistency"]` | `Signing config consistent` | `Signing consistency` |
| `_LABEL_MAP["ollama_tools_capability"]` | `Tool-calling capability` | `Tool-call capability` |
| `_format_tools_exposed_section`: `label` and docstring first line | `MCP tools exposed to model` | `Tools exposed to model` |

`Commit statuses: Read` is **not** renamed (matches GitHub permission names).

## Tests (write first)

New file `tests/cli/commands/test_verify_label_map.py`:

- `test_fixed_labels_fit_default_width`: every value in `_LABEL_MAP` has
  `len(...) <= _LABEL_WIDTH` (`Commit statuses: Read` is 21; it only widens
  GITHUB because it renders at indent 4 — expected, see summary).
- `test_renamed_labels`: `_LABEL_MAP["signing_consistency"] == "Signing consistency"`,
  `_LABEL_MAP["ollama_tools_capability"] == "Tool-call capability"`, and the first
  line returned by `_format_tools_exposed_section(None, STATUS_SYMBOLS)` starts
  with `"  Tools exposed to model "`.

In `tests/cli/commands/test_verify_alignment.py`, remove the
`"MCP tools exposed to model"` entry (and its comment) from `_NOTICE_PREFIXES`:
the renamed row now fits and is aligned like every other row.

## HOW

Plain string edits; no signature changes.

## DATA

No data-structure changes.
