# Automated Plan Review

The optional headless `review-plan` workflow reviews an implementation plan without a human. It pulls a human in only when needed. The code counterpart is [Automated code review](17-automated-code-review.md).

## Labels

| Label | Category |
|---|---|
| `status-14:plan-review-bot` | bot_pickup |
| `status-14i:plan-reviewing` | bot_busy |
| `status-14f:plan-review-failed` | human_action |
| `status-14f-timeout:plan-review-llm-timeout` | human_action |
| `status-14f-mcp:plan-review-mcp-unavailable` | human_action |

```
create-plan ──▶ status-14 → status-14i (coordinator dispatches review-plan)
                    ├─ success  → status-05:plan-ready
                    ├─ escalate → status-04:plan-review  (interactive supervisor)
                    └─ error    → status-14f-*           (failure label)
```

## Actor

Tier: automated. It **can** run only when the per-repo flag `auto_review_plan` is on. It defaults to `false` (see [Configuration Guide](../../configuration/config.md)). With the flag off, `create-plan` transitions to `status-04:plan-review` for the interactive review ([Plan review](04-plan-review.md)). With the flag on, that success transition targets `status-14` instead.

### How a review runs

The workflow runs a multi-round loop (rounds cap: 5) pairing a **fresh reviewer session per round** with a **persistent supervisor session**:

1. The reviewer session (fresh each round) fetches the plan, issue, and knowledge base via MCP tools and returns a structured findings report.
2. The supervisor session (persistent across rounds) triages the report into a machine-readable verdict: `dismiss` (converged → success), `tasks` (fixes for the reviewer to apply via MCP edit tools), or `escalate` (a design/scope question → needs-human).
3. On `tasks`, the reviewer applies the fixes. The loop repeats with a new reviewer session until convergence or the rounds cap.

Every round appends a detailed log to `pr_info/plan_review_log_{n}.md` — the source of truth for an escalation handoff. Escalations and the rounds cap post a structured `## ❌ <Lane> Handed Off` issue comment (category, reason, branch, base, files involved, next step) and apply the escalate label.

> **Quality gate before enabling.** Before setting `auto_review_plan=true` on a repo, validate that the bot's review quality matches a trusted reference (the interactive supervisor or a human) on real branches. The deterministic behavior is unit-tested and the session interleave is integration-tested, but the model-judgment match is a manual pre-enable check, not something CI enforces.

## Slash commands

| Command | Purpose | Resulting label |
|---|---|---|
| [`/check_branch_status`](../../../.claude/skills/check_branch_status/SKILL.md) | Investigate a failure label: CI, rebase need, tasks, labels | — |

## Failure exits

| Label | Cause | Recovery |
|---|---|---|
| `status-14f:plan-review-failed` | Automated plan review failed (generic error / unparseable verdict) | `mcp-coder gh-tool set-status status-14:plan-review-bot` |
| `status-14f-timeout:plan-review-llm-timeout` | LLM API timeout during automated plan review | `mcp-coder gh-tool set-status status-14:plan-review-bot` |
| `status-14f-mcp:plan-review-mcp-unavailable` | MCP server unavailable during automated plan review | `mcp-coder gh-tool set-status status-14:plan-review-bot` |

To hand off to the interactive supervisor instead of re-queuing, set `status-04:plan-review`. It carries `/plan_review_supervisor`, so a human review session opens automatically.
