# Step 3: Skills — replace format_all.sh with MCP tool

## Context
See `pr_info/steps/summary.md` for full issue context.

Update three skill files to use `mcp__tools-py__run_format_code` instead of `./tools/format_all.sh` / `tools/format_all.bat`.

## WHERE
- `.claude/skills/commit_push/SKILL.md`
- `.claude/skills/implement_direct/SKILL.md`
- `.claude/skills/rebase/SKILL.md`

## WHAT — commit_push/SKILL.md

### allowed-tools (YAML frontmatter)
Remove:
```yaml
- "Bash(./tools/format_all.sh *)"
- "Bash(tools/format_all.bat *)"
```
Add:
```yaml
- mcp__tools-py__run_format_code
```

### Step 1 instructions
Replace:
```bash
./tools/format_all.sh
```
With:
```
mcp__tools-py__run_format_code
```

## WHAT — implement_direct/SKILL.md

### allowed-tools (YAML frontmatter)
Add (currently missing — format was invoked via Bash without explicit permission):
```yaml
- mcp__tools-py__run_format_code
```

### Step 6 instructions
Replace:
```bash
./tools/format_all.sh
```
With:
```
mcp__tools-py__run_format_code
```

## WHAT — rebase/SKILL.md

### allowed-tools (YAML frontmatter)
Remove:
```yaml
- "Bash(./tools/format_all.sh *)"
- "Bash(tools/format_all.bat *)"
```
Add:
```yaml
- mcp__tools-py__run_format_code
```

### Workflow body
No explicit format_all.sh reference in the workflow steps (only in allowed-tools). No body changes needed.

## HOW
Pure text edits in markdown frontmatter and instruction sections.

## ALGORITHM
```
1. Edit commit_push/SKILL.md: swap allowed-tools entries, update step 1
2. Edit implement_direct/SKILL.md: add MCP tool to allowed-tools, update step 6
3. Edit rebase/SKILL.md: swap allowed-tools entries
4. Run quality checks
```

## DATA
No data structures. Markdown/YAML content only.

## Verification
```
mcp__tools-py__run_pytest_check(extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration and not langchain_integration"])
mcp__tools-py__run_pylint_check()
mcp__tools-py__run_mypy_check()
```

## LLM Prompt
```
Read pr_info/steps/summary.md and pr_info/steps/step_3.md for full context.

Implement step 3: Update three skill files to use MCP format tool.

1. Read and edit .claude/skills/commit_push/SKILL.md:
   - Replace format_all.sh/.bat in allowed-tools with mcp__tools-py__run_format_code
   - Replace ./tools/format_all.sh in step 1 with mcp__tools-py__run_format_code
2. Read and edit .claude/skills/implement_direct/SKILL.md:
   - Add mcp__tools-py__run_format_code to allowed-tools
   - Replace ./tools/format_all.sh in step 6 with mcp__tools-py__run_format_code
3. Read and edit .claude/skills/rebase/SKILL.md:
   - Replace format_all.sh/.bat in allowed-tools with mcp__tools-py__run_format_code
4. Run all three quality checks
5. Commit: "chore: replace format_all.sh with MCP tool in skills (#672)"
```
