# Failure Handling

Index of every failure label. Recovery steps live in the owner doc, not here.

## Labels

| Label | Stage | Recovery in |
|---|---|---|
| `status-73:merge-conflict-failed` | PR follow-up (merge conflict, crash) | [71-pr-follow-up.md](71-pr-follow-up.md#failure-exits) |
| `status-74:pr-merge-conflict` | PR follow-up (merge conflict) | [71-pr-follow-up.md](71-pr-follow-up.md#failure-exits) |
| `status-83:ci-fix-failed` | PR follow-up (CI fix, crash) | [71-pr-follow-up.md](71-pr-follow-up.md#failure-exits) |
| `status-84:pr-ci-failed` | PR follow-up (CI fix) | [71-pr-follow-up.md](71-pr-follow-up.md#failure-exits) |
| `status-03f-timeout:planning-llm-timeout` | Plan creation | [02-plan-creation.md](02-plan-creation.md#failure-exits) |
| `status-03f-mcp:planning-mcp-unavailable` | Plan creation | [02-plan-creation.md](02-plan-creation.md#failure-exits) |
| `status-03f-prereq:planning-prereq-failed` | Plan creation | [02-plan-creation.md](02-plan-creation.md#failure-exits) |
| `status-03f:planning-failed` | Plan creation | [02-plan-creation.md](02-plan-creation.md#failure-exits) |
| `status-06f:implementing-failed` | Implementation | [05-implementation.md](05-implementation.md#failure-exits) |
| `status-06f-prep:task-tracker-prep-failed` | Implementation | [05-implementation.md](05-implementation.md#failure-exits) |
| `status-06f-ci:ci-fix-needed` | Implementation | [05-implementation.md](05-implementation.md#failure-exits) |
| `status-06f-timeout:llm-timeout` | Implementation | [05-implementation.md](05-implementation.md#failure-exits) |
| `status-06f-mcp:mcp-unavailable` | Implementation | [05-implementation.md](05-implementation.md#failure-exits) |
| `status-06f-nochange:no-changes-after-retries` | Implementation | [05-implementation.md](05-implementation.md#failure-exits) |
| `status-06f-blocked:implementation-blocked` | Implementation | [05-implementation.md](05-implementation.md#failure-exits) |
| `status-09f-timeout:pr-creating-llm-timeout` | PR creation | [08-pr-creation.md](08-pr-creation.md#failure-exits) |
| `status-09f-mcp:pr-creating-mcp-unavailable` | PR creation | [08-pr-creation.md](08-pr-creation.md#failure-exits) |
| `status-09f:pr-creating-failed` | PR creation | [08-pr-creation.md](08-pr-creation.md#failure-exits) |
| `status-14f:plan-review-failed` | Automated plan review | [14-automated-plan-review.md](14-automated-plan-review.md#failure-exits) |
| `status-14f-timeout:plan-review-llm-timeout` | Automated plan review | [14-automated-plan-review.md](14-automated-plan-review.md#failure-exits) |
| `status-14f-mcp:plan-review-mcp-unavailable` | Automated plan review | [14-automated-plan-review.md](14-automated-plan-review.md#failure-exits) |
| `status-17f:code-review-failed` | Automated code review | [17-automated-code-review.md](17-automated-code-review.md#failure-exits) |
| `status-17f-ci:code-review-ci-fix-needed` | Automated code review | [17-automated-code-review.md](17-automated-code-review.md#failure-exits) |
| `status-17f-timeout:code-review-llm-timeout` | Automated code review | [17-automated-code-review.md](17-automated-code-review.md#failure-exits) |
| `status-17f-mcp:code-review-mcp-unavailable` | Automated code review | [17-automated-code-review.md](17-automated-code-review.md#failure-exits) |
| `status-17f-tasks:code-review-open-tasks` | Automated code review | [17-automated-code-review.md](17-automated-code-review.md#failure-exits) |
| `status-17f-ci-unknown:code-review-ci-unknown` | Automated code review | [17-automated-code-review.md](17-automated-code-review.md#failure-exits) |

`status-73` and `status-83` are crash labels (unhandled crash or Jenkins job died), not ordinary failures.

## Actor

Human. vscodeclaude opens a session on every failure label.

## Slash commands

`/check_branch_status` is the entry command for every failure label. Exception: `status-17f-tasks` auto-launches `/implementation_finalise`.

## Failure exits

General recovery, for every label above:

1. Read the failure comment on the issue (Category / Stage / Error).
2. Fix the cause.
3. `mcp-coder gh-tool set-status <retry label>` (the retry label is listed in the owner doc).
4. The bot picks the issue up again.
