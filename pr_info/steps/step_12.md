# Step 12 — Docs

## LLM prompt
> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_12.md` exactly.
> Read the current code in `src/mcp_coder/workflows/create_pr/` first so the docs match it.
> Run pylint, pytest (fast unit set, `-n auto`) and mypy to confirm nothing broke. Make exactly one commit.

## WHERE
- `docs/processes-prompts/development-process.md` — §6 "PR Creation Workflow" (~line 962), §10 "PR-Health (status-10)" (~line 1188)
- `docs/cli-reference.md` — `### create-pr` (~line 448)
- `docs/coordinator-vscodeclaude.md` — PR-health section (review only; edit only if it contradicts the new flow)

## WHAT
- §6: the new flow — rebase if behind → summary (excludes `pr_info/`) → cleanup/push → create PR → mergeability
  (rebase once on `dirty`) → CI wait (no fixing) → final label. Label table: 10 / 74 / 81 / 09f as in the issue.
  Resume: an open PR skips to the post-creation checks (cleanup first if `pr_info/` is still on the branch), which makes
  `09f` recovery safe after a Jenkins kill. Stale timeout of `status-09` is 30 min.
- §10: create-pr now does the first conflict/CI check itself; PR-health takes over on `unknown`, CI timeout or no CI.
- `cli-reference.md`: describe the post-creation checks, that they run even without `--update-issue-labels`
  (outcome only logged), and exit code 0 for every handled post-creation outcome.

## HOW
Keep additions short; follow the writing style in `.claude/CLAUDE.md`. Do not document the description refresh yet (step 15 does).

## DATA
None.
