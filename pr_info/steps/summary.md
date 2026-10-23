# Summary — #1286 create-pr: rebase if needed, verify mergeability, wait for CI, refresh PR description

## Goal
`create-pr` today opens the PR and sets `status-10` blindly. After this change it:
1. rebases before the summary when the branch is behind its base,
2. after creation checks `mergeable_state` (rebasing once on `dirty`),
3. waits for CI (no fixing),
4. sets the final label from the outcome (`10` / `74` / `81`),
5. resumes cleanly when re-run with an open PR for the branch,
6. refreshes the PR title/body when it (or `fix-ci`) pushed new commits.

Part 6 depends on `PullRequestManager.update_pull_request` (MarcusJellinghaus/mcp-workspace#349).
Steps 13–15 check for it first and write to `pr_info/.blocked.txt` if it is missing.

## Architectural / design changes

### create-pr is split into two guarded phases
`run_create_pr_workflow` calls `run_guarded` twice. `run_guarded` itself is unchanged.

| Phase | Contents | Crash fallback label |
|---|---|---|
| Pre-guard | branch-issue linkage, `find_pull_request_by_head` (resume check), closing-references fallback on resume | — |
| Phase A | prerequisites → rebase-if-needed → summary → cleanup/commit/push → create PR → closing-references fallback. On resume: only `check_git_clean` + cleanup/commit/push when `pr_info/` exists | `pr_creating_failed` (09f) |
| Phase B | `run_post_creation()` → final label (or log only when labels are off) | `pr_created` (10) |

- Phase A returning non-zero ends the workflow (exit 1). Phase B always returns 0 on handled outcomes.
- The issue number is a `nonlocal` in `run_create_pr_workflow`; phase A may fill it via the
  closing-references fallback, and phase B's `run_guarded(issue_number=...)` is called afterwards, so it sees the value.
- The closing-references fallback keeps today's `update_issue_labels` gate (with labels off, no label is set, so no issue number is needed).

### Phase B (new module `workflows/create_pr/post_creation.py`)
```
state = poll mergeable
if state == "dirty": rebase+push; state = poll mergeable
if state == "dirty": -> pr_merge_conflict (74), no CI wait
ci_status, ok = _poll_for_ci_completion(..., expected_sha=local HEAD)
-> failing_ci (81) if ci_status is not None and not ok, else pr_created (10)
```
`unknown`, `None`, and behind-but-not-dirty all fall through to the CI wait. CI timeout, no CI, API errors → `pr_created`.

### Shared helpers
- `_poll_mergeable_state` moves from `workflows/fix_conflict/core.py` to `workflow_steps/rebase.py`.
  Both callers use it right after `_attempt_rebase_and_push`.
- `parse_pr_summary`, `ensure_closing_reference`, `_CLOSING_REF_RE` move to a new
  `workflow_steps/pr_description.py`, which also gets `closing_issue_numbers(body)` and `refresh_pr_description(...)`.
  `workflow_steps` cannot import `workflows`, and `fix-ci` needs the refresh too.
  `create_pr/helpers.py` and `create_pr/core.py` keep re-exports.

### CI polling fixes (`workflow_steps/ci.py`, shared by all callers)
- `lookup_failed` is read from the top level of `CIStatusData`, not from `run`.
- With `expected_sha` given, "no run yet" and "run for another commit" count against the same counter,
  capped by `CI_EXPECTED_SHA_MAX_POLL_ATTEMPTS` (~105 s). The no-run exit still logs `CI_NOT_CONFIGURED`.

### Description refresh
Callers compare local HEAD before and after their own pushes and call `refresh_pr_description` only when it changed:
- create-pr phase B: HEAD at the start of phase B vs after the CI wait.
- `fix-ci`: HEAD before vs after `check_and_fix_ci`, on every outcome.

The refresh is best-effort and never changes a label. The LLM may answer `UNCHANGED`. Closing references are taken from the current PR body and re-applied.

### Config
- `labels.json`: `status-09:pr-creating` `stale_timeout_minutes` 15 → 30.
- `ci.yml`: `pull_request: branches: [ "**" ]`.

## Files

### Created
- `src/mcp_coder/workflows/create_pr/pre_creation.py` — `_rebase_if_needed`, `_find_open_pr`, `_resume_cleanup`
  (keeps `create_pr/core.py`, ~705 lines today, under the 750-line CI file-size gate).
- `src/mcp_coder/workflows/create_pr/post_creation.py` — phase B logic.
- `src/mcp_coder/workflow_steps/pr_description.py` — PR text helpers + refresh.
- `tests/workflows/create_pr/test_pre_creation.py`
- `tests/workflows/create_pr/test_post_creation.py`
- `tests/workflows/create_pr/test_resume.py`
- `tests/workflow_steps/test_pr_description.py`

### Modified
- `src/mcp_coder/workflow_steps/ci.py`
- `src/mcp_coder/workflow_steps/rebase.py`
- `src/mcp_coder/workflows/fix_conflict/core.py`
- `src/mcp_coder/workflows/create_pr/core.py`
- `src/mcp_coder/workflows/create_pr/helpers.py`
- `src/mcp_coder/workflows/fix_ci/core.py`
- `src/mcp_coder/prompts/prompts.md`
- `src/mcp_coder/config/labels.json`
- `.github/workflows/ci.yml`
- `tests/workflow_steps/test_ci.py`
- `tests/workflow_steps/test_rebase.py`
- `tests/workflows/fix_conflict/test_core.py`
- `tests/workflows/create_pr/test_generation.py`
- `tests/workflows/create_pr/test_workflow.py`
- `tests/workflows/fix_ci/test_core.py` (fix-ci refresh)
- `tests/cli/commands/test_define_labels_config.py`
- `docs/processes-prompts/development-process.md` (§6, §10)
- `docs/cli-reference.md` (`create-pr`)
- `docs/coordinator-vscodeclaude.md` (PR-health section, review only)

## Steps
| # | Step | Blocked by #349 |
|---|---|---|
| 1 | CI: read `lookup_failed` from top level | no |
| 2 | CI: cap "no run" wait when `expected_sha` is given | no |
| 3 | Move `_poll_mergeable_state` to `workflow_steps/rebase.py` | no |
| 4 | `labels.json`: 09 stale timeout 30 min | no |
| 5 | `ci.yml`: `pull_request` for all bases | no |
| 6 | Summary diff excludes all of `pr_info/` | no |
| 7 | Rebase-if-needed before the summary | no |
| 8 | Refactor: extract `_cleanup_commit_push`, `_resolve_issue_from_pr` | no |
| 9 | Phase B module `post_creation.run_post_creation` | no |
| 10 | Wire phase B into create-pr (two guards, final label, exit 0) | no |
| 11 | Resume path (open PR → skip to phase B) | no |
| 12 | Docs | no |
| 13 | Move PR text helpers to `workflow_steps/pr_description.py` | yes |
| 14 | `refresh_pr_description` + prompt | yes |
| 15 | Call the refresh from create-pr phase B and `fix-ci` | yes |
