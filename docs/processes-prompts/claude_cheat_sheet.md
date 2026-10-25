# Claude Code Cheat Sheet

Quick reference for mcp-coder slash commands and development workflow.

For a complete overview of the process, see [development-process.md](development-process.md).

---

## Overview

| Command | Description |
|---------|-------------|
| `/issue_analyse` | Analyze and discuss a GitHub issue |
| `/issue_analyse_supervisor` | Analyse an issue autonomously; ends at ready for approval |
| `/issue_create` | Create a new GitHub issue from discussion |
| `/issue_update` | Update issue description with discussed details |
| `/issue_approve` | Approve issue to start planning |
| `/plan_review` | Review the implementation plan |
| `/plan_review_supervisor` | Review the plan autonomously; ends at ready for approval |
| `/plan_update` | Update plan files with discussed changes |
| `/plan_approve` | Approve plan to start implementation |
| `/implementation_finalise` | Complete remaining tasks if `mcp-coder implement` failed to complete the plan |
| `/implementation_review` | Review implemented code (human-supervised) |
| `/implementation_review_supervisor` | Review implemented code (autonomous agent-driven, uses knowledge base) |
| `/implementation_approve` | Approve code to create PR |
| `/implementation_needs_rework` | Return to implementation for fixes |
| `/implementation_new_tasks` | Add new implementation steps |
| `/check_branch_status` | Check CI status, rebase needs and task completion; auto-fix CI |
| `/pr_comment_triage` | Triage new PR comments and review threads: fix, reply or decline, then resolve |
| `/commit_push` | Format, commit, and push changes |
| `/discuss` | Step-by-step Q&A on open questions, on any topic |
| `/rebase` | Rebase branch onto base branch |

---

## Happy Path

1. **Issue discussion:** refine and approve the issue before planning.

   `/issue_analyse` → `/discuss` → `/issue_update` → `/issue_approve`

   New issue instead: `/issue_create` → `/discuss` → `/issue_update` → `/issue_approve`

   > 🤖 *bot: mcp-coder coordinate → `create_plan`*

2. **Plan review:** review and refine the implementation plan.

   `/plan_review` → `/discuss` → `/plan_update` → `/commit_push` → `/plan_approve`

   Not ready? Repeat the review, starting with a cleared context. Ready when a review brings no new insights, or you are comfortable with the approach.

   > 🤖 *bot: mcp-coder coordinate → `implement`*

3. **Code review:** review the code, then approve or request rework.

   - `/implementation_review`: human-supervised. Claude presents findings; you decide what to act on.
   - `/implementation_review_supervisor`: autonomous. Claude supervises subagents and decides from the knowledge base; it escalates to you only when unsure or when a major refactoring is needed.

   Either one → `/discuss`, then:

   - Approve: `/commit_push` → `/implementation_approve`
   - Rework: `/implementation_new_tasks` → `/commit_push` → `/implementation_needs_rework`

   Smaller changes: ask the LLM to fix it directly, verify, then `/commit_push`.

   > 🤖 *bot: mcp-coder coordinate → `create_pr`*

4. **PR follow-up** (while the PR waits at status-10):

   - merge conflict → bot `fix-conflict`
   - failing CI → bot `fix-ci`
   - review comments → `/pr_comment_triage`

   > 🤖 *bot: mcp-coder coordinate → `fix-conflict` / `fix-ci`*

5. **Review and merge:** in GitHub.

---

## Failure labels

`/check_branch_status` is the entry command for every failure label. Exception: `status-17f-tasks` uses `/implementation_finalise`.

Details per label: [failure-handling.md](processes/failure-handling.md).
