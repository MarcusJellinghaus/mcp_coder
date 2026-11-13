# Step 3 — Executable bit on `tools/jenkins_download_log.sh` (human action)

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_3.md`.
> This step has no file changes. Do not attempt to set the executable bit and do not edit
> any other file. Write exactly one line to `pr_info/.blocked.txt` (text below) and stop.

## WHERE

- `pr_info/.blocked.txt` (created by the implement run; not a source change)

## WHAT

All existing `tools/*.sh` are mode `100755` in git. `tools/jenkins_download_log.sh`
(created in step 2) needs the same. Setting it requires
`git add --chmod=+x tools/jenkins_download_log.sh`, i.e. Bash, which the implement
workflow does not have.

This is a separate last step on purpose: a block inside a step takes the failure path with
no rescue commit, so any edits made in this step would be lost.

## HOW

Write `pr_info/.blocked.txt` with exactly this one line:

```
exec bit: tools/jenkins_download_log.sh needs git add --chmod=+x; Bash is disabled
```

Keep it verbatim — no `owner/repo#N` reference. `[[blocked.reason]]` patterns in
`tools/jenkins_issue_patterns.toml` are first-match-wins; this text classifies as
`MC-BLOCKED-NO-SHELL`, while an issue reference would classify it as an external
prerequisite. The run ends `implementation-blocked`, which is the intended escalation.

## ALGORITHM

```
write pr_info/.blocked.txt with the line above
stop
```

## DATA

None.

## Human follow-up (not done by the implement run)

1. `git add --chmod=+x tools/jenkins_download_log.sh`
2. In `pr_info/TASK_TRACKER.md`, tick **all** checkboxes of this step (not only the
   implementation sub-task).
3. Commit and push both — the re-run needs a clean tree.
4. Reset the status as described in the blocked-implementation recovery in
   `docs/processes-prompts/processes/05-implementation.md`
   (`mcp-coder gh-tool set-status status-05:plan-ready`).

## Checks

None — no code changes.
