# Step 7 — Docs: config.md flags + `executor_test_path` → `executor_job_path` rename

**Read `pr_info/steps/summary.md` first** (concern (B) doc-correctness + §5/§7). Doc-only step
(plus one stale source docstring). No tests assert these strings, so no test change is required.
This is a **separate, second concern** riding in this PR — call it out in the PR description.

## WHERE
- Modify `docs/configuration/config.md`.
- Modify `src/mcp_coder/cli/commands/coordinator/core.py` — the stale docstring at line ~377 that
  says `executor_test_path` (should read `executor_job_path`).

## WHAT — 1. Add two flag rows
In the `[coordinator.repos.*]` flag table (around `config.md:446-447`, alongside
`update_issue_labels` / `post_issue_comments`), add:
- `auto_review_plan` — type `boolean`, default `false`, "Gate automated plan review (routes
  create-plan success to `status-14:plan-review-bot` for coordinator pickup)."
- `auto_review_implementation` — type `boolean`, default `false`, "Gate automated implementation
  review (routes implement success to `status-17:code-review-bot` for coordinator pickup)."

## WHAT — 2. Rename `executor_test_path` → `executor_job_path`
The real schema field is `executor_job_path` (`utils/user_config.py:65`, `required=True`).
`config.md` uses the wrong name in 15 places:
`:91, :96, :102, :444, :453, :494, :774, :781, :899, :916, :933, :951, :957, :963, :987`.
Rename **all** occurrences, including the example error message at `:781` (should read
`executor_job_path` to match what the verifier emits). Also fix the `core.py:377` docstring.

## HOW
- Use a doc-wide find/replace of `executor_test_path` → `executor_job_path`; then verify zero
  remaining occurrences: `search_files(pattern="executor_test_path")` must return nothing across
  `docs/` and `src/`.
- Keep surrounding TOML examples otherwise unchanged.

## ALGORITHM
n/a (documentation edit).

## DATA
n/a.

## TESTS
None (doc + docstring only). Verify:
- `search_files(pattern="executor_test_path")` → no matches anywhere.
- Both new flag rows are present in the `[coordinator.repos.*]` table.
- `run_mypy_check` / `run_pylint_check` still clean (docstring edit only).

## Commit
One commit: config.md edits + docstring fix. Run pylint, pytest (`-n auto` unit exclusion), mypy
(sanity — docstring only), and a final `search_files` sweep for the old field name.
