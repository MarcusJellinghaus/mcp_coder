# Step 1: Update CLAUDE.md — remaining sections

## References
- [Summary](summary.md)
- Issue #672

## WHERE
- `.claude/CLAUDE.md`

## WHAT

Most CLAUDE.md changes were already completed via a prior PR on main (tool mapping table rows, "Before ANY commit" section, "Format all code" section, Quick Examples). Only two sections remain.

### Code Quality Requirements section

Update the count from "ALL THREE" to "ALL FIVE". Add two new descriptive bullets for `mcp__tools-py__run_lint_imports_check` and `mcp__tools-py__run_vulture_check` alongside the existing pylint/pytest/mypy bullets. Also add the 2 new tools to the code block listing the MCP tool names.

### Refactoring row in Tool Mapping Table

Add `get_library_source()` to the existing Refactoring row (which already lists `move_symbol()`, `list_symbols()`, `find_references()`).

## HOW

Edit markdown instruction text and table. Match existing formatting conventions.

## DATA

No code logic — markdown only.

## Verification

- `mcp__tools-py__run_lint_imports_check` and `mcp__tools-py__run_vulture_check` appear in the Code Quality Requirements section
- `get_library_source()` appears in the Refactoring row of the tool mapping table
- `ruff_check.sh` row is unchanged
- No other sections modified

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_1.md for context.

Edit `.claude/CLAUDE.md`:
1. In Code Quality Requirements section: change "ALL THREE" to "ALL FIVE", add descriptive bullets for lint_imports_check and vulture_check alongside existing pylint/pytest/mypy bullets, and add the 2 new tools to the code block listing MCP tool names
2. In the tool mapping table Refactoring row, add get_library_source() alongside existing move_symbol(), list_symbols(), find_references()
3. Do NOT add new rows to the tool mapping table for format_code, lint_imports, or vulture_check
4. Leave ruff_check.sh references unchanged
5. Leave Git Operations "ALLOWED" list unchanged
6. Do NOT modify "Before ANY commit", "Format all code", Quick Examples, or tool mapping table rows — those are already done

Use plain text MCP tool references matching the existing pylint/pytest/mypy pattern. Run code quality checks. Commit as: "docs: update CLAUDE.md quality checks section and refactoring row"
```
