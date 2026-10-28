# Step 13 — Docs: rate-limit behaviour and cache files

## LLM prompt
> Read `pr_info/steps/summary.md` and this file (`pr_info/steps/step_13.md`).
> Implement only Step 13 (documentation only). Run pylint, pytest (fast unit
> marker set, `-n auto`) and mypy to confirm nothing broke. Produce exactly one commit.

## WHERE
- `docs/coordinator-vscodeclaude.md`

## WHAT
Add a short "GitHub rate limits and caches" section:
- Stop on first error: a GitHub rate limit stops all remaining GitHub work of
  `coordinator`, `vscodeclaude launch` and `vscodeclaude status`; one log line
  names the reset time ("reset time unknown" for GraphQL / retry errors); exit 0.
- Exception: coordinator partial dispatch (Jenkins job started, label not
  updated) → one ERROR naming the issue, exit non-zero.
- `vscodeclaude launch` after a limit: cleanup and the session bookkeeping
  (`apply_assessments`) still run; restart, PR health and launch are skipped.
- `vscodeclaude status` under a limit prints only the rate-limit line, no table
  (same for `--explain`).
- A session whose issue state cannot be fetched is never treated as closed/stale.
- Cache files next to `.issues.json` (same directory, same repo prefix):
  `.prs.json` (open PRs + PR-health results) and `.branches.json`
  (issue → branch lookups), shared by all processes.
- Workflows (`--update-labels`, and always for `fix-conflict`): a failed final
  label update is retried once after ~30 s, then the workflow exits non-zero.
- Link to `docs/configuration/config.md` for the `traffic_log` switch.

## HOW
Before writing, confirm the cache file names with
`get_library_source("mcp_workspace.github_operations.caching._store.cache_file_path")`;
if they do not end in `.prs.json` / `.branches.json`, write one line to
`pr_info/.blocked.txt` and stop.

## DATA
None.
