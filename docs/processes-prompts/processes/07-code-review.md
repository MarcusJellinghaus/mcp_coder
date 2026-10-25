# Code Review

The implementation is reviewed and a decision is made: approve, rework, or redesign. The review is an interactive LLM session by default and can optionally run automated.

## Labels

How `implement` ends decides which review runs: `status-07` by default, `status-17` with `auto_review_implementation` on.

| Label | Category | Review |
|---|---|---|
| `status-07:code-review` | human_action | Interactive |
| `status-17:code-review-bot` | bot_pickup | Automated |
| `status-17i:code-reviewing` | bot_busy | Automated |
| `status-08:ready-pr` | bot_pickup | — |

- Interactive: `status-07:code-review` → `status-08:ready-pr` (approve)
- Automated: `status-17:code-review-bot` → `status-17i:code-reviewing` → `status-08:ready-pr` (success), `status-07:code-review` (needs a human) or `status-17f-*` (failure)

Other exits from the interactive review:

- → `status-05:plan-ready`: rework (new tasks, then re-implement)
- minor fixes: stay on `status-07:code-review`
- fundamental problems: → `status-04:plan-review` or `status-01:created` via `mcp-coder gh-tool set-status`

## Actor

**Interactive (`status-07`):** tier: interactive LLM session — you, or a supervisor skill. vscodeclaude auto-launches `/implementation_review_supervisor` for this label. The supervisor ends at "ready for approval". The label change is a separate command. Escalations from the automated review arrive here.

**Tools:** MCP code quality checks

**Automated (`status-17`):** tier: automated. The coordinator dispatches `review-implementation` on Jenkins, only with `auto_review_implementation` on (default off, see [configuration](../../configuration/config.md)). It reviews, fixes and re-runs rebase and CI in rounds, and moves the issue to `status-08` once converged and CI is proven green. When it needs a human, it hands over to `status-07`. How it runs: [Automated code review](17-automated-code-review.md).

## Slash commands

These apply to the interactive review (`status-07`). The automated review needs none, apart from `/check_branch_status` after a failure label and `/implementation_finalise` for `status-17f-tasks`.

| Command | Purpose | Resulting label |
|---|---|---|
| [`/implementation_review_supervisor`](../../../.claude/skills/implementation_review_supervisor/SKILL.md) | Autonomous review: runs `/implementation_review`, triages findings against `.claude/knowledge_base/`, has subagents fix accepted findings, repeats in rounds, writes `pr_info/implementation_review_log_*.md`. Escalates only when unsure or a major refactoring is needed. Use for the vscodeclaude flow or when the knowledge base can triage most findings | — |
| [`/implementation_review`](../../../.claude/skills/implementation_review/SKILL.md) | Human-supervised review: Claude presents findings, you decide what to act on. Use for full control over every finding | — |
| [`/discuss`](../../../.claude/skills/discuss/SKILL.md) | Go through open findings step by step | — |
| [`/implementation_finalise`](../../../.claude/skills/implementation_finalise/SKILL.md) | Finish open tasks | — |
| [`/implementation_new_tasks`](../../../.claude/skills/implementation_new_tasks/SKILL.md) | Draft additional implementation steps and update the task tracker | — |
| [`/commit_push`](../../../.claude/skills/commit_push/SKILL.md) | Commit and push the updated plan or fixes | — |
| [`/implementation_approve`](../../../.claude/skills/implementation_approve/SKILL.md) | Approve; only when `/check_branch_status` reports `Ready to merge` | `status-08:ready-pr` |
| [`/implementation_needs_rework`](../../../.claude/skills/implementation_needs_rework/SKILL.md) | Send back for rework; next step is implementation, not plan review | `status-05:plan-ready` |

Rework chain: `/implementation_new_tasks` → `/commit_push` → `/implementation_needs_rework`, then `mcp-coder implement` processes the new steps.

## Failure exits

**Interactive (`status-07`):** none — human stage.

**Automated (`status-17`):** the six `status-17f-*` labels (`17f`, `17f-ci`, `17f-timeout`, `17f-mcp`, `17f-tasks`, `17f-ci-unknown`). Recovery: `mcp-coder gh-tool set-status status-17:code-review-bot`. Causes: [Automated code review](17-automated-code-review.md#failure-exits).
