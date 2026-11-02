# Summary — #1266 Smarter rebase: LLM rebase in review, fix-conflict and create_pr

## Goal

Automated workflows rebase with git only today and hand every conflict to a human.
After this change, review and fix-conflict fall back to the LLM rebase
(`run_rebase_workflow`) when the git-only rebase hits `conflict` or `rebase_failed`.
create_pr routes a still-`dirty` PR to fix-conflict (`status-71`) instead of a human.
Hand-off comments name the LLM rebase's abort reason. A line-ending-only dirty tree is
renormalized instead of blocking the rebase (last step, blocked on mcp-workspace#373).

## Architectural / design changes

### Layering

```
workflows/rebase_automated.py   (NEW)  rebase_with_llm_fallback()   <- review, fix-conflict
   ├── workflow_steps/rebase.py        _attempt_rebase_and_push()   (git-only, unchanged contract)
   ├── workflows/rebase_permissions.py rebase_settings_file()       (NEW context manager)
   └── workflows/rebase.py             run_rebase_workflow()        (now returns RebaseRunResult)
```

- The "git-only, then LLM" composition lives in `workflows`, not in
  `_attempt_rebase_and_push`: `workflow_steps` sits below `workflows` in the
  import-linter layers.
- implement and create_pr keep calling `_attempt_rebase_and_push` directly (no LLM).

### Data types

- `RebaseRunResult` (new, frozen dataclass in `workflows/rebase.py`):
  `exit_code: int`, `reason: str`, `push_rejected: bool = False`.
  The CLI returns `result.exit_code` (contract 0 / 1 / 2 unchanged).
  `push_rejected` is the structured push-rejection signal — never match reason text.
- `RebaseOutcome` (existing) gains `llm_detail: str | None = None`.
  The helper changes `reason` only to `"ok"` (LLM success) or `"push_failed"`
  (push rejection). Every other LLM-path failure keeps the git-only reason
  (`conflict` / `rebase_failed`) with the detail in `llm_detail`.
  No new `RebaseReason` values.

### Behaviour of `rebase_with_llm_fallback`

1. Git-only rebase. Anything other than `conflict` / `rebase_failed` → return as-is.
2. Guard: `.mcp-coder/` must be gitignored (checked via `git_check_ignore` on
   `.mcp-coder/rebase_sessions/probe`). Not ignored / check raises → hand-off.
3. LLM rebase with `base_branch=outcome.base_branch`, least-privilege settings
   (`REBASE_LLM_PERMISSIONS` temp file, deleted afterwards) and the pytest marker
   filter `AUTOMATED_EXCLUDED_MARKERS`. Any exception → hand-off with the reason.
4. Exit 0 → plain `push_changes` (never force-with-lease). Rejected → `push_failed`.
5. `push_rejected` → `push_failed`; any other non-zero exit → git-only reason + detail.

### Smaller changes

- Checks: `run_pytest_check` shim accepts `markers` and `timeout_seconds`;
  `REBASE_PYTEST_TIMEOUT_SECONDS = 1800` used by CLI and automated callers.
  Regression-fix prompt gains a `[pytest_marker_filter]` placeholder (empty for the CLI).
- Conflict loop: one marker-retry per conflict stop ("markers remain in X").
- `REBASE_LLM_PERMISSIONS` loses `mcp__mcp-workspace__move_file`.
- fix-conflict CLI gains `--llm-method`, `--mcp-config`, `--settings` (no settings
  auto-detection); Jenkins templates pass `--mcp-config .mcp.json` and set `MCP_TIMEOUT`.
- Hand-off comments (review + fix-conflict) render an `LLM rebase` field.
- Labels: `status-72` stale timeout 60 min, description without "Mechanical";
  `status-74` VSCodeClaude commands `["/rebase", "/check_branch_status"]`.
- create_pr: still `dirty` after its rebase → `merge_conflict` (status-71).
- implement: logs the rebase outcome reason (#430).
- `_attempt_rebase_and_push`: line-ending-only dirt is renormalized and committed
  (all-or-nothing; any real change → `dirty_tree`). Blocked on mcp-workspace#373.

## Files

### Created
- `src/mcp_coder/workflows/rebase_automated.py`
- `tests/workflows/rebase/test_rebase_automated.py`
- `tests/workflows/rebase/test_marker_retry.py`
- `tests/workflows/review/test_after_steps_llm_rebase.py`
- `tests/workflow_steps/test_rebase_line_endings.py`

### Modified (source)
- `src/mcp_coder/workflows/rebase.py`
- `src/mcp_coder/workflows/rebase_checks.py`
- `src/mcp_coder/workflows/rebase_permissions.py`
- `src/mcp_coder/mcp_tools_py.py`
- `src/mcp_coder/mcp_workspace_git.py`
- `src/mcp_coder/prompts/prompts.md`
- `src/mcp_coder/workflow_steps/rebase.py`
- `src/mcp_coder/workflows/review/steps.py`
- `src/mcp_coder/workflows/review/handoff.py`
- `src/mcp_coder/workflows/fix_conflict/core.py`
- `src/mcp_coder/workflows/create_pr/post_creation.py`
- `src/mcp_coder/workflows/create_pr/core.py` (docstring only)
- `src/mcp_coder/workflows/implement/core.py`
- `src/mcp_coder/cli/commands/rebase.py`
- `src/mcp_coder/cli/commands/fix_conflict.py`
- `src/mcp_coder/cli/workflow_parsers.py`
- `src/mcp_coder/cli/commands/coordinator/command_templates.py`
- `src/mcp_coder/config/labels.json`

### Modified (tests)
- `tests/workflows/rebase/*` (return type, markers, prompt, permissions)
- `tests/test_mcp_tools_py.py`
- `tests/cli/commands/test_rebase.py`, `tests/cli/commands/test_fix_conflict.py`
- `tests/workflows/fix_conflict/test_core.py`
- `tests/workflows/create_pr/test_post_creation.py`, `tests/workflows/create_pr/test_workflow_labels.py`
- `tests/workflows/implement/test_core_workflow.py`
- `tests/cli/commands/coordinator/test_command_templates.py`
- `tests/cli/commands/test_define_labels_config.py`, `tests/config/test_label_config.py`

### Modified (docs)
- `docs/processes-prompts/processes/08-pr-creation.md`
- `docs/processes-prompts/processes/71-pr-follow-up.md`
- `docs/processes-prompts/processes/17-automated-code-review.md`
- `docs/processes-prompts/processes/failure-handling.md`
- `docs/cli-reference.md`
- `docs/getting-started/label-setup.md`
- `docs/processes-prompts/claude_cheat_sheet.md`
- `docs/coordinator-vscodeclaude.md`
- `docs/repository-setup/github.md`
- `docs/repository-setup/repo.md`

## Steps

| Step | Content |
|---|---|
| 1 | `RebaseRunResult` returned by `run_rebase_workflow`; CLI maps to exit code |
| 2 | pytest marker filter + timeout threaded to the shim; prompt placeholder |
| 3 | Marker retry once per conflict stop |
| 4 | Permissions: drop `move_file`; `rebase_settings_file` context manager |
| 5 | Shared helper `rebase_with_llm_fallback` (+ `llm_detail`, `git_check_ignore` re-export) |
| 6 | Review wiring + `LLM rebase` field in hand-off comment |
| 7 | fix-conflict wiring (CLI args, workflow, comment field, Jenkins templates) |
| 8 | Labels: `status-72` timeout/description, `status-74` commands |
| 9 | create_pr: still `dirty` → `status-71` |
| 10 | implement: log rebase outcome reason |
| 11 | Docs |
| 12 | Line-ending-only dirty tree (blocked on mcp-workspace#373) |

Every step: tests first, then implementation; pylint, pytest (fast unit set),
mypy and lint-imports pass; `run_format_code`; exactly one commit.
