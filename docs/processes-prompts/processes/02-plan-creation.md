# Plan Creation

The `create-plan` workflow turns an approved issue into an implementation plan in `pr_info/`.

## Labels

| Label | Category |
|---|---|
| `status-02:awaiting-planning` | bot_pickup |
| `status-03:planning` | bot_busy |
| `status-04:plan-review` | human_action |
| `status-14:plan-review-bot` | bot_pickup |

`status-02:awaiting-planning` → `status-03:planning` → `status-04:plan-review`

With `auto_review_plan` on (default off, see [configuration](../../configuration/config.md)), success goes to `status-14:plan-review-bot` instead. See [Plan review](04-plan-review.md).

## Actor

Fully automated. The coordinator dispatches `create-plan` on Jenkins (`WORKFLOW_MAPPING`).

Output: plan files with a summary and steps (`summary.md`, `step_*.md`).

## Slash commands

None for the bot. The failure labels auto-launch `/check_branch_status`.

The workflow generates the plan with three prompts ([prompts.md](../../../src/mcp_coder/prompts/prompts.md#plan-generation-workflow)):

- [Initial Analysis](../../../src/mcp_coder/prompts/prompts.md#initial-analysis)
- [Simplification Review](../../../src/mcp_coder/prompts/prompts.md#simplification-review)
- [Implementation Plan Creation](../../../src/mcp_coder/prompts/prompts.md#implementation-plan-creation)

## Failure exits

| Label | Cause | Recovery |
|---|---|---|
| `status-03f:planning-failed` | Any other error or crash | Fix the cause, then `mcp-coder gh-tool set-status status-02:awaiting-planning` |
| `status-03f-timeout:planning-llm-timeout` | LLM timeout | Same |
| `status-03f-mcp:planning-mcp-unavailable` | MCP server(s) failed to connect | Same |
| `status-03f-prereq:planning-prereq-failed` | Dirty working dir, issue not found, base branch missing, branch creation failed, `pr_info/` already exists, or `pr_info/` creation failed | Same |
