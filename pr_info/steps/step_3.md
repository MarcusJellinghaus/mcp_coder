# Step 3: Update CLAUDE.md tool mapping and commit instructions

## References
- [Summary](summary.md)
- Issue #672

## WHERE
- `.claude/CLAUDE.md`

## WHAT

### Tool Mapping Table

Add 4 new rows to the existing table (after the mypy row, before ruff):

```
| Format code | `Bash("./tools/format_all.sh")` | `mcp__tools-py__run_format_code` |
| Lint imports | `Bash("./tools/lint_imports.sh")` | `mcp__tools-py__run_lint_imports_check` |
| Vulture check | `Bash("./tools/vulture_check.sh")` | `mcp__tools-py__run_vulture_check` |
| Library source | - | `mcp__tools-py__get_library_source` |
```

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

### Git Operations "ALLOWED" list

No changes needed — `format_all.sh` is not in that list.

## HOW

Edit markdown table and instruction text. Match existing formatting conventions.

## DATA

No code logic — markdown only.

## Verification

- Tool mapping table has 4 new rows with correct column alignment
- No remaining references to `format_all.sh` in CLAUDE.md
- `lint_imports.sh` and `vulture_check.sh` appear only in the "NEVER USE" column
- `ruff_check.sh` row is unchanged
- `get_library_source` has `-` in the "NEVER USE" column (it's new, not a replacement)

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_3.md for context.

Edit `.claude/CLAUDE.md`:
1. Add 4 rows to the tool mapping table (format code, lint imports, vulture check, library source)
2. Update "Before ANY commit" section — replace format_all.sh with mcp__tools-py__run_format_code
3. Update "Format all code before committing" bullet — same replacement
4. Leave ruff_check.sh references unchanged
5. Leave Git Operations "ALLOWED" list unchanged

Use plain text MCP tool references matching the existing pylint/pytest/mypy pattern. Run code quality checks. Commit as: "docs: update CLAUDE.md tool mapping and commit instructions"
```
