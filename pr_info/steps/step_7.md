# Step 7: Migrate plan_review_supervisor with Workflow Extraction

> **Reference:** See [summary.md](summary.md) for overall migration context.

## Goal

Migrate `plan_review_supervisor` and extract the supervisor workflow into a separate `supervisor_workflow.md` file (Decision #4). The SKILL.md keeps the role description, setup, and skill-specific context. The extracted file contains the reusable workflow steps and log format.

## LLM Prompt

```
Read summary.md and this step file.

1. Read .claude/commands/plan_review_supervisor.md
2. Create .claude/skills/plan_review_supervisor/SKILL.md with:
   - New frontmatter
   - Role description, setup instructions, prerequisites
   - Reference to supervisor_workflow.md for workflow steps
3. Create .claude/skills/plan_review_supervisor/supervisor_workflow.md with:
   - The numbered workflow steps (1-8)
   - Review log format template
   - Subagent instructions and escalation rules
```

## WHERE

| Source | Target |
|--------|--------|
| `.claude/commands/plan_review_supervisor.md` | `.claude/skills/plan_review_supervisor/SKILL.md` |
| (extracted from above) | `.claude/skills/plan_review_supervisor/supervisor_workflow.md` |

## WHAT — Frontmatter

### plan_review_supervisor SKILL.md
```yaml
---
description: Autonomous plan review — supervisor delegates to engineer subagents
disable-model-invocation: true
allowed-tools:
  - "Bash(gh issue view *)"
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
- Everything before the `**Workflow:**` heading (title, role introduction, setup, Your Role, prerequisites, additional context)
- A reference line at the end: `For the detailed workflow steps, see supervisor_workflow.md in this skill directory.`

**supervisor_workflow.md gets:**
- Everything from the `**Workflow:**` heading through the end of the file (numbered workflow steps 1-8, review log format, subagent instructions, escalation rules)

## HOW

1. Create `.claude/skills/plan_review_supervisor/` directory
2. Read existing command file
3. Split content: role/setup/prerequisites → SKILL.md, workflow/format/instructions → supervisor_workflow.md
4. Add reference from SKILL.md to supervisor_workflow.md
5. Write both files

## ALGORITHM

```
content = read .claude/commands/plan_review_supervisor.md
skill_content = extract_sections(content, ["title", "setup", "your_role", "prerequisites", "additional_context"])
workflow_content = extract_sections(content, ["workflow", "review_log_format", "subagent_instructions", "escalation"])
skill_content += "\nFor the detailed workflow steps, see supervisor_workflow.md in this skill directory.\n"
write .claude/skills/plan_review_supervisor/SKILL.md = frontmatter + skill_content
write .claude/skills/plan_review_supervisor/supervisor_workflow.md = workflow_content
```

## DATA

- Input: 1 command file
- Output: 2 files (SKILL.md + supervisor_workflow.md)

## Acceptance Criteria

- SKILL.md and supervisor_workflow.md both created
- **Content verification**: The combined content of SKILL.md + supervisor_workflow.md must be equivalent to the original `.claude/commands/plan_review_supervisor.md` body. Only frontmatter changes and the split itself are expected — no content should be added, removed, or reworded.

## Commit Message

```
feat: migrate plan_review_supervisor to skills format

Extract supervisor workflow steps and log format into
supervisor_workflow.md. SKILL.md keeps role description,
setup, and prerequisites.
```
