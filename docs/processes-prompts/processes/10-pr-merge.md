# PR Merge

A human reviews the pull request, checks CI and merges it.

## Labels

| Label | Category |
|---|---|
| `status-10:pr-created` | human_action |

`status-10:pr-created` → merged and closed. GitHub closes the linked issue automatically.

## Actor

Tier: GitHub UI — the only strictly human step, unless [`auto_merge`](../../configuration/config.md#auto-merge) is on. Then `create-pr`, `fix-ci` and `fix-conflict` squash-merge after a real green and set `status-99:merged` (or `status-99f:merge-failed`). `status-99` matters for PRs into a non-default base, where GitHub does not close the issue. `status-10:pr-created` has no auto-launched command.

While the PR waits, see [PR follow-up](71-pr-follow-up.md).

**Tools:** GitHub UI (the PR page)

**Key steps:**

- Final review of changes
- CI green
- Merge

Major rework: add tasks and set `status-05:plan-ready`.

## Slash commands

| Command | Purpose | Resulting label |
|---|---|---|
| [`/check_branch_status`](../../../.claude/skills/check_branch_status/SKILL.md) | Optional pre-merge check of CI, rebase need, tasks and labels | — |

## Failure exits

None — human stage. Conflicts, CI failures, code-scanning alerts and review comments while waiting are handled by PR follow-up.
