# Step 2 — Rename misleading test file

## Goal

The current file `tests/llm/providers/claude/test_claude_cli_stream_integration.py`
tests **stream-json file logging** of the non-streaming `ask_claude_code_cli()`,
not the streaming `ask_claude_code_cli_stream()`. Rename it to reflect what it
actually tests, freeing the original name for Step 3's real streaming tests.

## WHERE

- From: `tests/llm/providers/claude/test_claude_cli_stream_integration.py`
- To:   `tests/llm/providers/claude/test_claude_cli_stream_logging_integration.py`

## WHAT

Pure file rename. **No content edits.** All assertions, fixtures, classes,
and imports stay byte-for-byte identical.

## HOW

Use `mcp__workspace__move_file` to rename the file. No other files import
from it (test modules are discovered by pytest, not imported), so no
follow-up edits should be required.

After moving, search the repository for any references to the old name to
confirm nothing else depends on it:
- `mcp__workspace__search_files` with pattern `test_claude_cli_stream_integration`

If references are found (e.g., in CI scripts or docs), update them.

## ALGORITHM

Not applicable — file rename only.

## DATA

Not applicable.

## Validation

1. Confirm new path exists, old path gone.
2. Run pylint, pytest (unit-only marker pattern), mypy via MCP tools.
3. Verify pytest still discovers and (skips, since marker excluded) the
   tests in the renamed file.
4. All three checks must pass.

## Commit

One commit titled e.g.:
`Rename test_claude_cli_stream_integration.py → ..._logging_integration.py (#916)`

---

## LLM Prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_2.md`. Implement
> Step 2 only: rename
> `tests/llm/providers/claude/test_claude_cli_stream_integration.py` to
> `tests/llm/providers/claude/test_claude_cli_stream_logging_integration.py`
> using `mcp__workspace__move_file`. Do **not** edit the file's contents.
> After the move, grep for the old filename across the repo and update any
> references (CI scripts, docs). Run pylint, pytest (unit-test exclusion
> markers), and mypy via MCP tools. All three must pass before producing
> one commit.
