# Claude Code Cheat Sheet

Quick reference for mcp-coder slash commands and development workflow.

For a complete overview of the process, see [DEVELOPMENT_PROCESS.md](DEVELOPMENT_PROCESS.md).

---

## Overview

| Command | Description |
|---------|-------------|
| `/issue_analyse` | Analyze and discuss a GitHub issue |
| `/issue_create` | Create a new GitHub issue from discussion |
| `/issue_update` | Update issue description with discussed details |
| `/issue_approve` | Approve issue to start planning |
| `/plan_review` | Review the implementation plan |
| `/plan_update` | Update plan files with discussed changes |
| `/plan_approve` | Approve plan to start implementation |
| `/implementation_finalise` | Complete remaining tasks if bot failed<br>to complete implementation plan |
| `/implementation_review` | Review implemented code for issues |
| `/implementation_approve` | Approve code to create PR |
| `/implementation_needs_rework` | Return to implementation for fixes |
| `/implementation_new_tasks` | Add new implementation steps |
| `/commit_push` | Format, commit, and push changes |
| `/discuss` | Step-by-step discussion of open questions |
| `/rebase` | Rebase branch onto main |

---

## General Process

The happy path workflow:

1. **Discuss the issue:** `/issue_analyse` → `/discuss` → `/issue_update` → `/issue_approve`
   > 🤖 *bot: mcp-coder coordinate → `create_plan`*
2. **Review the plan:** `/plan_review` → `/discuss` → `/plan_update` → `/commit_push` → `/plan_approve`
   > 🤖 *bot: mcp-coder coordinate → `implement`*
3. **Review code:** `/implementation_review` → `/discuss` → `/commit_push` → `/implementation_approve`
   > 🤖 *bot: mcp-coder coordinate → `create_pr`*
4. **Merge PR:** Review and merge in GitHub

---

## Issue Discussion

Refine and approve a GitHub issue before planning.

`/issue_analyse` → `/discuss` → `/issue_update` → `/issue_approve`

Or create a new issue:

`/issue_create` → `/discuss` → `/issue_update` → `/issue_approve`

---

## Plan Review

Review and refine the implementation plan.

`/plan_review` → `/discuss` → `/plan_update` → `/commit_push`

**Decision:** Is the plan ready?
  ↳ Yes → `/plan_approve`
  ↳ No, start over → `/clear` → `/plan_review` → `/discuss` → `/plan_update` → `/commit_push` → (repeat until ready)

**Ready when** no new insights from review or comfortable with approach.

---

## Code Review

Review code and either approve or request rework.

`/implementation_review` → `/discuss`

Then either:

- `/implementation_approve`
- `/implementation_new_tasks` → `/commit_push` → `/implementation_needs_rework`

**For smaller changes:** Ask the LLM to fix it directly, verify the change, then `/commit_push`.

---

## Utility Commands

| Command | Use When |
|---------|----------|
| `/discuss` | Need step-by-step Q&A on any topic |
| `/commit_push` | Ready to commit and push changes |
| `/rebase` | Need to rebase branch onto main |
| `/implementation_finalise` | `mcp-coder implement` failed to complete the plan |
