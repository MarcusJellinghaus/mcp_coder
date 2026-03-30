# Step 8: Migrate implementation_review_supervisor with Workflow Extraction

> **Reference:** See [summary.md](summary.md) for overall migration context.

## Goal

Migrate `implementation_review_supervisor` and extract the supervisor workflow into `supervisor_workflow.md` (Decision #4). Same pattern as step 7 but with code-review-specific content.

## LLM Prompt

```
Read summary.md and this step file.

1. Read .claude/commands/implementation_review_supervisor.md
2. Create .claude/skills/implementation_review_supervisor/SKILL.md with:
   - New frontmatter
   - Role description, setup, prerequisites (including task tracker check)
   - Reference to supervisor_workflow.md
3. Create .claude/skills/implementation_review_supervisor/supervisor_workflow.md with:
   - The numbered workflow steps (1-10)
   - Review log format template
   - Subagent instructions and escalation rules
```

## WHERE

| Source | Target |
|--------|--------|
| `.claude/commands/implementation_review_supervisor.md` | `.claude/skills/implementation_review_supervisor/SKILL.md` |
| (extracted from above) | `.claude/skills/implementation_review_supervisor/supervisor_workflow.md` |

## WHAT — Frontmatter

### implementation_review_supervisor SKILL.md
```yaml
---
description: Autonomous code review — supervisor delegates to engineer subagents with knowledge base
disable-model-invocation: true
allowed-tools:
  - "Bash(gh issue view:*)"
  - "Bash(mcp-coder git-tool:*)"
  - "Bash(mcp-coder check branch-status:*)"
  - mcp__workspace__read_file
  - mcp__workspace__save_file
  - mcp__workspace__edit_file
  - mcp__workspace__list_directory
  - mcp__tools-py__run_pylint_check
  - mcp__tools-py__run_pytest_check
  - mcp__tools-py__run_mypy_check
---
```

### Content Split

**SKILL.md keeps:**
- Title and role introduction
- Setup section (read issue, knowledge base, determine run number)
- Your Role section (Delegate, Triage, Guide, Scope)
- Pre-flight: Task Tracker Check
- Prerequisites (code must exist)
- Additional context note
- Reference line: `For the detailed workflow steps, see supervisor_workflow.md in this skill directory.`

**supervisor_workflow.md gets:**
- The numbered Workflow steps (1-10)
- Review Log Format template
- Subagent instructions
- Escalation rules

## HOW

1. Create `.claude/skills/implementation_review_supervisor/` directory
2. Read existing command file
3. Split content: role/setup/prerequisites → SKILL.md, workflow/format/instructions → supervisor_workflow.md
4. Add reference from SKILL.md to supervisor_workflow.md

## ALGORITHM

```
content = read .claude/commands/implementation_review_supervisor.md
skill_content = extract_sections(content, ["title", "setup", "your_role", "preflight", "prerequisites", "additional_context"])
workflow_content = extract_sections(content, ["workflow", "review_log_format", "subagent_instructions", "escalation"])
skill_content += "\nFor the detailed workflow steps, see supervisor_workflow.md in this skill directory.\n"
write .claude/skills/implementation_review_supervisor/SKILL.md = frontmatter + skill_content
write .claude/skills/implementation_review_supervisor/supervisor_workflow.md = workflow_content
```

## DATA

- Input: 1 command file
- Output: 2 files (SKILL.md + supervisor_workflow.md)

## Commit Message

```
feat: migrate implementation_review_supervisor to skills format

Extract supervisor workflow steps (10-step process) and log format
into supervisor_workflow.md. SKILL.md keeps role description,
setup, task tracker check, and prerequisites.
```
