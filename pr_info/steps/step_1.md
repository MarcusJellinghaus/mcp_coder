# Step 1: Migrate 4 Simplest Skills

> **Reference:** See [summary.md](summary.md) for overall migration context.

## Goal

Migrate `discuss`, `plan_approve`, `implementation_approve`, and `implementation_needs_rework` from `.claude/commands/` to `.claude/skills/*/SKILL.md`. These are the simplest commands: no dynamic injection, no supporting files, no checklist extraction.

## LLM Prompt

```
Read summary.md and this step file.
For each of the 4 skills listed below, read the existing command from .claude/commands/{name}.md,
then create .claude/skills/{name}/SKILL.md with the new frontmatter format.

Transform the frontmatter:
- Replace workflow-stage/suggested-next with: description, disable-model-invocation: true
- Convert allowed-tools to strict format (colon separator, only tools actually used)
- Drop workflow-stage and suggested-next (not supported in skills format)
- Keep the body content unchanged

After creating all 4, verify each SKILL.md has valid YAML frontmatter.
```

## WHERE

| Source | Target |
|--------|--------|
| `.claude/commands/discuss.md` | `.claude/skills/discuss/SKILL.md` |
| `.claude/commands/plan_approve.md` | `.claude/skills/plan_approve/SKILL.md` |
| `.claude/commands/implementation_approve.md` | `.claude/skills/implementation_approve/SKILL.md` |
| `.claude/commands/implementation_needs_rework.md` | `.claude/skills/implementation_needs_rework/SKILL.md` |

## WHAT — Frontmatter Mapping

### discuss
```yaml
# FROM:
workflow-stage: utility
suggested-next: (context-dependent)
# No allowed-tools

# TO:
description: Step-by-step discussion of open questions and suggestions
disable-model-invocation: true
allowed-tools: []
```

### plan_approve
```yaml
# FROM:
allowed-tools: Bash(mcp-coder set-status:*)
workflow-stage: plan-review

# TO:
description: Approve implementation plan and transition to plan-ready status
disable-model-invocation: true
allowed-tools:
  - "Bash(mcp-coder set-status:*)"
```

### implementation_approve
```yaml
# FROM:
allowed-tools: Bash(mcp-coder gh-tool set-status:*)
workflow-stage: code-review

# TO:
description: Approve implementation and transition issue to PR-ready state
disable-model-invocation: true
allowed-tools:
  - "Bash(mcp-coder gh-tool set-status:*)"
```

### implementation_needs_rework
```yaml
# FROM:
allowed-tools: Bash(mcp-coder set-status:*)
workflow-stage: code-review

# TO:
description: Return issue to plan-ready status for re-implementation after major review issues
disable-model-invocation: true
allowed-tools:
  - "Bash(mcp-coder set-status:*)"
```

## HOW

1. Create each skill directory under `.claude/skills/`
2. Write `SKILL.md` with new frontmatter + original body content (unchanged)
3. No imports, no integrations — pure file creation

## ALGORITHM

```
for each skill in [discuss, plan_approve, implementation_approve, implementation_needs_rework]:
    content = read .claude/commands/{skill}.md
    new_frontmatter = transform_frontmatter(content)  # see mapping above
    body = extract_body(content)  # everything after frontmatter
    write .claude/skills/{skill}/SKILL.md = new_frontmatter + body
```

## DATA

- Input: 4 existing `.md` command files
- Output: 4 new `SKILL.md` files in skill directories
- No return values or data structures (file operation only)

## Commit Message

```
feat: migrate simple skills to skills format

Migrate discuss, plan_approve, implementation_approve, and
implementation_needs_rework from .claude/commands/ to .claude/skills/.
New SKILL.md format with description, disable-model-invocation,
and strict allowed-tools.
```
