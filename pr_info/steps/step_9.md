# Step 9: Update settings.local.json and Documentation

> **Reference:** See [summary.md](summary.md) for overall migration context.

## Goal

Update configuration and documentation to reference the new `.claude/skills/` structure instead of `.claude/commands/`. Add missing `Skill(plan_review_supervisor)` to local `settings.local.json` (Decision #14).

## LLM Prompt

```
Read summary.md and this step file.

1. Edit .claude/settings.local.json — add "Skill(plan_review_supervisor)" if missing
2. Edit docs/configuration/claude-code.md — update directory structure and references
3. Edit docs/processes-prompts/claude_cheat_sheet.md — update command references
4. Edit docs/processes-prompts/development-process.md — update command path references

For all docs: replace .claude/commands/ with .claude/skills/ in path references.
Update the directory structure example in claude-code.md to show the new skills/ layout.
Preserve all other content unchanged.
```

## WHERE

| File | Change Type |
|------|-------------|
| `.claude/settings.local.json` | Add missing permission |
| `docs/configuration/claude-code.md` | Update references |
| `docs/processes-prompts/claude_cheat_sheet.md` | Update references |
| `docs/processes-prompts/development-process.md` | Update references |

## WHAT — Specific Changes

### .claude/settings.local.json

Add `"Skill(plan_review_supervisor)"` to the `permissions.allow` array if not already present. (In the local project's settings.local.json, this entry is currently missing — Decision #14.)

### docs/configuration/claude-code.md

1. Update the directory structure example:
```
# FROM:
├── .claude/
│   ├── CLAUDE.md
│   ├── settings.local.json
│   └── commands/
│       ├── commit_push.md
│       ├── plan_review.md
│       └── ...

# TO:
├── .claude/
│   ├── CLAUDE.md
│   ├── settings.local.json
│   └── skills/
│       ├── commit_push/
│       │   └── SKILL.md
│       ├── plan_review/
│       │   └── SKILL.md
│       └── ...
```

2. Update section heading from "`.claude/commands/` - Slash Commands" to "`.claude/skills/` - Skills"
3. Update the description text to reference skills instead of slash commands
4. Update the command table if it references file paths

### docs/processes-prompts/claude_cheat_sheet.md

- No structural changes needed (commands are referenced by `/name` not by path)
- If any file paths reference `.claude/commands/`, update to `.claude/skills/`

### docs/processes-prompts/development-process.md

- Update all `(.claude/commands/...)` path references to `(.claude/skills/.../SKILL.md)`
- Example: `[.claude/commands/issue_analyse.md](../../.claude/commands/issue_analyse.md)` → `[.claude/skills/issue_analyse/SKILL.md](../../.claude/skills/issue_analyse/SKILL.md)`
- Keep all other content (prompts, workflows, mermaid diagrams) unchanged

## HOW

1. Edit `settings.local.json` to add the missing permission entry
2. For each doc file: find-and-replace `.claude/commands/{name}.md` → `.claude/skills/{name}/SKILL.md`
3. Update the directory structure example in `claude-code.md`

## ALGORITHM

```
# settings.local.json
settings = read .claude/settings.local.json
if "Skill(plan_review_supervisor)" not in settings.permissions.allow:
    add it to the allow list
write settings

# docs — batch find-and-replace
for each doc in [claude-code.md, claude_cheat_sheet.md, development-process.md]:
    content = read doc
    content = replace_all(".claude/commands/", ".claude/skills/")
    content = replace_all("{name}.md", "{name}/SKILL.md")  # for path references
    # Special: update directory structure in claude-code.md
    write doc
```

## DATA

- Input: 4 files to modify
- Output: 4 modified files

## Commit Message

```
chore: update config and docs for skills migration
```
