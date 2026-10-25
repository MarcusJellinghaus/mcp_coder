# Automated Review

Two optional headless workflows, `review-plan` and `review-implementation`, can review a plan or an implementation without a human. They pull a human in only when needed.

## Labels

| Label | Category |
|---|---|
| `status-14:plan-review-bot` | bot_pickup |
| `status-14i:plan-reviewing` | bot_busy |
| `status-17:code-review-bot` | bot_pickup |
| `status-17i:code-reviewing` | bot_busy |
| `status-14f:plan-review-failed` | human_action |
| `status-14f-timeout:plan-review-llm-timeout` | human_action |
| `status-14f-mcp:plan-review-mcp-unavailable` | human_action |
| `status-17f:code-review-failed` | human_action |
| `status-17f-ci:code-review-ci-fix-needed` | human_action |
| `status-17f-timeout:code-review-llm-timeout` | human_action |
| `status-17f-mcp:code-review-mcp-unavailable` | human_action |
| `status-17f-tasks:code-review-open-tasks` | human_action |
| `status-17f-ci-unknown:code-review-ci-unknown` | human_action |

```
create-plan ──▶ status-14 → status-14i (coordinator dispatches review-plan)
                    ├─ success  → status-05:plan-ready
                    ├─ escalate → status-04:plan-review  (interactive supervisor)
                    └─ error    → status-14f-*           (failure label)

implement ────▶ status-17 → status-17i (coordinator dispatches review-implementation)
                    ├─ success  → status-08:ready-pr
                    ├─ escalate → status-07:code-review  (interactive supervisor)
                    └─ error    → status-17f-*           (failure label)
```

## Actor

Fully automated, and it **can** run only when the per-repo flag is on: `auto_review_plan` for the plan lane, `auto_review_implementation` for the code lane. Both default to `false` (see [Configuration Guide](../../configuration/config.md)). With the flags off, `create-plan` transitions to `status-04:plan-review` and `implement` to `status-07:code-review` for the interactive supervisor. With a flag on, that success transition targets `status-14` / `status-17` instead.

**How a review runs.** Each workflow runs a multi-round loop (rounds cap: 5) pairing a **fresh reviewer session per round** with a **persistent supervisor session**:

1. The reviewer session (fresh each round) fetches the plan/diff, issue, and knowledge base via MCP tools and returns a structured findings report.
2. The supervisor session (persistent across rounds) triages the report into a machine-readable verdict: `dismiss` (converged → success), `tasks` (fixes for the reviewer to apply via MCP edit tools), or `escalate` (a design/scope question → needs-human).
3. On `tasks`, the reviewer applies the fixes; `review-implementation` then re-runs the shared rebase/CI steps. The loop repeats with a new reviewer session until convergence or the rounds cap.

Every round appends a detailed log to `pr_info/plan_review_log_{n}.md` / `pr_info/implementation_review_log_{n}.md` — the source of truth for an escalation handoff. Escalations, rebase hand-offs and the rounds cap post a structured `## ❌ <Lane> Handed Off` issue comment (category, reason, branch, base, files involved, next step) and apply the escalate label. Rebase-needed or still-red CI is a gate: it routes to needs-human or error, never success.

> **Quality gate before enabling.** Before setting `auto_review_*=true` on a repo, validate that the bot's review quality matches a trusted reference (the interactive supervisor or a human) on real branches. The deterministic behavior is unit-tested and the session interleave is integration-tested, but the model-judgment match is a manual pre-enable check, not something CI enforces.

## Slash commands

| Command | Purpose | Resulting label |
|---|---|---|
| [`/check_branch_status`](../../../.claude/skills/check_branch_status/SKILL.md) | Investigate a failure label: CI, rebase need, tasks, labels | — |
| [`/implementation_finalise`](../../../.claude/skills/implementation_finalise/SKILL.md) | Finish open tasks (recovery for `status-17f-tasks`) | — |

## Failure exits

Recovery re-queues the automated review with `mcp-coder gh-tool set-status status-14:plan-review-bot` (plan lane) or `mcp-coder gh-tool set-status status-17:code-review-bot` (code lane).

| Label | Cause | Recovery |
|---|---|---|
| `status-14f:plan-review-failed` | Automated plan review failed (generic error / unparseable verdict) | `mcp-coder gh-tool set-status status-14:plan-review-bot` |
| `status-14f-timeout:plan-review-llm-timeout` | LLM API timeout during automated plan review | `mcp-coder gh-tool set-status status-14:plan-review-bot` |
| `status-14f-mcp:plan-review-mcp-unavailable` | MCP server unavailable during automated plan review | `mcp-coder gh-tool set-status status-14:plan-review-bot` |
| `status-17f:code-review-failed` | Automated code review failed (generic error / unparseable verdict) | `mcp-coder gh-tool set-status status-17:code-review-bot` |
| `status-17f-ci:code-review-ci-fix-needed` | CI still red at the rounds cap | `mcp-coder gh-tool set-status status-17:code-review-bot` |
| `status-17f-timeout:code-review-llm-timeout` | LLM API timeout during automated code review | `mcp-coder gh-tool set-status status-17:code-review-bot` |
| `status-17f-mcp:code-review-mcp-unavailable` | MCP server unavailable during automated code review | `mcp-coder gh-tool set-status status-17:code-review-bot` |
| `status-17f-tasks:code-review-open-tasks` | `review-implementation` refused to start because `## Tasks` in `TASK_TRACKER.md` still has unchecked items | Run `/implementation_finalise`, then `mcp-coder gh-tool set-status status-17:code-review-bot` |
| `status-17f-ci-unknown:code-review-ci-unknown` | The final dismiss gate could not prove CI green (status pending / not configured / unknown / unavailable) | Run `/check_branch_status` (check the GitHub token / whether CI exists), then `mcp-coder gh-tool set-status status-17:code-review-bot` |

To hand off to the interactive supervisor instead of re-queuing, set `status-04:plan-review` or `status-07:code-review`. `status-04` carries `/plan_review_supervisor` and `status-07` carries `/implementation_review_supervisor`, so a human review session opens automatically.

Enabling `auto_review_implementation` presumes the repo has CI: the implementation lane leans on `check_and_fix_ci` for quality, and the final dismiss gate refuses the success label unless CI is *proven* green. A CI-less repo ends every review on `status-17f-ci-unknown`.
