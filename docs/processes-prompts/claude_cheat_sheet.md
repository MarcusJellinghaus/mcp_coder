# Claude Code Cheat Sheet

Quick reference for mcp-coder slash commands and development workflow.

For a complete overview of the process, see [development-process.md](development-process.md).

---

## Overview

| Command | Description |
|---------|-------------|
| **Issue discussion** | |
| `/issue_analyse` | Analyze and discuss a GitHub issue |
| `/issue_analyse_supervisor` | Analyse an issue autonomously; ends at ready for approval |
| `/issue_create` | Create a new GitHub issue from discussion |
| `/issue_update` | Update issue description with discussed details |
| `/issue_approve` | Approve issue to start planning |
| **Plan review** | |
| `/plan_review` | Review the implementation plan |
| `/plan_review_supervisor` | Review the plan autonomously; ends at ready for approval |
| `/plan_update` | Update plan files with discussed changes |
| `/plan_approve` | Approve plan to start implementation |
| **Code review / failure handling** | |
| `/implementation_review` | Review implemented code (human-supervised) |
| `/implementation_review_supervisor` | Review implemented code (autonomous agent-driven, uses knowledge base) |
| `/implementation_finalise` | Complete remaining tasks if `mcp-coder implement` failed to complete the plan |
| `/implementation_new_tasks` | Add new implementation steps |
| `/implementation_needs_rework` | Return to implementation for fixes |
| `/implementation_approve` | Approve code to create PR |
| **PR follow-up** | |
| `/pr_comment_triage` | Triage new PR comments and review threads: fix, reply or decline, then resolve |
| `/rebase` | Rebase branch onto base branch |
| **General** | |
| `/discuss` | Step-by-step Q&A on open questions, on any topic |
| `/commit_push` | Format, commit, and push changes |
| `/check_branch_status` | Check CI status, rebase needs and task completion; auto-fix CI |

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

A failure label means an automated step stopped and needs you.

1. Run `/check_branch_status` to see what happened. For `status-17f-tasks`, run `/implementation_finalise` instead.
2. Fix the cause, then restart the stage with the command shown under its heading: `mcp-coder gh-tool set-status <label>`.

Recovery details per label: [failure-handling.md](processes/failure-handling.md).

### Plan creation

Restart with `mcp-coder gh-tool set-status status-02:awaiting-planning`.

| Failure label | Reason |
|---------------|--------|
| `status-03f:planning-failed` | Any other error or crash |
| `status-03f-timeout:planning-llm-timeout` | LLM timeout |
| `status-03f-mcp:planning-mcp-unavailable` | MCP server(s) failed to connect |
| `status-03f-prereq:planning-prereq-failed` | Dirty working dir, issue not found, base branch missing, branch creation failed, or `pr_info/` already exists or could not be created |

### Automated plan review

Restart with `mcp-coder gh-tool set-status status-14:plan-review-bot`.

| Failure label | Reason |
|---------------|--------|
| `status-14f:plan-review-failed` | Generic error or unparseable verdict |
| `status-14f-timeout:plan-review-llm-timeout` | LLM API timeout |
| `status-14f-mcp:plan-review-mcp-unavailable` | MCP server unavailable |

### Implementation

Restart with `mcp-coder gh-tool set-status status-05:plan-ready`.

| Failure label | Reason |
|---------------|--------|
| `status-06f:implementing-failed` | General implementation failure |
| `status-06f-ci:ci-fix-needed` | CI exhausted 3 fix attempts |
| `status-06f-timeout:llm-timeout` | LLM API timeout |
| `status-06f-prep:task-tracker-prep-failed` | Task tracker preparation failed |
| `status-06f-mcp:mcp-unavailable` | MCP server unavailable |
| `status-06f-nochange:no-changes-after-retries` | LLM produced no file changes after 3 retry attempts |
| `status-06f-blocked:implementation-blocked` | Agent could not verify the work and refused to claim it (`pr_info/.blocked.txt`) |

### Automated code review

Restart with `mcp-coder gh-tool set-status status-17:code-review-bot`.

| Failure label | Reason |
|---------------|--------|
| `status-17f:code-review-failed` | Generic error or unparseable verdict |
| `status-17f-ci:code-review-ci-fix-needed` | CI still red at the rounds cap |
| `status-17f-timeout:code-review-llm-timeout` | LLM API timeout |
| `status-17f-mcp:code-review-mcp-unavailable` | MCP server unavailable |
| `status-17f-tasks:code-review-open-tasks` | `## Tasks` in `TASK_TRACKER.md` still has unchecked items; run `/implementation_finalise` first |
| `status-17f-ci-unknown:code-review-ci-unknown` | The final gate could not prove CI green (pending, not configured, unknown or unavailable) |

### PR creation

Restart with `mcp-coder gh-tool set-status status-08:ready-pr`.

| Failure label | Reason |
|---------------|--------|
| `status-09f:pr-creating-failed` | Any other error or crash |
| `status-09f-timeout:pr-creating-llm-timeout` | LLM timeout during summary generation |
| `status-09f-mcp:pr-creating-mcp-unavailable` | MCP server(s) failed to connect |

### PR follow-up

Once the conflict or CI problem is fixed by hand, hand the PR back with `mcp-coder gh-tool set-status status-10:pr-created`.

| Failure label | Reason |
|---------------|--------|
| `status-73:merge-conflict-failed` | `fix-conflict` crashed, or the Jenkins job died |
| `status-74:pr-merge-conflict` | Still conflicting, no open PR found, or rebase failed (see the issue comment) |
| `status-83:ci-fix-failed` | `fix-ci` crashed, or the job died |
| `status-84:pr-ci-failed` | Fix attempts exhausted, LLM timeout, MCP unavailable, or formatter-config error (see the comment's Category line) |
