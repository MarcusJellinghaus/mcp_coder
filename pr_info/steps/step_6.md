# Step 6 — Documentation

## LLM prompt

> Read `pr_info/steps/summary.md` and this file (`pr_info/steps/step_6.md`). Implement step 6 only:
> update the docs listed below so they describe PR-health running in the Jenkins `coordinator`
> (inside the executor capacity gate) instead of `vscodeclaude launch`. Follow the Writing style in
> `.claude/CLAUDE.md`: short, no filler. No code changes. Run the checks from the summary; produce
> exactly one commit.

## WHERE / WHAT

`docs/coordinator-vscodeclaude.md` (PR-health section stays on this page, reworded):
- ~line 112: PR-health runs in `mcp-coder coordinator` on Jenkins, per repo, only while that repo's
  executor job has capacity (busy job → no GitHub call; detection resumes on the next run with
  capacity). Remove "on every `coordinator vscodeclaude` run" and "whether or not a session slot is
  free". Selection: open `status-10:pr-created` issues, any assignee, no `ignore_labels`.
- ~line 121: `trusted_commenters` must be set on both hosts — the Jenkins coordinator agent (PR-health)
  and the vscodeclaude host (❌ notes in the status file, `workflows/vscodeclaude/workspace.py`).
- ~line 178: the commands share one GitHub API budget only when they use the same token; the Jenkins
  coordinator may use a different one (e.g. a machine user).
- ~line 181: `vscodeclaude launch` no longer runs PR-health; drop it from that rate-limit bullet.
- ~line 186: caches are per machine and user account (`~/.mcp_coder/coordinator_cache/`), not "shared by
  all processes"; `.prs.json` is coordinator-only, `.branches.json` is used by both.
- ~line 190: `<repo>.prs.json` lives on the coordinator's host.
- Mention: an open issue with more than one `status-*` label is logged as ERROR every coordinator run
  (build UNSTABLE) until fixed.

`docs/processes-prompts/processes/71-pr-follow-up.md` line 3: "the vscodeclaude coordinator checks it"
→ "the Jenkins coordinator checks it".

`docs/getting-started/label-setup.md` line 319: name the Jenkins coordinator; "on every poll" → "on
every run while the executor job has capacity".

`docs/repository-setup/jenkins.md`:
- in "Executor Capacity Gate" (or a short new subsection): PR-health runs inside the capacity gate;
  busy repos still get no GitHub call;
- the agent's mcp-coder config needs `[github] trusted_commenters`, and its `[github] token` needs the
  PR-health permissions (Actions Read, Code scanning alerts Read, Pull requests Read);
- link to `../coordinator-vscodeclaude.md#pr-health-checks-for-status-10pr-created`.

`docs/cli-reference.md` `### coordinator` (line ~368): add that the PR checks run only while the
executor job has capacity, and that `vscodeclaude launch` no longer runs them.

`docs/repository-setup/github.md`:
- line 32 (Actions Read) and line 34 (Code scanning alerts Read): "vscodeclaude
  (`workflows/vscodeclaude/checks.py`...)" → "Jenkins coordinator PR-health (`workflows/pr_health/checks.py`...)";
- line 37 (Issues): "the vscodeclaude `status-91` escalation" → "the coordinator PR-health escalations
  (`status-71` / `81` / `91`)";
- line 39 (Pull requests): add PR-health as a read consumer (list open PRs, `mergeable_state`, review threads);
- line 64: "vscodeclaude silently does nothing about alerts" → "the coordinator's PR-health silently does nothing about alerts".

`docs/architecture/architecture.md`:
- line 57: "on every poll" → "on every run while the executor job has capacity";
- line 90 (`workflows` row): add `pr_health` to the package list.

## ALGORITHM / DATA

None.

## Verify

- `mcp__mcp-workspace__search_files` in `docs/` for `vscodeclaude/checks`, `vscodeclaude coordinator checks`,
  `on every poll` → no stale hits about PR-health.
- Anchor link in `jenkins.md` resolves to the heading in `coordinator-vscodeclaude.md`.
