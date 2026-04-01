# Step 2: Add MCP tool references to documentation

## References
- [Summary](summary.md)
- Issue #672

## WHERE
- `docs/repository-setup.md`
- `docs/configuration/claude-code.md`
- `docs/processes-prompts/refactoring-guide.md`
- `docs/architecture/dependencies/readme.md`

## WHAT

Add brief inline MCP tool notes. No subsection restructuring — keep changes minimal.

### docs/repository-setup.md

**"Running Architecture Tools" section** — After the "Recommended Approach: Use Tools Scripts" paragraph, add a note:

```markdown
> **Claude Code users:** MCP equivalents are available — `mcp__tools-py__run_format_code`, `mcp__tools-py__run_lint_imports_check`, `mcp__tools-py__run_vulture_check`. See `.claude/CLAUDE.md` for the full tool mapping.
```

**Formatting Tools table** — Add a note after the `format_all.sh/bat` row or in the description:

```markdown
> **Claude Code:** Use `mcp__tools-py__run_format_code` instead of the shell script.
```

### docs/configuration/claude-code.md

**Permissions JSON example** — Replace:
```json
"Bash(./tools/format_all.sh:*)",
```
With:
```json
"mcp__tools-py__run_format_code",
```

**Security considerations bullet** — Replace:
```
- **Allow formatting tools**: `Bash(./tools/format_all.sh:*)` for code formatting
```
With:
```
- **Allow formatting tools**: `mcp__tools-py__run_format_code` for code formatting
```

### docs/processes-prompts/refactoring-guide.md

**"Standard Checks" section** — Add MCP equivalents inline:

```markdown
# Import structure
./tools/lint_imports.sh          # humans/CI
./tools/tach_check.sh

# Functionality (Claude Code MCP tools)
mcp__tools-py__run_pytest_check
mcp__tools-py__run_pylint_check
mcp__tools-py__run_mypy_check
mcp__tools-py__run_lint_imports_check   # MCP equivalent of lint_imports.sh
mcp__tools-py__run_vulture_check        # MCP equivalent of vulture_check.sh
```

### docs/architecture/dependencies/readme.md

**Tools table** — Add a note after the table:

```markdown
> **Claude Code users:** MCP equivalents exist for `lint_imports.sh` (`mcp__tools-py__run_lint_imports_check`) and `vulture_check.sh` (`mcp__tools-py__run_vulture_check`). See `.claude/CLAUDE.md`.
```

## HOW

Edit markdown files. Add blockquote notes or inline comments — no structural changes.

## DATA

No code logic — documentation only.

## Verification

- All 4 files edited
- MCP tool names are spelled correctly
- Existing content is preserved
- Shell script references remain for humans/CI
- No broken markdown formatting

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_2.md for context.

Edit 4 documentation files to add brief MCP tool references:
1. `docs/repository-setup.md` — Add note after "Running Architecture Tools" section and formatting tools table
2. `docs/configuration/claude-code.md` — Update permissions example and security bullet (format_all.sh → MCP tool)
3. `docs/processes-prompts/refactoring-guide.md` — Add MCP equivalents to "Standard Checks" section
4. `docs/architecture/dependencies/readme.md` — Add note after tools table

Find the closest matching section if exact section names differ slightly from what's listed here. Keep changes minimal — inline notes, not subsection restructuring. Shell script references stay for humans/CI. Run code quality checks. Commit as: "docs: add MCP tool references to documentation"
```
