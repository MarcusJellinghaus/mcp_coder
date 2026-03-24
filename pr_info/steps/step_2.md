# Step 2: Add `init` to help text

## LLM Prompt

> Read `pr_info/steps/summary.md` for context, then implement Step 2 from `pr_info/steps/step_2.md`.
> Follow TDD: update test first, then implement, then verify all checks pass.
> Use MCP tools for all file operations and code quality checks per CLAUDE.md.

## Overview

Add the `init` command to the help text so users can discover it via `mcp-coder help`. Full help text consolidation is tracked in #565 — this step only adds the `init` entry.

## WHERE: Files to modify

### `tests/cli/commands/test_help.py` (update existing test)

- **WHAT**: Add assertion that help text contains `init` command entry
- **HOW**: Find the existing test that checks help text content (likely `test_help_text_contains_commands` or similar), add assertion that the output contains `"init"` and a description like `"Create default configuration file"` or `"Create default config"`
- **DATA**: String assertion on help text output

### `src/mcp_coder/cli/commands/help.py`

- **WHAT**: Add `init` line to `get_help_text()` COMMANDS section
- **HOW**: In the COMMANDS section string, add after the `verify` line:
  ```
      init                    Create default configuration file
  ```
- **DATA**: No new functions or return values — string content change only

## Commit

One commit: `feat: add init command to help text (#554)`
