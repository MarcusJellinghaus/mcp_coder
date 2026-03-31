# Step 4: Migrate plan_review, implementation_review, implementation_finalise

> **Reference:** See [summary.md](summary.md) for overall migration context.

## Goal

Migrate 3 review/quality skills. These are read-heavy skills with specific tool requirements but no dynamic injection or file extraction.

## LLM Prompt

```
Read summary.md and this step file.
For each of the 3 skills listed below, read the existing command from .claude/commands/{name}.md,
then create .claude/skills/{name}/SKILL.md with the new frontmatter format.

Convert allowed-tools carefully — replace Read/Glob/Grep with MCP workspace equivalents.
Keep body content unchanged.
```

## WHERE

| Source | Target |
|--------|--------|
| `.claude/commands/plan_review.md` | `.claude/skills/plan_review/SKILL.md` |
| `.claude/commands/implementation_review.md` | `.claude/skills/implementation_review/SKILL.md` |
| `.claude/commands/implementation_finalise.md` | `.claude/skills/implementation_finalise/SKILL.md` |

## WHAT — Frontmatter Mapping

### plan_review
```yaml
# FROM:
allowed-tools: Bash(git fetch *), Bash(git status *), Read, Glob, Grep
workflow-stage: plan-review

# TO:
description: Review implementation plan for completeness, simplicity, and risks
disable-model-invocation: true
allowed-tools:
  - "Bash(git fetch *)"
  - "Bash(git status *)"
  - mcp__workspace__read_file
  - mcp__workspace__list_directory
```

### implementation_review
```yaml
# FROM:
allowed-tools: Bash(git fetch *), Bash(git status *), Bash(git diff *), Bash(mcp-coder git-tool compact-diff *), Bash(mcp-coder check branch-status *), Read, Glob, Grep
workflow-stage: code-review

# TO:
description: Code review of implementation with compact diff analysis
disable-model-invocation: true
allowed-tools:
  - "Bash(git fetch *)"
  - "Bash(git status *)"
  - "Bash(git diff *)"
  - "Bash(mcp-coder git-tool *)"
  - "Bash(mcp-coder check branch-status *)"
  - mcp__workspace__read_file
  - mcp__workspace__list_directory
```

### implementation_finalise
```yaml
# FROM:
workflow-stage: utility
# No allowed-tools listed

# TO:
description: Complete remaining unchecked tasks in the task tracker
disable-model-invocation: true
# No allowed-tools — intentionally unrestricted because this skill performs arbitrary implementation work.
```

## HOW

1. Create each skill directory
2. Write `SKILL.md` with transformed frontmatter + unchanged body
3. Replace `Read`, `Glob`, `Grep` references in allowed-tools with MCP workspace equivalents

## ALGORITHM

```
for each skill in [plan_review, implementation_review, implementation_finalise]:
    content = read .claude/commands/{skill}.md
    new_frontmatter = transform_frontmatter(content)
    body = extract_body(content)
    write .claude/skills/{skill}/SKILL.md = new_frontmatter + body
```

## DATA

- Input: 3 existing `.md` command files
- Output: 3 new `SKILL.md` files

## Acceptance Criteria

- All 3 SKILL.md files have valid YAML frontmatter
- **Content verification**: Compare each migrated SKILL.md body against the original `.claude/commands/<name>.md` body. The content must be equivalent — only these changes are expected:
  - Frontmatter fields changed (`workflow-stage`/`suggested-next` removed, `description`/`disable-model-invocation`/`allowed-tools` added)
  - No other content should be added, removed, or reworded

## Commit Message

```
feat: migrate review and finalise skills to skills format

Migrate plan_review, implementation_review, implementation_finalise.
Replace Read/Glob/Grep with MCP workspace tools in allowed-tools.
```
