---
description: Follow an issue's (or all) mcp-coder Jenkins builds until something needs a look, then analyse it
argument-hint: "[issue number] [repo, default mcp_coder]"
allowed-tools:
  - "Bash(tools/jenkins_watch.sh *)"
  - mcp__mcp-workspace__read_file
  - mcp__mcp-workspace__search_files
  - mcp__mcp-workspace__github_issue_view
  - mcp__mcp-workspace__delete_directory
---

# Jenkins Watch

Follows mcp-coder's automated workflow on Jenkins (create-plan, review-plan, implement, create-pr, ...) and comes back only when something needs a look. The polling is done by `tools/jenkins_watch.sh` in the mcp-coder repository, not by you, so waiting costs no tokens.

**Arguments:** `$ARGUMENTS` — an issue number and optionally the repo name as it appears in the build name (default `mcp_coder`). No issue: watch all builds of the executor job.

## Rules

- **Approval before any GitHub write:** status labels, `blocked` / `wait`, comments, new issues. Propose first, then wait.
- Don't read whole console logs yourself. They are long; the watcher saves them and the analysis subagent reads the relevant lines.
- **Run folder:** the watcher's logs go to one folder per watch, `.scratch/jenkins_watch_<issue or all>_<date>/` (e.g. `.scratch/jenkins_watch_1490_2026-11-27/`). Pass it as `--log-dir` to every watcher command that saves logs (the watch, `--watch-only`, `--inspect`); restarts within one watch reuse it. The watcher creates it. Other sessions may share `.scratch/`: never write the logs anywhere else, and never delete anything there but this folder.
- Background: `docs/processes-prompts/development-process.md` (labels, steps) and `docs/processes-prompts/processes/failure-handling.md` (failure labels, retry labels) in the mcp-coder repository, via `read_file`.

## Loop

1. **Start the watcher in the background** (`run_in_background: true`), and wait for its completion notice. Don't poll its output or sleep.

   ```bash
   tools/jenkins_watch.sh --issue <N> --repo <repo> --log-dir <run folder>
   tools/jenkins_watch.sh --log-dir <run folder>            # all builds
   ```

   It first checks the current state: it prints the running builds, else the newest build, and if that one ended badly it exits at once with `problem` and the log scan. Only if nothing needs a look does it wait. Right after a retry, add `--watch-only`: the old failure is still the newest build until the coordinator starts the new one.

   Defaults: list the builds every 15 s (`--interval`), `--idle 20` min, `--stall 60` min, `--report 120` min. The polls are cheap and print nothing unless something changed; a running build's log is downloaded only every 5 min for the stall check, and when it is reported. A running build is fine as long as its console log grows; long implementations (two hours and more) are normal. Jenkins must fail every poll for 5 min before the watch ends with `jenkins-error`. It prints each new build and status change; for each finished build it saves the log to `<run folder>/jenkins_log_<issue>_<step>_<build>_<date>_<time>.txt` and prints the scan: the command section's line range (between `command execution ===` and `archive after execution ===`), counts of errors, deciding lines and warnings, the last label change (`label: status-17i:code-reviewing → status-07:code-review`), and the first 25 matches with line numbers. Errors and deciding lines (`Error:`, the handoff `Reason:`) are printed in full, warnings cut at 200 characters.

2. **Read the watcher's output** (the output file named in the completion notice) and act on the `RESULT:` line. The exit code is 0 for all of them except `jenkins-error` (3); 2 means bad arguments.

   | `RESULT:` | Action |
   |---|---|
   | `idle` | `github_issue_view` the issue. Label a bot picks up (`02`, `05`, `08`, `14`, `17`) without `blocked` / `wait` → restart the watcher (step 1). Human-action label (`04`, `07`, `10`, ...) or closed → report: done, or what you need to do next |
   | `problem` | Analyse (step 3). For `unstable`: if the `label:` line shows the label moved on as expected, it was a warning only → mention it and restart the watcher |
   | `stalled` | A running build wrote no log output for `--stall` minutes. The scan of its log so far is in the output → analyse (step 3), then report |
   | `jenkins-error` | Report. Suggest `mcp-coder verify` (JENKINS sections) |
   | `heartbeat` | Still running, log still growing. Tell the user in one or two lines (step, how long, anything the scan flagged), then restart with `--watch-only` |

3. **Analyse a problem.**
   - Read the failure comment on the issue first (`github_issue_view` with comments: Category / Stage / Error). It often settles the cause.
   - Otherwise start a subagent (`general-purpose`) to read the log. Give it the log path (the watcher's `log:` line), the command-section line range and the matches the watcher printed, and ask for: the cause in two or three sentences, with the deciding log lines quoted by line number; whether it is transient or needs a fix; the fix. Tell it to read only the command section with `read_file(start_line, end_line)`, and more only if the section does not explain the failure.
   - More logs: `tools/jenkins_watch.sh --list --issue <N> --repo <repo>` lists the issue's builds (start, duration, status, number, step), oldest first. `tools/jenkins_watch.sh --inspect <build> [<build> ...] --log-dir <run folder>` saves and scans those builds, also a running one (its log so far).

4. **Report** to the user: issue, build, step, result, cause, and a proposal: the fix, then the retry label from `failure-handling.md` (set with `github_issue_set_status` only after approval). After the fix and retry, offer to restart the watcher with `--watch-only`.

5. **Clean up** when the watch ends: delete the run folder with `delete_directory(<run folder>, recursive=True)`. Never delete `.scratch/` itself or files by pattern.
