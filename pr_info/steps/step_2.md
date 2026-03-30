# Step 2: Migrate issue_create, issue_update, plan_update

> **Reference:** See [summary.md](summary.md) for overall migration context.

## Goal

Migrate `issue_create`, `issue_update`, and `plan_update`. These skills use tools and/or `argument-hint` but no dynamic context injection.

## LLM Prompt

```
Read summary.md and this step file.
For each of the 3 skills listed below, read the existing command from .claude/commands/{name}.md,
then create .claude/skills/{name}/SKILL.md with the new frontmatter format.

- issue_create and issue_update take an argument (issue number or title) — add argument-hint
- Convert allowed-tools to strict colon-separated format
- Keep body content unchanged
```

## WHERE

| Source | Target |
|--------|--------|
| `.claude/commands/issue_create.md` | `.claude/skills/issue_create/SKILL.md` |
| `.claude/commands/issue_update.md` | `.claude/skills/issue_update/SKILL.md` |
| `.claude/commands/plan_update.md` | `.claude/skills/plan_update/SKILL.md` |

## WHAT — Frontmatter Mapping

### issue_create
```yaml
# FROM:
allowed-tools: Bash(gh issue create *)
workflow-stage: issue-discussion

# TO:
description: Create a new GitHub issue from discussion context
disable-model-invocation: true
argument-hint: "<title>"
allowed-tools:
  - "Bash(gh issue create:*)"
  - "Bash(git ls-remote:*)"
```

### issue_update
```yaml
# FROM:
allowed-tools: Bash(gh issue edit *), Bash(gh issue view *), Read, Glob, Grep, mcp__workspace__save_file, mcp__workspace__delete_this_file
workflow-stage: issue-discussion

# TO:
description: Update GitHub issue with refined content from analysis discussion
disable-model-invocation: true
argument-hint: "<issue-number>"
allowed-tools:
  - "Bash(gh issue edit:*)"
  - "Bash(gh issue view:*)"
  - mcp__workspace__save_file
  - mcp__workspace__delete_this_file
```

Note: `Read`, `Glob`, `Grep` are standard Claude tools that don't need `allowed-tools` entries — they're always available. The MCP workspace tools replace them for file access per CLAUDE.md.

### plan_update
```yaml
# FROM:
workflow-stage: plan-review
# No allowed-tools

# TO:
description: Update implementation plan files based on discussion
disable-model-invocation: true
allowed-tools:
  - mcp__workspace__read_file
  - mcp__workspace__save_file
  - mcp__workspace__edit_file
```

## HOW

1. Create each skill directory under `.claude/skills/`
2. Write `SKILL.md` with new frontmatter + original body content
3. For `issue_create`: add `argument-hint: "<title>"`
4. For `issue_update`: add `argument-hint: "<issue-number>"`, replace Read/Glob/Grep with MCP tools

## ALGORITHM

```
for each skill in [issue_create, issue_update, plan_update]:
    content = read .claude/commands/{skill}.md
    new_frontmatter = transform_frontmatter(content)  # see mapping above
    body = extract_body(content)
    write .claude/skills/{skill}/SKILL.md = new_frontmatter + body
```

## DATA

- Input: 3 existing `.md` command files
- Output: 3 new `SKILL.md` files in skill directories

## Commit Message

```
feat: migrate issue_create, issue_update, plan_update to skills format

Add argument-hint for issue_create and issue_update.
Convert allowed-tools to strict format with MCP workspace tools.
```
