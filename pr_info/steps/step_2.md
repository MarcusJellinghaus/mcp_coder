# Step 2: Config — settings.local.json and CLAUDE.md

## Context
See `pr_info/steps/summary.md` for full issue context.

Update the two central configuration files: add MCP tool permissions and update instructions to reference MCP tools instead of Bash scripts.

## WHERE
- `.claude/settings.local.json`
- `.claude/CLAUDE.md`

## WHAT — settings.local.json

### Add 4 MCP permissions (in the `permissions.allow` array)
```
"mcp__tools-py__run_format_code"
"mcp__tools-py__run_lint_imports_check"
"mcp__tools-py__run_vulture_check"
"mcp__tools-py__get_library_source"
```

Place them after the existing `mcp__tools-py__run_mypy_check` entry for logical grouping.

### Remove 3 Bash permissions
```
"Bash(./tools/format_all.sh:*)"
"Bash(./tools/lint_imports.sh:*)"
"Bash(./tools/vulture_check.sh:*)"
```

**Keep:** `"Bash(./tools/ruff_check.sh:*)"` — no MCP equivalent.

## WHAT — CLAUDE.md

### 1. Tool Mapping Table
Add rows for the 4 new MCP tools. Current table has Read/Edit/Write/pytest/pylint/mypy. Add:

| Task | Old | New |
|------|-----|-----|
| Format code | `Bash("./tools/format_all.sh")` | `mcp__tools-py__run_format_code` |
| Lint imports | `Bash("./tools/lint_imports.sh")` | `mcp__tools-py__run_lint_imports_check` |
| Vulture check | `Bash("./tools/vulture_check.sh")` | `mcp__tools-py__run_vulture_check` |
| Get library source | _(new capability)_ | `mcp__tools-py__get_library_source` |

### 2. "Git Operations" section — "MANDATORY: Before ANY commit"
Replace:
```bash
# ALWAYS run format_all before committing
./tools/format_all.sh
```
With:
```
# ALWAYS run format_all before committing
mcp__tools-py__run_format_code
```

### 3. "Format all code before committing" block
Replace `./tools/format_all.sh` reference with `mcp__tools-py__run_format_code`. Update surrounding text to say "Run `mcp__tools-py__run_format_code`" instead of "Run `./tools/format_all.sh`".

### 4. Quick Examples section (❌ WRONG / ✅ CORRECT)
Add format_all.sh to the "WRONG" example and MCP format to the "CORRECT" example if not already there.

## HOW
Pure text edits — no code logic involved.

## ALGORITHM
```
1. Edit settings.local.json: add 4 MCP permissions after mypy entry
2. Edit settings.local.json: remove 3 Bash script permissions
3. Edit CLAUDE.md: add 4 rows to tool mapping table
4. Edit CLAUDE.md: replace format_all.sh in "Before ANY commit" section
5. Edit CLAUDE.md: replace format_all.sh in "Format all code" paragraph
6. Edit CLAUDE.md: update Quick Examples if applicable
7. Run pylint, pytest, mypy (should be no-ops for config files, but verify)
```

## DATA
No data structures. JSON config and markdown content only.

## Verification
```
mcp__tools-py__run_pytest_check(extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration and not langchain_integration"])
mcp__tools-py__run_pylint_check()
mcp__tools-py__run_mypy_check()
```

## LLM Prompt
```
Read pr_info/steps/summary.md and pr_info/steps/step_2.md for full context.

Implement step 2: Update settings.local.json and CLAUDE.md.

1. Read .claude/settings.local.json
2. Add 4 MCP permissions after the mypy entry: run_format_code, run_lint_imports_check, run_vulture_check, get_library_source
3. Remove 3 Bash permissions: format_all.sh, lint_imports.sh, vulture_check.sh
4. Read .claude/CLAUDE.md
5. Add 4 new rows to the tool mapping table (format code, lint imports, vulture, get library source)
6. Replace all format_all.sh references with mcp__tools-py__run_format_code in Git Operations section
7. Update the Quick Examples section to include format_all.sh as "WRONG" and MCP format as "CORRECT"
8. Run all three quality checks
9. Commit: "chore: update settings and CLAUDE.md with MCP tool permissions (#672)"
```
