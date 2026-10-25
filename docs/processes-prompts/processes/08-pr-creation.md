# PR Creation

The `create-pr` workflow generates a PR summary, cleans up `pr_info/`, pushes the branch and opens the pull request.

## Labels

| Label | Category |
|---|---|
| `status-08:ready-pr` | bot_pickup |
| `status-09:pr-creating` | bot_busy |
| `status-10:pr-created` | human_action |

`status-08:ready-pr` → `status-09:pr-creating` → `status-10:pr-created`

## Actor

Tier: automated. The coordinator dispatches `create-pr` on Jenkins (`WORKFLOW_MAPPING`).

**Output:** Pull request on GitHub with a generated summary.

**Process:**

- Generates PR summary from git diff using LLM
- Cleans up pr_info folder (deletes steps/, clears TASK_TRACKER.md tasks)
- Commits cleanup changes
- Pushes branch to remote
- Creates pull request on GitHub with generated summary
- Uses prompt 🔗 [PR Summary Generation](../../../src/mcp_coder/prompts/prompts.md#pr-summary-generation)

## Slash commands

None for the bot. The failure labels auto-launch [`/check_branch_status`](../../../.claude/skills/check_branch_status/SKILL.md).

## Failure exits

Recovery for all: fix the cause, then `mcp-coder gh-tool set-status status-08:ready-pr`.

| Label | Cause | Recovery |
|---|---|---|
| `status-09f:pr-creating-failed` | Any other error or crash | `mcp-coder gh-tool set-status status-08:ready-pr` |
| `status-09f-timeout:pr-creating-llm-timeout` | LLM timeout during summary generation | `mcp-coder gh-tool set-status status-08:ready-pr` |
| `status-09f-mcp:pr-creating-mcp-unavailable` | MCP server(s) failed to connect | `mcp-coder gh-tool set-status status-08:ready-pr` |
