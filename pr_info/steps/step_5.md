# Step 5: Auto-merge and token docs

## LLM prompt

> Read `pr_info/steps/summary.md` and this file, and GitHub issue #1342 §5 and Decisions 9, 14,
> 17, 18. Edit docs only, so no new tests. Run `run_format_code` and pytest (`-n auto`, unit-test
> markers); all must pass. Produce exactly one commit. Do not edit `pr_info/TASK_TRACKER.md`.

## WHERE

Docs listed under HOW.

## WHAT

No code. The facts to document:

- An open alert blocks the merge: `pr_created` → `status-10`, then the coordinator escalates to
  `status-91`.
- A failed alert check blocks the merge: `merge_failed` → `status-99f`, with a comment, exit 1.
- Skipped (403/404) merges, with a warning in the Jenkins log.
- A PR blocked by alerts needs a manual merge after triage, unless a later fix-conflict or
  fix-ci run merges it.
- Auto-merge waits for the code-scanning run on `refs/pull/N/head`: up to about 5 minutes, about
  105 s if no run appears for the commit.

## HOW

| File | Edit |
|---|---|
| `docs/configuration/config.md` `#auto-merge` | Outcomes table rows: open alert → `status-10`, exit 0; failed alert check → `status-99f` + comment, exit 1. Caveats: the wait, skipped warns, manual merge after triage |
| `docs/cli-reference.md` (create-pr auto-merge paragraph, line 290) | Open alerts and failed alert check block; skipped warns |
| `docs/processes-prompts/processes/08-pr-creation.md` | Outcome rows: open alert → `status-10`; failed alert check in the `status-99f` row |
| `docs/processes-prompts/processes/10-pr-merge.md` | Actor paragraph: alerts block the merge; manual merge after triage |
| `docs/processes-prompts/processes/71-pr-follow-up.md` | "With `auto_merge`" paragraph; `status-99f` row of "Failure exits" |
| `docs/getting-started/label-setup.md` | `status-99f` row: add failed alert check |
| `docs/processes-prompts/claude_cheat_sheet.md` | `status-99f` row (line 162): add failed alert check |
| `docs/repository-setup/github.md` token section | Add `Code scanning alerts: Read` to the fine-grained list; remove "unconfirmed" and "kept out of the list above"; the heading is no longer scoped to `(check_branch_status)`: state it is needed by `check_branch_status`, the coordinator and auto-merge, and what happens without it (coordinator silently does nothing, auto-merge merges with a warning) |
| `docs/repository-setup/github.md` classic-PAT bullets | Replace the open questions with one instruction: add `security_events` alongside `repo`, and confirm with the Code scanning alerts row of `mcp-coder verify` |
| `docs/repository-setup/github.md` timeouts | Note the alert wait adds up to about 10 minutes across two merge attempts, so `09` can reach about 45 minutes and `72` can exceed its 30; the stale warning stays accepted. Values unchanged |
| `docs/repository-setup/quality-and-security-checks.md` | Correct "Branch rulesets (#1294) set the required status checks": `main` has no required checks and the `protect main` ruleset is disabled (checked 2026-11-04). Also adjust the table row "required checks are on" and the job-name rule so they do not imply otherwise |

## ALGORITHM

None.

## DATA

None.

## Tests

Not applicable: docs only.
