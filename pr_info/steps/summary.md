# Summary: Migrate Commands to Skills Format (#500)

## Overview

Migrate all 18 slash commands from `.claude/commands/*.md` to the new `.claude/skills/*/SKILL.md` format with YAML frontmatter. This enables structured metadata (`allowed-tools`, `argument-hint`, `disable-model-invocation`), dynamic context injection, and supporting files for complex skills.

## Architectural / Design Changes

### Before: Flat command files

```
.claude/commands/
├── discuss.md
├── issue_analyse.md
├── rebase.md
├── rebase_design.md.txt
└── ... (18 command files + 1 design doc)
```

- Flat directory with one `.md` file per command
- Frontmatter: `workflow-stage`, `suggested-next`, `allowed-tools`
- No dynamic context injection
- No supporting files (design docs use `.txt` suffix hack to avoid execution)
- No `disable-model-invocation` control

### After: Structured skill directories

```
.claude/skills/
├── discuss/
│   └── SKILL.md
├── rebase/
│   ├── SKILL.md
│   └── rebase_design.md          (supporting file, not auto-loaded)
├── plan_review_supervisor/
│   ├── SKILL.md
│   └── supervisor_workflow.md    (extracted workflow reference)
├── implementation_review_supervisor/
│   ├── SKILL.md
│   └── supervisor_workflow.md    (extracted workflow reference)
└── ... (18 skill directories total)
```

- One directory per skill with `SKILL.md` as entry point
- New frontmatter: `description`, `disable-model-invocation: true`, strict `allowed-tools`, optional `argument-hint`
- Dynamic context injection via `` !`command $ARGUMENTS` `` syntax for 4 skills
- Supporting files for complex skills (non-auto-loaded)
- `workflow-stage` and `suggested-next` fields removed (not supported in skills format)

### Key Design Decisions (from issue #500)

| # | Decision |
|---|----------|
| 1 | Keep underscore naming (e.g., `issue_analyse`) — minimize churn |
| 2 | `commit-pusher` agent stays in `.claude/agents/` — skills don't support `bypassPermissions` |
| 3 | `rebase_design.md.txt` → `skills/rebase/rebase_design.md` as non-referenced supporting file |
| 4 | Checklist extraction only for `implementation_review_supervisor` and `plan_review_supervisor` |
| 7 | `disable-model-invocation: true` on all skills |
| 8 | Strict `allowed-tools` — only tools each skill actually uses |
| 12 | Remove redundant fetch/command instructions from body when dynamic injection handles it |
| 14 | Add missing `Skill(plan_review_supervisor)` to `settings.local.json` |

### What stays unchanged

- `.claude/agents/commit-pusher.md` — unchanged
- `.claude/CLAUDE.md` — unchanged (skills are auto-discovered)
- `.claude/knowledge_base/` — unchanged
- All Python source code — unchanged (no code changes in this migration)
- `settings.local.json` Skill() permission names — already use skill names

## Files Created

| Directory | Files |
|-----------|-------|
| `.claude/skills/discuss/` | `SKILL.md` |
| `.claude/skills/implementation_approve/` | `SKILL.md` |
| `.claude/skills/implementation_needs_rework/` | `SKILL.md` |
| `.claude/skills/plan_approve/` | `SKILL.md` |
| `.claude/skills/issue_create/` | `SKILL.md` |
| `.claude/skills/issue_update/` | `SKILL.md` |
| `.claude/skills/plan_update/` | `SKILL.md` |
| `.claude/skills/issue_analyse/` | `SKILL.md` |
| `.claude/skills/issue_approve/` | `SKILL.md` |
| `.claude/skills/check_branch_status/` | `SKILL.md` |
| `.claude/skills/plan_review/` | `SKILL.md` |
| `.claude/skills/implementation_review/` | `SKILL.md` |
| `.claude/skills/implementation_finalise/` | `SKILL.md` |
| `.claude/skills/implementation_new_tasks/` | `SKILL.md` |
| `.claude/skills/commit_push/` | `SKILL.md` |
| `.claude/skills/rebase/` | `SKILL.md`, `rebase_design.md` |
| `.claude/skills/plan_review_supervisor/` | `SKILL.md`, `supervisor_workflow.md` |
| `.claude/skills/implementation_review_supervisor/` | `SKILL.md`, `supervisor_workflow.md` |

## Files Modified

- `.claude/settings.local.json` — add `Skill(plan_review_supervisor)`
- `docs/processes-prompts/claude_cheat_sheet.md` — update command references
- `docs/processes-prompts/development-process.md` — update command references
- `docs/configuration/claude-code.md` — update directory structure and references

## Files Deleted

- `.claude/commands/` — entire directory (18 `.md` files + `rebase_design.md.txt`)

## SKILL.md Template

```yaml
---
description: One-line description
disable-model-invocation: true
allowed-tools:
  - Tool1
  - Tool2
argument-hint: "<hint>"  # optional, only on skills that take arguments
---

# Skill Title

Instructions here...
```

## Implementation Steps

| Step | Description | Commit |
|------|-------------|--------|
| 1 | Migrate 4 simplest skills: discuss, plan_approve, implementation_approve, implementation_needs_rework | `feat: migrate simple skills to skills format` |
| 2 | Migrate 3 skills: issue_create, issue_update, plan_update | `feat: migrate issue_create, issue_update, plan_update to skills format` |
| 3 | Migrate 3 skills with dynamic injection: issue_analyse, issue_approve, check_branch_status | `feat: migrate skills with dynamic context injection` |
| 4 | Migrate 3 review skills: plan_review, implementation_review, implementation_finalise | `feat: migrate review and finalise skills` |
| 5 | Migrate 2 remaining skills: implementation_new_tasks, commit_push | `feat: migrate implementation_new_tasks and commit_push skills` |
| 6 | Migrate rebase + move rebase_design.md | `feat: migrate rebase skill with design document` |
| 7 | Migrate plan_review_supervisor + extract supervisor_workflow.md | `feat: migrate plan_review_supervisor skill` |
| 8 | Migrate implementation_review_supervisor + extract supervisor_workflow.md | `feat: migrate implementation_review_supervisor skill` |
| 9 | Update settings.local.json + 3 documentation files | `docs: update references from commands to skills` |
| 10 | Delete old .claude/commands/ directory | `chore: remove old commands directory` |

## Notes

- **No Python code changes** — this is purely a file migration of markdown/YAML config
- **No tests to write** — TDD not applicable; verification is manual (invoke each skill)
- **No code quality checks needed** — no `.py` files are modified
- `disable-model-invocation: true` prevents auto-loading but supervisors can still call skills via `Skill()` tool
- Dynamic injection syntax: `` !`command $ARGUMENTS` `` runs at invocation time
