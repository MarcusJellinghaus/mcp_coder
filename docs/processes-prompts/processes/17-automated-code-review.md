# Automated Code Review

The optional headless `review-implementation` workflow reviews an implementation without a human. It pulls a human in only when needed. The plan counterpart is [Automated plan review](14-automated-plan-review.md).

## Labels

| Label | Category |
|---|---|
| `status-17:code-review-bot` | bot_pickup |
| `status-17i:code-reviewing` | bot_busy |
| `status-17f:code-review-failed` | human_action |
| `status-17f-ci:code-review-ci-fix-needed` | human_action |
| `status-17f-timeout:code-review-llm-timeout` | human_action |
| `status-17f-mcp:code-review-mcp-unavailable` | human_action |
| `status-17f-tasks:code-review-open-tasks` | human_action |
| `status-17f-ci-unknown:code-review-ci-unknown` | human_action |

```
implement ────▶ status-17 → status-17i (coordinator dispatches review-implementation)
                    ├─ success  → status-08:ready-pr
                    ├─ escalate → status-07:code-review  (interactive supervisor)
                    └─ error    → status-17f-*           (failure label)
```

## Actor

Fully automated, and it **can** run only when the per-repo flag `auto_review_implementation` is on. It defaults to `false` (see [Configuration Guide](../../configuration/config.md)). With the flag off, `implement` transitions to `status-07:code-review` for the interactive review ([Code review](07-code-review.md)). With the flag on, that success transition targets `status-17` instead.

### How a review runs

The loop is the one described in [Automated plan review](14-automated-plan-review.md#how-a-review-runs): a fresh reviewer session per round, a persistent supervisor session, rounds cap 5, verdicts `dismiss` / `tasks` / `escalate`. The code lane differs in these ways:

- The reviewer fetches the diff (not the plan).
- After fixes, `review-implementation` re-runs the shared rebase and CI steps before the next round.
- Rebase-needed or still-red CI is a gate: it routes to needs-human or error, never success.
- The log is `pr_info/implementation_review_log_{n}.md`.

> **Quality gate before enabling.** Before setting `auto_review_implementation=true` on a repo, validate that the bot's review quality matches a trusted reference (the interactive supervisor or a human) on real branches. The model-judgment match is a manual pre-enable check, not something CI enforces.

Enabling `auto_review_implementation` presumes the repo has CI: the lane leans on `check_and_fix_ci` for quality, and the final dismiss gate refuses the success label unless CI is *proven* green. A CI-less repo ends every review on `status-17f-ci-unknown`.

## Slash commands

| Command | Purpose | Resulting label |
|---|---|---|
| [`/check_branch_status`](../../../.claude/skills/check_branch_status/SKILL.md) | Investigate a failure label: CI, rebase need, tasks, labels | — |
| [`/implementation_finalise`](../../../.claude/skills/implementation_finalise/SKILL.md) | Finish open tasks (recovery for `status-17f-tasks`) | — |

## Failure exits

| Label | Cause | Recovery |
|---|---|---|
| `status-17f:code-review-failed` | Automated code review failed (generic error / unparseable verdict) | `mcp-coder gh-tool set-status status-17:code-review-bot` |
| `status-17f-ci:code-review-ci-fix-needed` | CI still red at the rounds cap | `mcp-coder gh-tool set-status status-17:code-review-bot` |
| `status-17f-timeout:code-review-llm-timeout` | LLM API timeout during automated code review | `mcp-coder gh-tool set-status status-17:code-review-bot` |
| `status-17f-mcp:code-review-mcp-unavailable` | MCP server unavailable during automated code review | `mcp-coder gh-tool set-status status-17:code-review-bot` |
| `status-17f-tasks:code-review-open-tasks` | `review-implementation` refused to start because `## Tasks` in `TASK_TRACKER.md` still has unchecked items | Run `/implementation_finalise`, then `mcp-coder gh-tool set-status status-17:code-review-bot` |
| `status-17f-ci-unknown:code-review-ci-unknown` | The final dismiss gate could not prove CI green (status pending / not configured / unknown / unavailable) | Run `/check_branch_status` (check the GitHub token / whether CI exists), then `mcp-coder gh-tool set-status status-17:code-review-bot` |

To hand off to the interactive supervisor instead of re-queuing, set `status-07:code-review`. It carries `/implementation_review_supervisor`, so a human review session opens automatically.
