# Step 6: Migrate rebase Skill with Design Document

> **Reference:** See [summary.md](summary.md) for overall migration context.

## Goal

Migrate `rebase` command to skill format. This is the most tool-heavy skill. Additionally, move `rebase_design.md.txt` into the skill directory as `rebase_design.md` (Decision #3). Add `` !`git status` `` dynamic injection and remove the redundant instruction from the body (Decision #12).

## LLM Prompt

```
Read summary.md and this step file.

1. Read .claude/commands/rebase.md and create .claude/skills/rebase/SKILL.md
2. Read .claude/commands/rebase_design.md.txt and save as .claude/skills/rebase/rebase_design.md
3. Add !`git status` dynamic injection after frontmatter
4. Keep ALL operational content (workflow, conflict table, abort rules) in SKILL.md (Decision #13)
5. Remove redundant git status instruction from body since injection handles it
```

## WHERE

| Source | Target |
|--------|--------|
| `.claude/commands/rebase.md` | `.claude/skills/rebase/SKILL.md` |
| `.claude/commands/rebase_design.md.txt` | `.claude/skills/rebase/rebase_design.md` |

## WHAT — Frontmatter

### rebase
```yaml
---
description: Rebase feature branch onto base branch with conflict resolution
disable-model-invocation: true
allowed-tools:
  - "Bash(git status *)"
  - "Bash(git log *)"
  - "Bash(git branch *)"
  - "Bash(git ls-files *)"
  - "Bash(git fetch *)"
  - "Bash(git rebase *)"
  - "Bash(git add *)"
  - "Bash(git rm *)"
  - "Bash(git commit *)"
  - "Bash(git checkout --ours *)"
  - "Bash(git checkout --theirs *)"
  - "Bash(git remote get-url *)"
  - "Bash(git restore *)"
  - "Bash(git stash *)"
  - "Bash(git push --force-with-lease *)"
  - "Bash(git diff *)"
  - "Bash(git rev-parse *)"
  - "Bash(gh run view *)"
  - "Bash(gh issue view *)"
  - "Bash(./tools/format_all.sh *)"
  - "Bash(tools/format_all.bat *)"
  - "Bash(mcp-coder gh-tool get-base-branch *)"
  - mcp__tools-py__run_pylint_check
  - mcp__tools-py__run_pytest_check
  - mcp__tools-py__run_mypy_check
  - mcp__workspace__read_file
  - mcp__workspace__save_file
  - mcp__workspace__edit_file
  - mcp__workspace__list_directory
  - mcp__workspace__get_reference_projects
  - mcp__workspace__list_reference_directory
  - mcp__workspace__read_reference_file
  - mcp__workspace__append_file
  - mcp__workspace__delete_this_file
  - mcp__workspace__move_file
---

!`git status`
```

### rebase_design.md

Copy `.claude/commands/rebase_design.md.txt` as-is to `.claude/skills/rebase/rebase_design.md` (just rename, no content change). This is a non-referenced supporting file — it won't auto-load but is available for manual reference.

## HOW

1. Create `.claude/skills/rebase/` directory
2. Write `SKILL.md` with new frontmatter + dynamic injection + body
3. Copy `rebase_design.md.txt` → `rebase_design.md` (content unchanged)
4. Remove redundant pre-flight git status instruction from body (Decision #12 — the `` !`git status` `` injection already provides this context)

## ALGORITHM

```
rebase_content = read .claude/commands/rebase.md
new_frontmatter = build_rebase_frontmatter()  # see above
injection = "!`git status`\n"
body = extract_body(rebase_content)
body = remove_redundant_git_status_instruction(body)
write .claude/skills/rebase/SKILL.md = new_frontmatter + injection + body

design_doc = read .claude/commands/rebase_design.md.txt
write .claude/skills/rebase/rebase_design.md = design_doc
```

## DATA

- Input: 2 files (`rebase.md`, `rebase_design.md.txt`)
- Output: 2 files (`SKILL.md`, `rebase_design.md`)

## Acceptance Criteria

- SKILL.md has valid YAML frontmatter and dynamic injection line
- `rebase_design.md` copied with content unchanged
- **Content verification**: Compare the migrated SKILL.md body against the original `.claude/commands/rebase.md` body. The content must be equivalent — only these changes are expected:
  - Frontmatter fields changed (`workflow-stage`/`suggested-next` removed, `description`/`disable-model-invocation`/`allowed-tools` added)
  - Dynamic injection line added (replaces manual git status instruction per Decision #12)
  - No other content should be added, removed, or reworded

## Commit Message

```
feat: migrate rebase skill with design document

Move rebase_design.md.txt into skill directory as rebase_design.md.
Add !`git status` dynamic injection. Keep all operational content
(workflow, conflict table, abort rules) inline in SKILL.md.
```
