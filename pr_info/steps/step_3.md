# Step 3: Migrate Skills with Dynamic Context Injection

> **Reference:** See [summary.md](summary.md) for overall migration context.

## Goal

Migrate `issue_analyse`, `issue_approve`, and `check_branch_status`. These 3 skills use dynamic context injection (`` !`command $ARGUMENTS` ``) to auto-fetch data at invocation time. Per Decision #12, remove redundant manual fetch instructions from the body when dynamic injection handles it.

## LLM Prompt

```
Read summary.md and this step file.
For each of the 3 skills listed below, read the existing command from .claude/commands/{name}.md,
then create .claude/skills/{name}/SKILL.md with:
1. New frontmatter with dynamic injection line
2. Body content with redundant fetch instructions REMOVED (Decision #12)

Dynamic injection syntax: place !`command $ARGUMENTS` in the frontmatter block
or as the first line after frontmatter. This runs the command at skill invocation
and injects the output into the context.

For issue_analyse: the body currently says "First, fetch the issue details: gh issue view $ARGUMENTS"
— remove that instruction since dynamic injection handles it.
Similarly for issue_approve and check_branch_status.
```

## WHERE

| Source | Target |
|--------|--------|
| `.claude/commands/issue_analyse.md` | `.claude/skills/issue_analyse/SKILL.md` |
| `.claude/commands/issue_approve.md` | `.claude/skills/issue_approve/SKILL.md` |
| `.claude/commands/check_branch_status.md` | `.claude/skills/check_branch_status/SKILL.md` |

## WHAT — Frontmatter and Injection Mapping

### issue_analyse
```yaml
---
description: Analyse GitHub issue requirements, feasibility, and implementation approaches
disable-model-invocation: true
argument-hint: "<issue-number>"
allowed-tools:
  - "Bash(gh issue view:*)"
  - "Bash(git ls-remote:*)"
  - mcp__workspace__read_file
  - mcp__workspace__list_directory
---

!`gh issue view $ARGUMENTS`
```

**Body changes:** Remove the "First, fetch the issue details" section including the `gh issue view $ARGUMENTS` code block. Keep the fallback instruction about checking `.vscodeclaude_status.txt` if no arguments. Keep all analysis instructions unchanged.

### issue_approve
```yaml
---
description: Approve issue to transition to next workflow status
disable-model-invocation: true
argument-hint: "<issue-number>"
allowed-tools:
  - "Bash(gh issue comment:*)"
  - "Bash(MSYS_NO_PATHCONV=1 gh issue comment:*)"
---

!`gh issue view $ARGUMENTS`
```

**Body changes:** Remove any instruction to manually fetch issue context. Keep the validation steps and the `gh issue comment` command.

### check_branch_status
```yaml
---
description: Check branch readiness including CI, rebase needs, tasks, and labels
disable-model-invocation: true
allowed-tools:
  - "Bash(mcp-coder check branch-status:*)"
---

!`mcp-coder check branch-status --llm-truncate`
```

**Body changes:** Remove the "Usage" section that tells the user to call `mcp-coder check branch-status --ci-timeout 180 --llm-truncate`. Keep the "What This Command Does", "Follow-Up Actions", and other informational sections.

## HOW

1. Create each skill directory
2. Write `SKILL.md` with new frontmatter
3. Add dynamic injection line (`` !`command` ``) immediately after frontmatter
4. Remove redundant fetch/command instructions from body (Decision #12)
5. Keep all other body content unchanged

## ALGORITHM

```
for each skill in [issue_analyse, issue_approve, check_branch_status]:
    content = read .claude/commands/{skill}.md
    new_frontmatter = build_frontmatter(skill)  # see mapping above
    injection_line = get_injection_line(skill)   # !`command...`
    body = extract_body(content)
    body = remove_redundant_fetch_instruction(body)  # Decision #12
    write .claude/skills/{skill}/SKILL.md = new_frontmatter + injection_line + body
```

## DATA

- Input: 3 existing `.md` command files
- Output: 3 new `SKILL.md` files with dynamic injection

## Commit Message

```
feat: migrate skills with dynamic context injection

Migrate issue_analyse, issue_approve, check_branch_status with
dynamic context injection (!`command $ARGUMENTS`).
Remove redundant fetch instructions from body (Decision #12).
```
