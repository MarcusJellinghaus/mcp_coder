# Analysing Jenkins failures

Goal: a catalogue of failure types where **none is missing and none is invented**. Assigning every build to the right type matters less.

## Steps

1. **Download** the failed workflow builds:
   `tools/jenkins_download_logs.sh --limit 200 --name-pattern ' - #\d+$' --outdir .scratch/jenkins_logs`
2. **Classify**: `tools/jenkins_classify_logs.sh --logdir .scratch/jenkins_logs`.
   It adds `repo`, `issue_identified`, the `venv_*`/`tool_*` versions and `version_mismatch` to `index.csv`, and prints per id the count, last occurrence and mcp-coder version range.
3. **Unmatched logs and `MC-BLOCKED-OTHER`**: read the log, find the line that decides the failure, then add a signature or blocked reason to `jenkins_issue_patterns.toml`. Re-run until nothing is unmatched.
4. **Completeness sweep**: in all logs, list the lines with `ERROR`, `Traceback`, `Access is denied` or a non-zero exit code that no id explains, including secondary problems in builds that already have an id. Each such group becomes a new id or a documented "not an issue".
5. **Verify** each id before reporting it: a quoted log line exists, the regex matches it, and the stated cause is backed by code or logs. Anything inferred is labelled *unverified*.
6. **Status from versions**: if an id's last occurrence predates a fix, or the newest builds don't show it, mark it *likely fixed in &lt;commit/version&gt;*, not open.
7. **Write up** one section per id: example line, regex, source, fix idea, status. GitHub issues are created from that write-up. Then delete `.scratch/`.

## Patterns file rules

- One id per root cause. Prefixes: `PIPE-` Jenkins pipeline, `ENV-` machine/network/package index, `MC-` mcp-coder code, `PROMPT-` plan or prompt content.
- `pre_workflow = true` marks failures before the workflow runs. They also get the `PIPE-NO-STATUS-…` id, because nothing sets a `*-failed` label.
- Blocked reasons: first match wins, so put specific ones before broad ones.
- After a change, diff the `issue_identified` column before and after: only the builds you meant to change may change.
- Target repos in `unsupported_repos` (AutoRunner) are reported separately. Their failures are not mcp-coder issues.

## Tips

- With many logs, use subagents to read them and write their findings to files. Read their summaries, not the logs.
- For LLM-side failures (blocked, review failed), the conversation is in MLflow: `tools/mlflow/`.
- `version_mismatch` lists packages whose repo `.venv` version differs from the tool env that runs the workflow.
