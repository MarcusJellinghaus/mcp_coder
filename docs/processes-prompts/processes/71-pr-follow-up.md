# PR Follow-up

While a PR waits at `status-10:pr-created`, the vscodeclaude coordinator checks it for merge conflicts, failing CI, code-scanning alerts and review feedback. Conflicts and CI are fixed automatically on Jenkins. Alerts and review feedback always go to a human.

## Labels

| Label | Category |
|---|---|
| `status-10:pr-created` | human_action (start and end state) |
| `status-71:merge-conflict` | bot_pickup |
| `status-72:fixing-merge-conflict` | bot_busy |
| `status-73:merge-conflict-failed` | human_action |
| `status-74:pr-merge-conflict` | human_action |
| `status-81:failing-ci` | bot_pickup |
| `status-82:fixing-ci` | bot_busy |
| `status-83:ci-fix-failed` | human_action |
| `status-84:pr-ci-failed` | human_action |
| `status-91:pr-review-comments` | human_action |

```
status-10:pr-created
  ├─ merge conflict   → status-71 ─▶ (Jenkins: fix-conflict) ─▶ status-72
  │                        ├─ settled, not dirty            → status-10:pr-created
  │                        ├─ unknown, rebase ok            → status-10:pr-created
  │                        ├─ still conflicting (dirty)     → status-74  (human)
  │                        ├─ no open PR / unknown + rebase failed → status-74  (human)
  │                        └─ job crashed                   → status-73  (human)
  ├─ failing CI       → status-81 ─▶ (Jenkins: fix-ci) ─▶ status-82
  │                        ├─ CI green         → status-10:pr-created
  │                        ├─ fix exhausted / LLM timeout / MCP unavailable / formatter-config error / branch moved → status-84  (human)
  │                        └─ job crashed      → status-83  (human)
  ├─ open alerts      → status-91  (human, /pr_comment_triage) → status-10:pr-created
  └─ review feedback  → status-91  (human, /pr_comment_triage) → status-10:pr-created
```

**With [`auto_merge`](../../configuration/config.md#auto-merge)**, the green ends of `fix-conflict` and `fix-ci` squash-merge the PR instead of returning to `status-10`: merged → `status-99:merged`; refused or errored → `status-99f:merge-failed` (human, `/check_branch_status`). A merge-time rebase conflict → `status-74`; CI red on HEAD → `status-81`; a failed alert check → `status-99f`. An open code-scanning alert → `status-10`, which the coordinator escalates to `status-91`; after triage the PR needs a manual merge, unless a later `fix-conflict` or `fix-ci` run merges it.

**Detection order at `status-10`:** conflict → CI → alerts → review comments. At most one acts per poll; the rest are re-checked next poll. Detection uses live GitHub data only (no local checkout) and is always active — there is no config flag.

**First check is done by create-pr.** `create-pr` already checks conflicts and waits for CI once, setting `71` or `81` directly (see [PR Creation](08-pr-creation.md)). PR follow-up takes over for whatever it left at `status-10`: `unknown` mergeability, CI timeout or no CI — and for everything that happens later.

**Order matters.** Conflicts come first because a branch that is behind its base can itself make CI fail; fixing the symptom first would waste CI-fix attempts. Alerts follow CI because they are read only once every CI run on the head has completed; until then GitHub still reports the previous commit's alerts. Review comments come last.

## Actor

| Labels | Actor |
|---|---|
| `status-71` / `status-81` | Automated. The coordinator dispatches Jenkins `fix-conflict` / `fix-ci`; the job sets the final label itself. Without Jenkins configured for a repo, the issue waits unprocessed. |
| `status-91`, `status-73` / `74` / `83` / `84` | Interactive LLM session (vscodeclaude). |

`fix-conflict` runs a git-only rebase, then the LLM rebase on a conflict or failed rebase. When it hands off at `status-74`, the comment includes the LLM rebase's reason. `fix-ci` reuses the `implement` CI-fix loop. See [CLI Reference](../../cli-reference.md#fix-conflict).

## Slash commands

| Command | Purpose | Resulting label |
|---|---|---|
| [`/pr_comment_triage`](../../../.claude/skills/pr_comment_triage/SKILL.md) | Auto-launched at `status-91`. Triage each review item: fix, reply or decline. Each code-scanning alert: fix, or explain a false positive and wait for the user to dismiss it | ends with `mcp-coder gh-tool set-status status-10:pr-created`, only once no alert is open |
| [`/check_branch_status`](../../../.claude/skills/check_branch_status/SKILL.md) | Auto-launched at `status-73` / `74` / `83` / `84` (at `74` after `/rebase`). Shows CI, rebase need, tasks and labels | — |
| [`/rebase`](../../../.claude/skills/rebase/SKILL.md) | Auto-launched first at `status-74`. Rebase onto the base branch | — |

## Failure exits

| Label | Cause | Recovery |
|---|---|---|
| `status-73:merge-conflict-failed` | `fix-conflict` crashed (`run_guarded` net) or the Jenkins job died without transitioning (watchdog) | `/check_branch_status`, fix, `mcp-coder gh-tool set-status status-10:pr-created` |
| `status-74:pr-merge-conflict` | Still `dirty`, no open PR found, or `unknown` after a failed rebase (git-only and LLM). See the issue comment | Resolve manually (`/rebase` / `/check_branch_status`), then `mcp-coder gh-tool set-status status-10:pr-created` |
| `status-83:ci-fix-failed` | `fix-ci` crashed or the job died | `/check_branch_status`, fix, `mcp-coder gh-tool set-status status-10:pr-created` |
| `status-84:pr-ci-failed` | Fix attempts exhausted, LLM timeout, MCP unavailable, formatter-config error, or branch moved during the CI fix (see the comment's Category line) | Fix CI manually, then `mcp-coder gh-tool set-status status-10:pr-created`. Branch moved: check the new commit on the branch, then set the same status |
| `status-99f:merge-failed` | `auto_merge` was refused (409, `blocked`, required approvals, squash disabled), errored, its rebase failed, or its alert check failed. See the issue comment | `/check_branch_status`, fix the cause or merge by hand; or `mcp-coder gh-tool set-status status-10:pr-created` |
| — (label stays `status-72` / `status-82`) | Current branch could not be determined → exit 1 | Check the Jenkins log; set `status-71:merge-conflict` / `status-81:failing-ci` to retry |

## Review feedback rules

**Review feedback is never auto-fixed.** Answering a human reviewer is a judgment call, and a wrong automated answer is public. Alerts are not auto-fixed either: `fix-ci` works from failed-run logs, an alert has none, and real versus false positive needs a human. `status-91` triggers on any unresolved review thread, any open code-scanning alert, or on a changes-requested review or top-level PR comment that has not been triaged yet. Unresolved threads and alerts use GitHub's own live state, so a fixed or dismissed alert simply drops out. Alerts count only once every CI run on the head has completed; a skipped alert query (403/404, e.g. no code scanning on the repo) does not escalate. Changes-requested reviews and conversation comments count only if newer than the last time the issue returned to `status-10` after a `status-91`, or always if it has never been through `status-91` (reviews by `submitted_at`, comments by `created_at`; derived from the issue's label history, nothing is stored locally), so a review already triaged does not re-trigger. Comments whose first line contains ❌ are skipped — that is mcp-coder's marker for its own notes, so a human comment starting that way is ignored too.

**Trusted authors only.** `status-91` fires only on items from trusted authors (`OWNER`, `MEMBER`, `COLLABORATOR`, or `[github] trusted_commenters` — see [Configuration](../../configuration/config.md)) on PRs whose author is trusted. Alerts have no author, so only the PR-author check applies to them. Untrusted feedback never escalates: the coordinator prints one line per issue (`untrusted PR feedback from @a — review manually`) and writes nothing to GitHub.

**Triage session.** `/pr_comment_triage` starts with `/check_branch_status`, then for each item either fixes (quality checks, commit, push), replies or declines. Inline replies are used for review threads; a general PR comment for conversation comments and changes-requested reviews, which carry no thread id. Addressed threads are resolved so they do not re-trigger `status-91`. A changes-requested review that has been answered or fixed does not block `status-10`; it stays listed until the reviewer re-reviews. A real alert is fixed and pushed. For a false positive the session explains why in a PR comment, asks the user to dismiss the alert in the GitHub UI and waits; it never dismisses an alert itself. Items from untrusted authors are withheld from the session: never fixed, replied to or resolved, and they do not block `status-10`. When nothing is left, the session re-runs `/check_branch_status`, then sets `status-10:pr-created`. It never does so while an alert is open, because the coordinator would re-escalate on the next poll; if the user leaves, the issue stays at `status-91`.
