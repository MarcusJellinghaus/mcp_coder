# Step 4: Docs — audience-split updates

## Context
See `pr_info/steps/summary.md` for full issue context.

Update four documentation files with audience-split approach: "For Claude Code" shows MCP tools, "For humans/CI" shows shell scripts.

## WHERE
- `docs/repository-setup.md`
- `docs/configuration/claude-code.md`
- `docs/processes-prompts/refactoring-guide.md`
- `docs/architecture/dependencies/readme.md`

## WHAT — docs/repository-setup.md

### "Development Tools > Formatting Tools" table
Add a note below the table:
```markdown
> **For Claude Code:** Use `mcp__tools-py__run_format_code` (runs both isort and black).
> Shell scripts are for human developers and CI pipelines.
```

### "Running Architecture Tools" section
After the "Examples" code block showing shell scripts, add:
```markdown
**For Claude Code**, use MCP tools instead of shell scripts:
- `mcp__tools-py__run_format_code` (replaces `format_all.sh`)
- `mcp__tools-py__run_lint_imports_check` (replaces `lint_imports.sh`)
- `mcp__tools-py__run_vulture_check` (replaces `vulture_check.sh`)
```

### "Enhanced Claude Permissions" bullet
Update the "Architecture Tools" sub-bullet to mention MCP tools as the preferred approach for Claude.

## WHAT — docs/configuration/claude-code.md

### settings.local.json example
The current example shows `"Bash(./tools/format_all.sh:*)"`. Replace with `"mcp__tools-py__run_format_code"`. Add the other 3 new MCP permissions to the example.

### "Allow formatting tools" security note
Update from `Bash(./tools/format_all.sh:*)` to reference MCP tool.

## WHAT — docs/processes-prompts/refactoring-guide.md

### "Standard Checks" section
Currently shows:
```bash
# Import structure
./tools/lint_imports.sh
./tools/tach_check.sh

# Functionality (Claude Code MCP tools)
mcp__tools-py__run_pytest_check
mcp__tools-py__run_pylint_check
mcp__tools-py__run_mypy_check
```

Add MCP alternatives for import structure:
```bash
# Import structure
# For humans/CI:
./tools/lint_imports.sh
./tools/tach_check.sh
# For Claude Code:
mcp__tools-py__run_lint_imports_check
# (tach has no MCP equivalent — use shell script)

# Functionality (Claude Code MCP tools)
mcp__tools-py__run_pytest_check
mcp__tools-py__run_pylint_check
mcp__tools-py__run_mypy_check
```

## WHAT — docs/architecture/dependencies/readme.md

### Tools table
Add a "MCP Tool" column to the existing table:

| Tool | Purpose | Config | Script | MCP Tool |
|------|---------|--------|--------|----------|
| **import-linter** | ... | ... | `tools/lint_imports.sh` | `mcp__tools-py__run_lint_imports_check` |
| **vulture** | ... | ... | `tools/vulture_check.sh` | `mcp__tools-py__run_vulture_check` |
| others | ... | ... | ... | — |

### "Running Checks" section
Add a Claude Code alternative block:
```markdown
**For Claude Code**, use MCP tools:
- `mcp__tools-py__run_lint_imports_check`
- `mcp__tools-py__run_vulture_check`
```

## HOW
Pure documentation edits. No code changes.

## ALGORITHM
```
1. Edit repository-setup.md: add MCP notes to formatting and architecture sections
2. Edit claude-code.md: update settings example and security note
3. Edit refactoring-guide.md: add MCP alternatives to standard checks
4. Edit dependencies/readme.md: add MCP column to tools table, add Claude Code block
5. Run quality checks (should be no-ops for docs)
```

## DATA
No data structures. Markdown content only.

## Verification
```
mcp__tools-py__run_pytest_check(extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration and not langchain_integration"])
mcp__tools-py__run_pylint_check()
mcp__tools-py__run_mypy_check()
```

## LLM Prompt
```
Read pr_info/steps/summary.md and pr_info/steps/step_4.md for full context.

Implement step 4: Update 4 documentation files with audience-split approach.

1. Read and edit docs/repository-setup.md:
   - Add MCP tool notes after formatting tools table and architecture tools examples
2. Read and edit docs/configuration/claude-code.md:
   - Replace format_all.sh in settings example with MCP tools
   - Update security considerations note
3. Read and edit docs/processes-prompts/refactoring-guide.md:
   - Add MCP alternatives in standard checks section
4. Read and edit docs/architecture/dependencies/readme.md:
   - Add MCP Tool column to tools table
   - Add Claude Code alternative in running checks section
5. Run all three quality checks
6. Commit: "docs: add MCP tool references with audience-split approach (#672)"
```
