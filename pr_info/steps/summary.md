# Summary — Opt-in `auto_merge` for `create-pr`, `fix-ci` and `fix-conflict` (#1101)

## Goal

With the per-repo flag `auto_merge` on, mcp-coder squash-merges the PR itself, but only
after CI has really passed on the PR's HEAD commit. One shared, LLM-free helper serves
three commands. With the flag off, behaviour is unchanged except one exit-code change:
an issue ending on `status-74` now exits 1 (Decision 6).

The issue (#1101) is the specification. This plan follows it, with the simplifications
listed under "Design decisions".

## Architectural / design changes

### New module `src/mcp_coder/workflow_steps/merge.py`

The single home of the auto-merge logic. It lives in `workflow_steps`, so it may import
`workflow_utils`, the `mcp_workspace_*` shims and the other `workflow_steps` modules, but
never `mcp_coder.workflows` (import-linter layers).

| Symbol | Role |
|---|---|
| `MergeOutcome` (frozen dataclass) | `label_id: str` + `comment_fields: tuple[CommentField, ...]` (non-empty only for `merge_failed` / `pr_merge_conflict`) |
| `is_real_green(ci_status, ci_ok, expected_sha) -> bool` | `ci_status is not None and ci_ok and run.commit_sha == expected_sha` |
| `resolve_merge_issue_number(project_dir, branch) -> int \| None` | Decision 22: linked → number; lookup failed / raised → branch-name number; unlinked or no number → `None` (label write skipped). Never raises |
| `run_auto_merge(project_dir, branch, *, verified_sha=None) -> MergeOutcome` | Steps 0–3 of the issue: find PR, confirm real green on HEAD, head-SHA re-check, squash merge with `sha=` guard, one mechanical rebase + retry |
| `finish_auto_merge(project_dir, outcome, *, from_label_id, issue_number, update_issue_labels, post_issue_comments) -> int` | Applies the label (`apply_final_label(..., issue_number=)`), then posts the `74`/`99f` comment best-effort, then maps the exit code |

Outcome → label → exit code:

| `label_id` | Meaning | Exit |
|---|---|---|
| `merged` | PR squash-merged | 0 |
| `pr_created` | No PR / ambiguous PR / no `head_sha`, soft pass, head mismatch, rate limit | 0 |
| `failing_ci` | CI red on HEAD | 0 |
| `pr_merge_conflict` | Helper's rebase hit a conflict | 1 |
| `merge_failed` | Refused (409, `blocked`, …), `error`, auth 401/403, failed rebase, any refusal on the retry | 1 |

If the label write fails (`apply_final_label` returns 1), the exit code is 1.

### Design decisions (KISS)

1. **One exception handler.** `run_auto_merge` wraps its whole body in one
   `try/except`: rate limit first (`as_rate_limit`) → `pr_created`; then
   `GithubException` with status 401/403 → `merge_failed` with an `exception_summary`
   field; anything else is re-raised to `run_guarded`. This covers every GitHub call
   listed in Constraint 8, and no partial local state needs cleanup: `_attempt_rebase_and_push`
   raises only from `detect_base_branch`, before any git change, and `_poll_for_ci_completion`
   catches its own errors.
2. **Comment content is built where the data is.** `MergeOutcome.comment_fields` is filled
   inside `run_auto_merge` (merge `outcome`/`status`/`message`/`mergeable_state`, rebase
   `Reason`/`Base`, conflicting files, or the exception summary). `finish_auto_merge` only
   renders them with `build_failure_comment(title="Auto-merge", kind="Failed")`.
3. **Retry is a two-pass loop** (`for attempt in (1, 2)`). On `dirty`/`behind`, the first
   pass rebases; on the second pass every refusal or error becomes `merge_failed`.
4. **Callers resolve the issue number before the merge** and pass it to `finish_auto_merge`:
   create-pr passes `cached_issue_number`; fix-ci / fix-conflict call
   `resolve_merge_issue_number`. `None` → label write skipped with a warning, merge still runs.
5. **One finishing function** for all three commands, so the label → exit mapping and the
   comment code exist once. Callers end with `return finish_auto_merge(...)`.
6. **Flag resolution is one line**: `resolve_auto_merge(args, project_dir)` =
   CLI value if not `None`, else `get_repo_flag(project_dir, "auto_merge")` (default `False`).
   One parser helper `add_auto_merge_arg(parser)` is shared by the three parsers.
7. **create-pr keeps new logic out of `core.py`.** Phase B's final-label write, the
   label → exit mapping and the helper call move into `post_creation.py`;
   `run_post_creation` returns the exit code.
8. **Docs say each caveat once**, in `docs/configuration/config.md`; other docs add their
   label / table rows and link there.

### Behavioural changes per command

- **create-pr (phase B):** `_check_mergeability_and_ci` returns `(label, verified_sha)`,
  where `verified_sha` is set only for a real green. When `auto_merge` is on, the label is
  `pr_created` and `verified_sha` is set, the helper runs **after** the PR description refresh,
  skipping its own CI poll. Phase B's own `74` stays label-only, now exits 1.
- **fix-ci:** on the `ci_ok` path with `auto_merge` on, resolve issue → helper → finish
  (`from_label_id="fixing_ci"`). The helper's CI poll turns a red-but-`True` into `81`.
- **fix-conflict:** on the success path with `auto_merge` on, same pattern
  (`from_label_id="fixing_merge_conflict"`, labels and comments always on). `74` exits 1.

### Labels (`src/mcp_coder/config/labels.json`)

- New `merged` → `status-99:merged` (human_action, display-only).
- New `merge_failed` → `status-99f:merge-failed` (human_action, failure, `/check_branch_status`).
- `status-72:fixing-merge-conflict` stale timeout 15 → 30 minutes.

## Files

### Created

| Path | Purpose |
|---|---|
| `src/mcp_coder/workflow_steps/merge.py` | Auto-merge helper (steps 3, 4) |
| `tests/workflow_steps/test_merge.py` | `run_auto_merge`, `is_real_green`, `resolve_merge_issue_number` tests (step 3) |
| `tests/workflow_steps/test_merge_finish.py` | `finish_auto_merge` tests (step 4) |

### Modified — source

| Path | Step | Change |
|---|---|---|
| `src/mcp_coder/config/labels.json` | 1 | Two labels, `72` timeout |
| `src/mcp_coder/workflows/create_pr/post_creation.py` | 2, 5 | Final label + exit mapping; real-green SHA; helper call |
| `src/mcp_coder/workflows/create_pr/core.py` | 2, 5 | `phase_b` delegates; `auto_merge` parameter |
| `src/mcp_coder/workflows/fix_conflict/core.py` | 2, 7 | `74` → exit 1; `auto_merge` parameter + helper call |
| `src/mcp_coder/mcp_workspace_github.py` | 3 | Re-export `MergeResult` |
| `src/mcp_coder/workflow_utils/failure_handling.py` | 4 | `post_issue_comment` (best-effort) |
| `src/mcp_coder/utils/user_config.py` | 5 | `auto_merge = FieldDef(bool)` |
| `src/mcp_coder/cli/utils.py` | 5 | `resolve_auto_merge` |
| `src/mcp_coder/cli/workflow_parsers.py` | 5, 6, 7 | `add_auto_merge_arg` on three parsers |
| `src/mcp_coder/cli/commands/create_pr.py` | 5 | Pass `auto_merge` |
| `src/mcp_coder/cli/commands/fix_ci.py` | 6 | Pass `auto_merge` |
| `src/mcp_coder/workflows/fix_ci/core.py` | 6 | `auto_merge` parameter + helper call |
| `src/mcp_coder/cli/commands/fix_conflict.py` | 7 | Resolve + pass `auto_merge` |

### Modified — tests

| Path | Step |
|---|---|
| `tests/cli/commands/test_define_labels*.py`, `tests/config/test_label_config.py`, `tests/workflows/vscodeclaude/test_types.py` (label counts / ordered names) | 1 |
| `tests/docs/test_workflow_matrix.py` (unchanged, must pass with new cards) | 1 |
| `tests/workflows/create_pr/test_post_creation.py`, `tests/workflows/create_pr/test_workflow_labels.py` | 2, 5 |
| `tests/workflows/fix_conflict/test_core.py` | 2, 7 |
| `tests/test_mcp_workspace_github_smoke.py` (`__all__` 41 → 42) | 3 |
| `tests/workflow_utils/` failure-handling tests | 4 |
| `tests/cli/test_workflow_parsers.py`, `tests/cli/test_resolver_utils.py` (or the file testing `resolve_issue_interaction_flags`), `tests/cli/commands/test_create_pr.py` | 5 |
| `tests/workflows/fix_ci/test_core.py`, `tests/cli/commands/test_fix_ci.py` | 6 |
| `tests/cli/commands/test_fix_conflict.py` | 7 |

### Modified — docs (step 8)

`docs/configuration/config.md`, `docs/cli-reference.md`, `docs/getting-started/label-setup.md`,
`docs/repository-setup/github.md`, `docs/repository-setup/README.md`,
`docs/coordinator-vscodeclaude.md`, `docs/architecture/architecture.md`,
`docs/processes-prompts/development-process.md`, `docs/processes-prompts/claude_cheat_sheet.md`,
`docs/processes-prompts/processes/08-pr-creation.md`, `.../71-pr-follow-up.md`,
`.../10-pr-merge.md`, `.../failure-handling.md`
(`docs/processes-prompts/github_Issue_Workflow_Matrix.html` is updated in step 1).

## Steps

1. Labels `merged` / `merge_failed`, `72` timeout, workflow-matrix cards
2. `74` exits 1 everywhere; create-pr phase B final label moves into `post_creation.py`
3. `workflow_steps/merge.py`: `run_auto_merge` (+ `MergeResult` shim re-export)
4. `finish_auto_merge` + best-effort `post_issue_comment`
5. `auto_merge` flag resolution + create-pr wiring
6. fix-ci wiring
7. fix-conflict wiring
8. Docs

## Checks (every step)

`run_format_code`, `run_pylint_check`, `run_mypy_check`,
`run_pytest_check(extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not copilot_cli_integration and not install_integration and not jenkins_integration and not langchain_integration and not llm_integration and not textual_integration"])`,
`run_lint_imports_check`, and `check_file_size` for touched files. All must pass before the commit.
