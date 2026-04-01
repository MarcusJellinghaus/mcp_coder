# Step 1: Update settings.local.json permissions

## References
- [Summary](summary.md)
- Issue #672

## WHERE
- `.claude/settings.local.json`

## WHAT

Update the `permissions.allow` array:

**Add** these 4 MCP tool permissions:
```
"mcp__tools-py__run_format_code"
"mcp__tools-py__run_lint_imports_check"
"mcp__tools-py__run_vulture_check"
"mcp__tools-py__get_library_source"
```

**Remove** these 3 Bash permissions:
```
"Bash(./tools/format_all.sh:*)"
"Bash(./tools/lint_imports.sh:*)"
"Bash(./tools/vulture_check.sh:*)"
```

## HOW

Edit the JSON `permissions.allow` array. Place new MCP tool entries next to the existing `mcp__tools-py__*` entries for logical grouping.

## DATA

No code logic — JSON configuration only.

## Verification

- File is valid JSON after edit
- 4 new entries present
- 3 old entries removed
- Other permissions unchanged (especially `ruff_check.sh` which stays)

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_1.md for context.

Edit `.claude/settings.local.json`:
1. Add 4 MCP permissions (run_format_code, run_lint_imports_check, run_vulture_check, get_library_source) — group them with existing mcp__tools-py entries
2. Remove 3 Bash permissions (format_all.sh, lint_imports.sh, vulture_check.sh)
3. Keep all other permissions unchanged (ruff_check.sh stays)
4. Verify valid JSON

Run code quality checks after editing. Commit as: "chore: update permissions for MCP tool replacements"
```
