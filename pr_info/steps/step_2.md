# Step 2: Replace format_all.sh with MCP tool in skills

## References
- [Summary](summary.md)
- Issue #672

## WHERE
- `.claude/skills/commit_push/SKILL.md`
- `.claude/skills/implement_direct/SKILL.md`
- `.claude/skills/rebase/SKILL.md`

## WHAT

### commit_push/SKILL.md

**allowed-tools** — Remove:
```
- "Bash(./tools/format_all.sh *)"
- "Bash(tools/format_all.bat *)"
```
Add:
```
- mcp__tools-py__run_format_code
```

**Step 1 instructions** — Replace the bash block `./tools/format_all.sh` with:
```
Run `mcp__tools-py__run_format_code` to format all code.
```

### implement_direct/SKILL.md

**allowed-tools** — Add (was missing entirely — issue decision #6):
```
- mcp__tools-py__run_format_code
```

**Step 6** — Replace:
```bash
./tools/format_all.sh
```
With reference to `mcp__tools-py__run_format_code`.

### rebase/SKILL.md

**allowed-tools** — Remove:
```
- "Bash(./tools/format_all.sh *)"
- "Bash(tools/format_all.bat *)"
```
Add:
```
- mcp__tools-py__run_format_code
```

No instruction text changes needed — format_all.sh is only in allowed-tools, not in the workflow text.

## HOW

Edit YAML frontmatter `allowed-tools` lists and markdown instruction text.

## DATA

No code logic — SKILL.md configuration only.

## Verification

- YAML frontmatter parses correctly (no broken `---` boundaries)
- `mcp__tools-py__run_format_code` appears in all 3 skills' allowed-tools
- No references to `format_all.sh` or `format_all.bat` remain in any skill
- `ruff_check.sh` reference in implement_direct step 5 is unchanged

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_2.md for context.

Edit 3 skill files to replace format_all.sh/.bat with mcp__tools-py__run_format_code:

1. `.claude/skills/commit_push/SKILL.md` — Update allowed-tools (remove 2 Bash entries, add MCP tool) and update step 1 instructions
2. `.claude/skills/implement_direct/SKILL.md` — Add MCP tool to allowed-tools (it was missing), update step 6 instructions
3. `.claude/skills/rebase/SKILL.md` — Update allowed-tools only (remove 2 Bash entries, add MCP tool)

Keep ruff_check.sh references unchanged. Run code quality checks. Commit as: "chore: replace format_all.sh with MCP tool in skills"
```
