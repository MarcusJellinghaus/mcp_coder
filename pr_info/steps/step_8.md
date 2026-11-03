# Step 8 — Docs

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement **only** `pr_info/steps/step_8.md`.
> Docs only — no code. Put every caveat once in `docs/configuration/config.md`; other docs
> add their label / table rows and link to it. Re-check each target exists (the docs were
> restructured in #1370). Run pytest (fast unit set, `-n auto`, includes `tests/docs/`) and
> `check_file_size`; make them pass. Produce exactly one commit.

## Precondition

If `docs/configuration/config.md` has no per-repo flag table (the one listing
`auto_review_implementation`), write one line to `pr_info/.blocked.txt` and stop.

## WHERE / WHAT

| File | Change |
|---|---|
| `docs/configuration/config.md` | Row `auto_merge` (boolean, default `false`) in the repo-flag table + example line. New subsection "Auto-merge" with: what it does (squash merge after a real green on HEAD; create-pr, fix-ci, fix-conflict); `--auto-merge/--no-auto-merge` overrides; must be set in the **Jenkins executor's** `config.toml`; enable "Automatically delete head branches"; squash merging must be enabled, else every run ends on `99f`; required review approvals → always `99f`; recommend branch protection with the PR checks required (false-green race); repos without CI, skipped/neutral/action-required runs, and CI runs longer than the 12.5-minute poll cap never auto-merge; a CI run must appear for the pushed SHA within ~105 s or the wait soft-passes; rate-limit caveat (issue may stay on the busy label → Jenkins fallback); branch not linked to an issue → label skipped, Jenkins fallback label after a merge; **warning**: auto-merge removes the merge as the last human step, so bot-written code merges without review unless branch protection requires approvals; link to the issue-body trust gate (#1375) |
| `docs/cli-reference.md` | `--auto-merge` on `create-pr`, `fix-ci`, `fix-conflict`; outcomes `99` / `99f`; exit codes (0: `99`, `10`, `81`; 1: `74`, `99f`); fix-conflict's `74` now exits 1 |
| `docs/getting-started/label-setup.md` | Rows `status-99:merged`, `status-99f:merge-failed`; note: a custom `labels-config` must add `merged` and `merge_failed` and re-run `define-labels`, else the label write fails after a successful merge |
| `docs/repository-setup/github.md` | Stale-timeout table: add a `72` row (30 min, two CI waits); adjust the `09` rationale (worst case ≈ 35 min, stale warning accepted). File is near the size limit — keep it terse |
| `docs/repository-setup/README.md` | Optional flag `auto_merge` (default `false`) with link to config.md |
| `docs/coordinator-vscodeclaude.md` | `99` (display-only) and `99f` (`/check_branch_status`) |
| `docs/architecture/architecture.md` | `workflow_steps/merge.py` as the shared auto-merge step |
| `docs/processes-prompts/development-process.md` | PR-merge row: automated with `auto_merge` |
| `docs/processes-prompts/claude_cheat_sheet.md` | Label rows `99`, `99f` |
| `docs/processes-prompts/processes/08-pr-creation.md` | Outcome table: `99` / `99f`; `74` exits 1 |
| `docs/processes-prompts/processes/71-pr-follow-up.md` | fix-ci / fix-conflict end on `99` / `99f` with `auto_merge` |
| `docs/processes-prompts/processes/10-pr-merge.md` | No longer "the only strictly human step" when `auto_merge` is on; `99` matters for PRs into a non-default base (issue not auto-closed) |
| `docs/processes-prompts/processes/failure-handling.md` | Failure-label table row `status-99f:merge-failed` |

## Done when

All listed docs mention the flag / labels where relevant; `tests/docs/` passes; no file
exceeds the size limit.
