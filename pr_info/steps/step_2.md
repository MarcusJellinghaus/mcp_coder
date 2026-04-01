# Step 2: Update CLAUDE.md tool mapping and commit instructions

## References
- [Summary](summary.md)
- Issue #672

## WHERE
- `.claude/CLAUDE.md`

## WHAT

### "Before ANY commit" section

Replace:
```bash
# ALWAYS run format_all before committing
./tools/format_all.sh
```
With:
```
# ALWAYS run mcp__tools-py__run_format_code before committing
```
(Plain text MCP tool reference, matching existing pylint/pytest/mypy pattern.)

### "Format all code before committing" section

Replace:
```
- Run `./tools/format_all.sh` to format with black and isort
```
With:
```
- Run `mcp__tools-py__run_format_code` to format with black and isort
```

### Code Quality Requirements section

Update the count from "ALL THREE" to "ALL FIVE". Add two new descriptive bullets for `mcp__tools-py__run_lint_imports_check` and `mcp__tools-py__run_vulture_check` alongside the existing pylint/pytest/mypy bullets. Also add the 2 new tools to the code block listing the MCP tool names.

### Refactoring row in Tool Mapping Table

Add `get_library_source()` to the existing Refactoring row (which already lists `move_symbol()`, `list_symbols()`, `find_references()`).

### Tool Mapping Table — no new rows

The table is for "don't use X, use Y" replacements. Claude wouldn't naturally run these shell scripts via Bash, so no "NEVER USE" entries are needed. No new rows added.

### Git Operations "ALLOWED" list

No changes needed — `format_all.sh` is not in that list.

## HOW

Edit markdown instruction text and table. Match existing formatting conventions.

## DATA

No code logic — markdown only.

## Verification

- No remaining references to `format_all.sh` in CLAUDE.md
- `ruff_check.sh` row is unchanged
- `mcp__tools-py__run_lint_imports_check` and `mcp__tools-py__run_vulture_check` appear in the Code Quality Requirements section
- `get_library_source()` appears in the Refactoring row of the tool mapping table
- "Before ANY commit" and "Format all code" sections reference `mcp__tools-py__run_format_code`

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_2.md for context.

Edit `.claude/CLAUDE.md`:
1. Update "Before ANY commit" section — replace the content inside the code block with mcp__tools-py__run_format_code (keep the code block wrapper for consistency with the quality checks section above)
2. Update "Format all code before committing" bullet — same replacement
3. In Code Quality Requirements section: change "ALL THREE" to "ALL FIVE", add descriptive bullets for lint_imports_check and vulture_check alongside existing pylint/pytest/mypy bullets, and add the 2 new tools to the code block listing MCP tool names
4. In the tool mapping table Refactoring row, add get_library_source() alongside existing move_symbol(), list_symbols(), find_references()
5. Do NOT add new rows to the tool mapping table for format_code, lint_imports, or vulture_check
6. Leave ruff_check.sh references unchanged
7. Leave Git Operations "ALLOWED" list unchanged

Use plain text MCP tool references matching the existing pylint/pytest/mypy pattern. Run code quality checks. Commit as: "docs: update CLAUDE.md tool mapping and commit instructions"
```
