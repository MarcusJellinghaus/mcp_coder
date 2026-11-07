# Jenkins status check

Goal: for a time window, say which Executor builds succeeded and which failed, which issues need action, and which problems need recording. To catalogue failure types instead, use [`jenkins_issue_analysis.md`](jenkins_issue_analysis.md).

**Scope:** the repos the coordinator serves (the JENKINS JOBS section of `mcp-coder verify`). Leave AutoRunner out: its automated runs don't work reliably yet.

## Rules

- **Approval before any GitHub write:** status labels, adding or removing `blocked` / `wait`, new issues, comments. Show the proposal or draft first, then wait.
- **Check every blocker against the current state** before calling it gone or still there (step 5). Say which checks ran; mark anything only read from code *not run*.
- Work from build status and labels. Open logs only for issues whose last build didn't finish cleanly.

## Background

The workflow, labels and steps are in [`development-process.md`](../docs/processes-prompts/development-process.md); each step's doc under [`processes/`](../docs/processes-prompts/processes/) lists its failure exits.

- One Jenkins job, `Windows-Agents/Executor`, runs every step for every repo. Display name: `<repo> - #<issue> - <step> - #<build>`.
- Each step sets the issue's `status-*` label; the coordinator dispatches the next step from it.
- The coordinator skips issues with an `ignore_labels` label (`blocked`, `wait`, `Overview`; `src/mcp_coder/config/labels.json`).

| Build status | Meaning |
|---|---|
| `success` | Step finished, no warnings |
| `unstable` | Step finished, but a ` - WARNING - ` line was logged. Judge by the label |
| `failure` | Step or pipeline failed |
| `aborted` | Stopped by hand or by timeout |

## Steps

If a Jenkins call fails, run `mcp-coder verify` (JENKINS sections) first.

1. **List builds:** `tools/jenkins_builds.sh --limit N`, with `N ≈ 30 × days`. Count them per status and group them by issue in time order.
2. **Classify each issue** by its last build and current label (`github_issue_view`; `reference_name` for other repos). See [Outcomes](#outcomes).
3. **Cross-check open issues** for the ones nothing has run for. Search each repo with one OR query, e.g. `github_search('is:open label:"status-02:awaiting-planning","status-05:plan-ready",...', reference_name=...)`. Label categories are in `labels.json`:
   - `bot_busy` (`03`, `06`, `09`, `14i`, `17i`, `72`, `82`) → a build must be running, otherwise the label is stuck
   - `bot_pickup` (`02`, `05`, `08`, `14`, `17`) → a build starts on the next poll, unless `blocked` / `wait` is set; then check the blocker
   - `status-01`, Overview and human-action labels → not expected to run. `71` / `81` come from the coordinator's PR checks, not from a build
4. **Find the cause** for every issue that needs action. Read the failure comment on the issue first (Category / Stage / Error). If that doesn't settle it, download the logs: `tools/jenkins_download_logs.sh --limit N --name-pattern ' - #\d+$' --outdir .scratch/jenkins_logs`, then `tools/jenkins_classify_logs.sh --logdir .scratch/jenkins_logs`. Deciding lines:
   - `Blocked marker found:` — implement refused; the reason follows
   - `REVIEW HANDED OFF` and its `Reason:` line
   - `Successfully updated issue #N label:` — the label the step set
   - `Skipped set-status`, `Workflow failed`
5. **Check blockers:** blocking issue open or closed? Blocking PR merged, and its fix on the base branch (`git fetch`, then `git log` / `git show origin/main:<file>` with `reference_name`)? Does the failing check's code still look the same? Comments such as "Blocked by #N" get the same check.
6. **Propose** in one batch: label changes (issue, current → new, evidence) and drafts for comments or issues (see [Recording problems](#recording-problems)). Wait for approval.
7. **Act** on what was approved:
   - `blocked` / `wait`: `github_issue_edit(remove_labels=[...])`
   - status: `mcp-coder gh-tool set-status <label> --issue N --from-status <current> --project-dir <checkout>`. Retry labels are in [`failure-handling.md`](../docs/processes-prompts/processes/failure-handling.md); a stuck in-progress label goes back one (`03` → `02`, `06` → `05`, `09` → `08`). For other repos, `git rev_parse --show-toplevel` with `reference_name` gives the checkout path.
   - Then confirm that each re-run started and got past provisioning. If it's stuck again, propose again.
8. **Report:** counts per status; done issues, one line per repo; a table for the rest (issue, last build, label now, action, why); the known problems seen, with build numbers. Delete `.scratch/`.

## Outcomes

| Outcome | Action |
|---|---|
| Done (`create-pr` succeeded), recovered by a retry, or issue closed | None. Leftover labels on closed issues don't matter |
| Build running, matching its label | None |
| Handed off (`04:plan-review`, `07:code-review`) | Human decision |
| Blocked, blocker still there | Wait; name the blocker |
| Blocked, blocker gone | Propose removing `blocked` / `wait` |
| Failure label, cause gone or transient | Propose the retry label |
| Stuck in progress (failed before the workflow ran, `PIPE-NO-STATUS-ON-PRE-WORKFLOW-FAILURE`) | Propose the reset label |
| Problem seen in the logs | See [Recording problems](#recording-problems) |

## Recording problems

Search before proposing anything: the [known problems](#known-problems) below, the repo's chore issue, the analysis issue mcp_coder #1363, and open issues (`github_search`). Then propose one of:

- **Already tracked** → only report it, with build numbers
- **Small config or cleanup** → a section in the repo's chore issue
- **One-off, or adds evidence to a known type** → a comment on the tracking issue, or on #1363
- **New, recurring problem** → a new issue in the repo that owns the code

## Known problems

Remove a row once its tracking issue is closed.

| Problem | Signature | Tracked in |
|---|---|---|
| Duplicate builds for one issue | Two builds of the same step for the same issue, minutes apart (`PIPE-CONCURRENT-BUILDS-SAME-ISSUE`). Find out who started the second | mcp_coder #1363, fix group 8 |
| Builds that start together collide on the uv cache | `Failed to persist temporary file ... uv\cache ... Access is denied`; the label stays in progress | AutoRunner #82, mcp_coder #1369 |
| mcp-tools-py builds always `unstable` | `[tool.mcp-coder.implement] format_code is ignored` | mcp-tools-py #107 (chore) |
| MLflow errors when builds start together | `Failed to set MLflow experiment ... table skills already exists` | mcp_coder #1363, fix group 7 |
| Handled stops end as FAILURE | A specific label set, then `Skipped set-status` and `Workflow failed` | mcp_coder #1363, fix group 5 |
