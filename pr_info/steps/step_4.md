# Step 4: CLI wiring — parser + prompt command + test updates

> See `pr_info/steps/summary.md` for full context (Issue #642).

## Goal

Wire `rendered` into the CLI: add it to parser choices, make it the default,
add it to the streaming format tuple in prompt.py, and update any tests that
assert on the old default.

## WHERE

- **Modify**: `src/mcp_coder/cli/parsers.py`
- **Modify**: `src/mcp_coder/cli/commands/prompt.py`
- **Modify**: `tests/llm/formatting/test_formatters.py` (if any tests depend on default format)
- **Modify**: `tests/cli/commands/test_prompt_streaming.py` (update docstring/default references)
- **Modify**: `tests/cli/commands/test_prompt.py` (update docstring/default references)
- **Check**: `tests/cli/test_parsers.py` for tests that may assert on default output format

> The test_prompt_streaming.py and test_prompt.py changes are likely just updating a
> docstring reference or explicit format value to reflect the new default.

## WHAT — parsers.py (2 edits)

```python
# 1. Add "rendered" to choices
choices=["rendered", "text", "json", "session-id", "ndjson", "json-raw"],

# 2. Change default
default="rendered",

# 3. Update help text to reflect new default
help="Output format: rendered (default, human-friendly streaming), text (plain streaming), ..."
```

## WHAT — prompt.py (1 edit)

```python
# Add "rendered" to the streaming format tuple
if output_format in ("rendered", "text", "ndjson", "json-raw"):
```

## HOW

These are minimal edits — no new functions or imports.

## Tests to update

Search existing tests for:
- `output_format="text"` used as implicit default assumption
- `default="text"` assertions on parser configuration
- Any test that creates `argparse.Namespace` without explicit `output_format`

Update these to either:
- Explicitly set `output_format="text"` (if they test text format behavior)
- Assert the new default is `"rendered"`

## LLM Prompt

```
Implement Step 4 of Issue #642 (see pr_info/steps/summary.md and pr_info/steps/step_4.md).

Wire the "rendered" format into the CLI:
1. In src/mcp_coder/cli/parsers.py: add "rendered" to --output-format choices and change
   default from "text" to "rendered".
2. In src/mcp_coder/cli/commands/prompt.py: add "rendered" to the streaming format tuple.
3. Search tests for any assertions on the old default ("text") and update them.

Run all three code quality checks after changes. Produce one commit.
```
