# Step 1: Add --llm-method claude to automated Windows templates

## LLM Prompt

> Read `pr_info/steps/summary.md` for context. Implement Step 1: add `--llm-method claude` to the two automated Windows templates and update tests to match. Run all code quality checks after changes.

## WHERE

- `src/mcp_coder/workflows/vscodeclaude/templates.py`
- `tests/workflows/vscodeclaude/test_templates.py`

## WHAT

No new functions. String-level edits to two existing template constants and updates to four existing test functions.

### Template changes (`templates.py`)

1. **`AUTOMATED_SECTION_WINDOWS`** — In the `for /f` line, add `--llm-method claude` to the `mcp-coder prompt` command:
   - Before: `mcp-coder prompt "{command} {issue_number}" --output-format session-id --mcp-config .mcp.json --timeout {timeout}`
   - After: `mcp-coder prompt "{command} {issue_number}" --llm-method claude --output-format session-id --mcp-config .mcp.json --timeout {timeout}`

2. **`AUTOMATED_RESUME_SECTION_WINDOWS`** — Add `--llm-method claude` to the `mcp-coder prompt` command:
   - Before: `mcp-coder prompt "{command}" --session-id %SESSION_ID% --mcp-config .mcp.json --timeout {timeout}`
   - After: `mcp-coder prompt "{command}" --llm-method claude --session-id %SESSION_ID% --mcp-config .mcp.json --timeout {timeout}`

### Test changes (`test_templates.py`)

1. **Flip** `test_automated_section_no_hardcoded_llm_method` — rename to `test_automated_section_has_llm_method_claude`, assert `--llm-method claude` IS in `AUTOMATED_SECTION_WINDOWS`
2. **Flip** `test_automated_resume_section_no_hardcoded_llm_method` — rename to `test_automated_resume_section_has_llm_method_claude`, assert `--llm-method claude` IS in `AUTOMATED_RESUME_SECTION_WINDOWS`
3. **Delete** `test_interactive_only_section_no_hardcoded_llm_method` — tests `INTERACTIVE_ONLY_SECTION_WINDOWS` which uses `claude` CLI directly, not `mcp-coder prompt`; `--llm-method` is irrelevant
4. **Delete** `test_interactive_resume_section_no_hardcoded_llm_method` — tests `INTERACTIVE_RESUME_WITH_COMMAND_WINDOWS` which uses `claude` CLI directly; same reasoning

## HOW

- Direct string edits to template constants
- No new imports, decorators, or integration points

## ALGORITHM

```
1. In AUTOMATED_SECTION_WINDOWS, insert "--llm-method claude" after the prompt argument
2. In AUTOMATED_RESUME_SECTION_WINDOWS, insert "--llm-method claude" after the prompt argument
3. Flip 2 automated tests: assert --llm-method claude IS present
4. Delete 2 interactive tests: they don't use mcp-coder prompt
5. Run pylint, pytest, mypy — all must pass
6. Commit
```

## DATA

- No new return values or data structures
- Template strings gain one CLI flag each
