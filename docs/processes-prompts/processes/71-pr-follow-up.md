# PR Follow-up

While a PR waits at `status-10:pr-created`, the vscodeclaude coordinator checks it for merge conflicts, failing CI and review feedback. Conflicts and CI are fixed mechanically on Jenkins. Review feedback always goes to a human.

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
  │                        ├─ fix exhausted / LLM timeout / MCP unavailable / formatter-config error → status-84  (human)
  │                        └─ job crashed      → status-83  (human)
  └─ review feedback  → status-91  (human, /pr_comment_triage) → status-10:pr-created
```

**Detection order at `status-10`:** conflict → CI → review comments. At most one acts per poll; the rest are re-checked next poll. Detection uses live GitHub data only (no local checkout) and is always active — there is no config flag.

**First check is done by create-pr.** `create-pr` already checks conflicts and waits for CI once, setting `74` or `81` directly (see [PR Creation](08-pr-creation.md)). PR follow-up takes over for whatever it left at `status-10`: `unknown` mergeability, CI timeout or no CI — and for everything that happens later.

**Order matters.** Conflicts come first because a branch that is behind its base can itself make CI fail; fixing the symptom first would waste CI-fix attempts. Review comments come last.

## Actor

| Labels | Actor |
|---|---|
| `status-71` / `status-81` | Automated. The coordinator dispatches Jenkins `fix-conflict` / `fix-ci`; the job sets the final label itself. Without Jenkins configured for a repo, the issue waits unprocessed. |
| `status-91`, `status-73` / `74` / `83` / `84` | Interactive LLM session (vscodeclaude). |

`fix-conflict` is a plain rebase with no LLM. `fix-ci` reuses the `implement` CI-fix loop. See [CLI Reference](../../cli-reference.md#fix-conflict).

## Slash commands

| Command | Purpose | Resulting label |
|---|---|---|
| [`/pr_comment_triage`](../../../.claude/skills/pr_comment_triage/SKILL.md) | Auto-launched at `status-91`. Triage each review item: fix, reply or decline | ends with `mcp-coder gh-tool set-status status-10:pr-created` |
| [`/check_branch_status`](../../../.claude/skills/check_branch_status/SKILL.md) | Auto-launched at `status-73` / `74` / `83` / `84`. Shows CI, rebase need, tasks and labels | — |
| [`/rebase`](../../../.claude/skills/rebase/SKILL.md) | Rebase onto the base branch by hand | — |

## Failure exits

| Label | Cause | Recovery |
|---|---|---|
| `status-73:merge-conflict-failed` | `fix-conflict` crashed (`run_guarded` net) or the Jenkins job died without transitioning (watchdog) | `/check_branch_status`, fix, `mcp-coder gh-tool set-status status-10:pr-created` |
| `status-74:pr-merge-conflict` | Still `dirty`, no open PR found, or `unknown` after a failed rebase. See the issue comment | Resolve manually (`/rebase` / `/check_branch_status`), then `mcp-coder gh-tool set-status status-10:pr-created` |
| `status-83:ci-fix-failed` | `fix-ci` crashed or the job died | `/check_branch_status`, fix, `mcp-coder gh-tool set-status status-10:pr-created` |
| `status-84:pr-ci-failed` | Fix attempts exhausted, LLM timeout, MCP unavailable, or formatter-config error (see the comment's Category line) | Fix CI manually, then `mcp-coder gh-tool set-status status-10:pr-created` |
| — (label stays `status-72` / `status-82`) | Current branch could not be determined → exit 1 | Check the Jenkins log; set `status-71:merge-conflict` / `status-81:failing-ci` to retry |

## Review feedback rules

**Review feedback is never auto-fixed.** Answering a human reviewer is a judgment call, and a wrong automated answer is public. `status-91` triggers on any unresolved review thread, or on a changes-requested review or top-level PR comment that has not been triaged yet. Code-scanning alerts are excluded. Unresolved threads use GitHub's own live state. Changes-requested reviews and conversation comments count only if newer than the last time the issue returned to `status-10` after a `status-91`, or always if it has never been through `status-91` (reviews by `submitted_at`, comments by `created_at`; derived from the issue's label history, nothing is stored locally), so a review already triaged does not re-trigger. Comments whose first line contains ❌ are skipped — that is mcp-coder's marker for its own notes, so a human comment starting that way is ignored too.

**Trusted authors only.** `status-91` fires only on items from trusted authors (`OWNER`, `MEMBER`, `COLLABORATOR`, or `[github] trusted_commenters` — see [Configuration](../../configuration/config.md)) on PRs whose author is trusted. Untrusted feedback never escalates: the coordinator prints one line per issue (`untrusted PR feedback from @a — review manually`) and writes nothing to GitHub.

**Triage session.** `/pr_comment_triage` starts with `/check_branch_status`, then for each item either fixes (quality checks, commit, push), replies or declines. Inline replies are used for review threads; a general PR comment for conversation comments and changes-requested reviews, which carry no thread id. Addressed threads are resolved so they do not re-trigger `status-91`. A changes-requested review that has been answered or fixed does not block `status-10`; it stays listed until the reviewer re-reviews. Items from untrusted authors are withheld from the session: never fixed, replied to or resolved, and they do not block `status-10`. When nothing is left, the session re-runs `/check_branch_status`, then sets `status-10:pr-created`.
