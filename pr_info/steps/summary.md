# Summary: act on code-scanning alerts (#1342)

## Goal

A PR whose only problem is an open code-scanning alert currently stays at
`status-10:pr-created`, and auto-merge can merge it unseen. After this change:

- the coordinator moves such a PR to `status-91:pr-review-comments`;
- `/pr_comment_triage` handles alerts: fix a real issue, or explain a false positive
  and wait for the user to dismiss it in the GitHub UI;
- `run_auto_merge` refuses to merge a PR with an open alert.

The GitHub issue #1342 is the full specification, including its Constraints, Decisions
and Acceptance sections. If this plan and the issue disagree on required behaviour,
the issue wins.

## Architectural / design changes

### Coordinator: one new check in the existing chain

`check_pr_health` order becomes: merge conflict → failing CI → **alerts** → review
comments. First hit wins, one label change per poll.

- `_check_alerts` follows the shape of the other `_check_*` functions: returns `bool`,
  and never raises except `GitHubRateLimitError`.
- It reads `PullRequestCache.alerts()` from mcp-workspace (#374). No new cache and no
  new persistence in this repo.
- Alerts are live state, so there is no watermark.
- An untrusted PR author returns False silently. The existing review-comments line is
  reworded to cover alerts, so there is still one OUTPUT line per PR.

### Auto-merge: one gate before the merge call

`run_auto_merge` calls a new `_check_alert_gate` on every attempt, after the CI check
and head-SHA guard, immediately before merging. That covers the `verified_sha` path and
the rebase retry without extra code.

```
_check_alert_gate(project_dir, pr_number, sha) -> MergeOutcome | None   # None = merge
  ├─ _wait_for_code_scanning(project_dir, pr_number, sha) -> str | None # None = read alerts
  │    polls get_latest_ci_status("refs/pull/N/head")
  └─ PullRequestManager.get_pr_feedback(pr_number)                      # alerts keys only
```

| Gate result | Outcome | Label / exit |
|---|---|---|
| Open alert | `pr_created`, with OUTPUT line | `status-10`, exit 0; coordinator escalates to `status-91` |
| Alerts skipped (403/404) | `None`, with a warning | merges |
| No alerts | `None` | merges |
| Alert check failed | `merge_failed`, with comment fields | `status-99f`, exit 1 |
| Rate limit | `pr_created` via `log_rate_limit_stop` | `status-10`, exit 0 |

### Simplicity decisions

- **One polling loop.** A single loop bound of about 5 minutes covers the whole CodeQL
  wait, plus one counter for "no matching run" and one for consecutive lookup failures.
  A run first seen late therefore gets less than a full 5 minutes, which still meets
  "about 5 min". This is an assumption of the plan.
- **One `try` in the gate.** It wraps both the wait and the alerts fetch.
- **Plain return values.** `str | None` from the wait, `MergeOutcome | None` from the
  gate. No new enum or dataclass.
- **`_poll_for_ci_completion` is not reused.** It soft-passes on API errors and swallows
  rate limits, which the issue forbids here.
- **No second head-SHA check after the wait.** If the head moves during the wait, the
  `sha=` guard on the merge call refuses it (409 → `status-99f`), so a wrong commit can
  never be merged.
- **`_check_alerts` condition is `final and alerts`.** Skipped results always carry
  `alerts=[]` in `PullRequestCache._alerts`, so they need no separate branch.
- **No new mcp-workspace import at runtime.** `mcp_workspace_github.py` is unchanged and
  `AlertsResult` is read as a plain mapping, so an old env degrades rather than failing
  at startup.
- **Existing merge tests stay in place.** The `mocks` fixture patches `_check_alert_gate`
  to return `None`, and the gate is tested in a new file with its own small fixture.

### Skill and docs

- `pr_comment_triage` gains an Alert item type and a stricter "When done".
- The `status-91` label description is rewritten and every doc stating the check order or
  the triggers is updated.
- Docs beyond the issue's list, included as an assumption of the plan: the `status-99f`
  descriptions now mention a failed alert check, and the `github.md` stale-timeout note
  reflects the longer wait. Timeout values are not changed.

## Files

### Modified: source

| File | Change |
|---|---|
| `src/mcp_coder/workflows/vscodeclaude/checks.py` | `_check_alerts`, chain, docstrings, reworded line |
| `src/mcp_coder/workflow_steps/merge.py` | `_wait_for_code_scanning`, `_alert_check_failed`, `_check_alert_gate`, call site |
| `src/mcp_coder/workflow_steps/constants.py` | `CODE_SCANNING_MAX_POLL_ATTEMPTS` |
| `src/mcp_coder/config/labels.json` | `status-91` description |
| `.claude/skills/pr_comment_triage/SKILL.md` | alerts |

### Created: tests

| File | Covers |
|---|---|
| `tests/workflows/vscodeclaude/test_checks_alerts.py` | `_check_alerts` and its place in the chain |
| `tests/workflow_steps/test_merge_alerts.py` | wait, gate, and real-gate runs of `run_auto_merge` |

### Modified: tests

- `tests/workflows/vscodeclaude/test_checks.py`
- `tests/workflows/vscodeclaude/test_checks_pr_cache.py`
- `tests/workflows/vscodeclaude/test_checks_review_comments_trust.py`
- `tests/cli/commands/coordinator/test_vscodeclaude_pr_health.py`
- `tests/workflow_steps/test_merge.py`
- `tests/config/test_label_config.py`

### Modified: docs

- `docs/architecture/architecture.md`
- `docs/cli-reference.md`
- `docs/configuration/config.md`
- `docs/coordinator-vscodeclaude.md`
- `docs/getting-started/label-setup.md`
- `docs/processes-prompts/claude_cheat_sheet.md`
- `docs/processes-prompts/github_Issue_Workflow_Matrix.html`
- `docs/processes-prompts/processes/08-pr-creation.md`
- `docs/processes-prompts/processes/10-pr-merge.md`
- `docs/processes-prompts/processes/71-pr-follow-up.md`
- `docs/repository-setup/claude-code.md`
- `docs/repository-setup/github.md`
- `docs/repository-setup/quality-and-security-checks.md`

### Not modified

`src/mcp_coder/mcp_workspace_github.py` (issue §2).

## Steps

| Step | Commit |
|---|---|
| [1](step_1.md) | Coordinator: `_check_alerts` |
| [2](step_2.md) | Auto-merge: CodeQL wait and alert gate |
| [3](step_3.md) | `pr_comment_triage` skill: alerts |
| [4](step_4.md) | `status-91` label and PR-health docs |
| [5](step_5.md) | Auto-merge and token docs |

## After merge (manual rollout)

These are not implementation steps:

- Reinstall the coordinator and Jenkins tool envs, upgrading mcp-workspace.
- Grant `Code scanning alerts: Read` to the coordinator and Jenkins tokens.
- Re-run `define-labels` so the `status-91` description reaches GitHub.
- The `.claude/` changes need maintainer review before merge.
