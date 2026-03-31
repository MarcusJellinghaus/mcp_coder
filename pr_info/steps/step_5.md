# Step 5: Migrate implementation_new_tasks and commit_push

> **Reference:** See [summary.md](summary.md) for overall migration context.

## Goal

Migrate the last 2 medium-complexity skills. `implementation_new_tasks` creates plan steps. `commit_push` handles the format/commit/push workflow.

## LLM Prompt

```
Read summary.md and this step file.
For each of the 2 skills listed below, read the existing command from .claude/commands/{name}.md,
then create .claude/skills/{name}/SKILL.md with the new frontmatter format.

Both keep all content inline (no extraction). Convert allowed-tools to strict format.
```

## WHERE

| Source | Target |
|--------|--------|
| `.claude/commands/implementation_new_tasks.md` | `.claude/skills/implementation_new_tasks/SKILL.md` |
| `.claude/commands/commit_push.md` | `.claude/skills/commit_push/SKILL.md` |

## WHAT — Frontmatter Mapping

### implementation_new_tasks
```yaml
# FROM:
workflow-stage: code-review
# No allowed-tools listed

# TO:
description: Create additional implementation steps after code review findings
disable-model-invocation: true
allowed-tools:
  - mcp__workspace__read_file
  - mcp__workspace__save_file
  - mcp__workspace__edit_file
  - mcp__workspace__list_directory
```

### commit_push
```yaml
# FROM:
allowed-tools: Bash(git status *), Bash(git diff *), Bash(git add *), Bash(git commit *), Bash(git push *), Bash(git log *), Bash(./tools/format_all.sh), Bash(tools/format_all.bat), Read, Glob, Grep
workflow-stage: utility

# TO:
description: Format code, review changes, commit, and push to remote
disable-model-invocation: true
allowed-tools:
  - "Bash(git status *)"
  - "Bash(git diff *)"
  - "Bash(git add *)"
  - "Bash(git commit *)"
  - "Bash(git push *)"
  - "Bash(git log *)"
  - "Bash(./tools/format_all.sh *)"
  - "Bash(tools/format_all.bat *)"
```

Note: `Read`, `Glob`, `Grep` dropped — commit_push doesn't need file reading tools; it operates on git state.

## HOW

1. Create each skill directory
2. Write `SKILL.md` with transformed frontmatter + unchanged body

## ALGORITHM

```
for each skill in [implementation_new_tasks, commit_push]:
    content = read .claude/commands/{skill}.md
    new_frontmatter = transform_frontmatter(content)
    body = extract_body(content)
    write .claude/skills/{skill}/SKILL.md = new_frontmatter + body
```

## DATA

- Input: 2 existing `.md` command files
- Output: 2 new `SKILL.md` files

## Acceptance Criteria

- Both SKILL.md files have valid YAML frontmatter
- **Content verification**: Compare each migrated SKILL.md body against the original `.claude/commands/<name>.md` body. The content must be equivalent — only these changes are expected:
  - Frontmatter fields changed (`workflow-stage`/`suggested-next` removed, `description`/`disable-model-invocation`/`allowed-tools` added)
  - No other content should be added, removed, or reworded

## Commit Message

```
feat: migrate implementation_new_tasks and commit_push to skills format

Convert allowed-tools to strict format. Drop Read/Glob/Grep from
commit_push (operates on git state only).
```
