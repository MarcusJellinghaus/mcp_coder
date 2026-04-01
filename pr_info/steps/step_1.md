# Step 1: Update settings.local.json permissions and skill files

## References
- [Summary](summary.md)
- Issue #672

## WHERE
- `.claude/settings.local.json`
- `.claude/skills/commit_push/SKILL.md`
- `.claude/skills/implement_direct/SKILL.md`
- `.claude/skills/rebase/SKILL.md`

## WHAT

### settings.local.json

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

1. Edit `settings.local.json` — update the `permissions.allow` array, placing new MCP entries next to existing `mcp__tools-py__*` entries
2. Edit 3 skill YAML frontmatter `allowed-tools` lists and markdown instruction text

## DATA

No code logic — JSON configuration and SKILL.md files only.

## Verification

- `settings.local.json` is valid JSON after edit
- 4 new MCP entries present, 3 old Bash entries removed
- Other permissions unchanged (especially `ruff_check.sh` which stays)
- YAML frontmatter parses correctly in all 3 skills (no broken `---` boundaries)
- `mcp__tools-py__run_format_code` appears in all 3 skills' allowed-tools
- No references to `format_all.sh` or `format_all.bat` remain in any skill
- `ruff_check.sh` reference in implement_direct step 5 is unchanged

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_1.md for context.

Edit `.claude/settings.local.json`:
1. Add 4 MCP permissions (run_format_code, run_lint_imports_check, run_vulture_check, get_library_source) — group them with existing mcp__tools-py entries
2. Remove 3 Bash permissions (format_all.sh, lint_imports.sh, vulture_check.sh)
3. Keep all other permissions unchanged (ruff_check.sh stays)
4. Verify valid JSON

Edit 3 skill files to replace format_all.sh/.bat with mcp__tools-py__run_format_code:
1. `.claude/skills/commit_push/SKILL.md` — Update allowed-tools (remove 2 Bash entries, add MCP tool) and update step 1 instructions
2. `.claude/skills/implement_direct/SKILL.md` — Add MCP tool to allowed-tools (it was missing), replace the bash code block in step 6 with a plain-text instruction (e.g., 'Run `mcp__tools-py__run_format_code` to format all code.')
3. `.claude/skills/rebase/SKILL.md` — Update allowed-tools only (remove 2 Bash entries, add MCP tool)

Keep ruff_check.sh references unchanged. Run code quality checks. Commit as: "chore: update permissions and skills for MCP tool replacements"
```
