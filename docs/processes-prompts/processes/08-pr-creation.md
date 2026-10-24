# PR Creation

The `create-pr` workflow generates a PR summary, cleans up `pr_info/`, pushes the branch and opens the pull request.

## Labels

| Label | Category |
|---|---|
| `status-08:ready-pr` | bot_pickup |
| `status-09:pr-creating` | bot_busy |
| `status-10:pr-created` | human_action |

`status-08:ready-pr` → `status-09:pr-creating` → `status-10:pr-created` (or `status-74` / `status-81`, see below)

## Actor

Tier: automated. The coordinator dispatches `create-pr` on Jenkins (`WORKFLOW_MAPPING`).

**Output:** Pull request on GitHub with a generated summary.

**Process:**

- Rebases onto the base branch if the branch is behind (a failed rebase is logged, not fatal)
- Generates PR summary from git diff using LLM (the diff excludes `pr_info/`)
- Cleans up pr_info folder (deletes steps/, clears TASK_TRACKER.md tasks)
- Commits cleanup changes
- Pushes branch to remote
- Creates pull request on GitHub with generated summary
- Post-creation checks: polls `mergeable_state`; on `dirty`, rebases and pushes once, then polls again
- Waits for the CI run of the pushed HEAD — no fixing
- Refreshes the PR title/body if the post-creation checks pushed new commits
- Sets the final label from the outcome (table below)
- Uses prompt 🔗 [PR Summary Generation](../../../src/mcp_coder/prompts/prompts.md#pr-summary-generation)

| Outcome | Final label |
|---|---|
| CI green, CI timeout, no CI, `unknown` mergeability, API error | `status-10:pr-created` |
| Still `dirty` after the rebase (CI wait skipped) | `status-74:pr-merge-conflict` |
| CI failed | `status-81:failing-ci` (Jenkins runs `fix-ci`) |
| Crash after the PR exists | `status-10:pr-created` (crash comment posted) |

**Resume.** If the branch already has an open PR, `create-pr` skips straight to the post-creation checks — after cleanup/commit/push if `pr_info/` is still on the branch. Recovering from `09f` with `set-status status-08:ready-pr` is therefore safe even when Jenkins killed the job after the PR was opened. `status-09:pr-creating` goes stale after 30 min, to cover the CI wait.

## Slash commands

None for the bot. The failure labels auto-launch [`/check_branch_status`](../../../.claude/skills/check_branch_status/SKILL.md).

## Failure exits

Recovery for all: fix the cause, then `mcp-coder gh-tool set-status status-08:ready-pr`.

| Label | Cause | Recovery |
|---|---|---|
| `status-09f:pr-creating-failed` | Any other error or crash | `mcp-coder gh-tool set-status status-08:ready-pr` |
| `status-09f-timeout:pr-creating-llm-timeout` | LLM timeout during summary generation | `mcp-coder gh-tool set-status status-08:ready-pr` |
| `status-09f-mcp:pr-creating-mcp-unavailable` | MCP server(s) failed to connect | `mcp-coder gh-tool set-status status-08:ready-pr` |
