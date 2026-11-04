# Summary: CI fix loop stops on a rejected push and treats no-change fixes as failures (#1376)

## Goal

Two behaviours in `check_and_fix_ci` (shared by `implement`, `fix-ci`, automated code review and `check_branch_status`) are wrong:

1. A push rejected because the branch moved is retried and reported as broken CI.
2. A CI fix that changes nothing, or an empty analysis on attempt 2 or later, can end as `True` while CI is still red.

After this change:

- A rejected push stops the loop at once, and each workflow reports it under its own CI label.
- A no-change fix and a late empty analysis each consume one attempt of the existing budget.

## Architectural / design changes

### New signal: `PushRejectedError`

- Defined in `workflow_steps/commit.py`, raised by `push_changes(..., raise_on_rejected=True)` outside its broad `try`.
- `push_changes` stays opt-in, so other callers and their mocks are unchanged.
- The message is one fixed sentence followed by git's status line. There is no extra attribute, because callers only use `str(exc)`.
- Detection matches only git's own status line, anchored at line start:

  ```python
  r"^[ \t]*! \[rejected\] .*\((?:fetch first|non-fast-forward)\)"  # re.MULTILINE
  ```

  This excludes `[remote rejected]`, a hook echo starting `remote:`, `hint:` lines, and the `cmdline:` line, which carries the branch name.

- `check_and_fix_ci` never catches it, so it reaches every caller. It must never come back as `True`.
- `llm_failure_reason` is unchanged: it lives below `workflow_steps` in `.importlinter`, and this is not an LLM failure.

### Reporting per caller

| Caller | Label | Reporting |
|---|---|---|
| `implement` | `status-06f-ci:ci-fix-needed` | New reason `branch_moved` in `FAILURE_LABELS` and `CATEGORY_DISPLAY` |
| `fix-ci` | `status-84:pr-ci-failed` | `WorkflowFailure.category` stays `pr_ci_failed`; display category "Branch Moved"; no PR description refresh |
| Automated code review | `status-17f-ci:code-review-ci-fix-needed` | New reason `branch_moved`, terminal in dismiss and mid-loop paths. `review/core.py` already treats unknown reasons as terminal, so only a comment changes there |
| `check_branch_status` | none | Explicit log message, returns `False`, no retry |

The comment's `Error` field holds `str(exc)`. Its `Next step` field holds the shared constant `BRANCH_MOVED_NEXT_STEP` plus a recovery sentence per workflow:

| Workflow | Recovery sentence |
|---|---|
| `fix-ci` | ``Then set `status-10:pr-created` so CI is re-detected.`` |
| `implement` | ``Then set `status-05:plan-ready`.`` |
| Review | ``Then set `status-17:code-review-bot`.`` |

### No-change detection

- New module `workflow_steps/ci_fix_helpers.py` holds:
  - `CIFixState`, with one field, `push_pending`.
  - `read_head`, which never raises.
  - `discard_if_no_change`, which never raises.
  - `_read_problem_description`, moved from `ci.py` only to stay under CI's 750-line limit.
- `_run_ci_fix` captures HEAD just before this attempt's fix LLM call, and checks after `run_formatters`, so a formatter-only change still counts.
- No changes means HEAD is unchanged and the tree is clean, ignoring `pr_info/.commit_message.txt` and `DEFAULT_IGNORED_BUILD_ARTIFACTS`. Any failed read counts as "has changes", which keeps today's behaviour.
- A no-change attempt deletes the message file and skips `commit_changes`. It pushes only if an earlier attempt's push failed (`state.push_pending`).

### Constraints

- The CI fix loop never force-pushes or rebases over someone else's commits.
- No pre-flight sync and no comparison with the remote tip.
- Authentication, network and hook-decline failures keep their current behaviour.
- `define-labels` is a manual step after merge, not part of this plan.
- Do not add files to `.large-files-allowlist`.
- Do not edit `tests/workflow_steps/test_ci.py` or `tests/workflows/implement/test_core_workflow.py`; both are near the limit.

## Files

### Created

| File | Purpose |
|---|---|
| `src/mcp_coder/workflow_steps/ci_fix_helpers.py` | State object, HEAD read, no-change check, moved `_read_problem_description` |
| `tests/workflow_steps/test_ci_fix_loop.py` | Loop behaviour: rejected push, empty analysis, no-change, push retry |
| `tests/workflow_steps/test_ci_fix_helpers.py` | Unit tests for the new helpers |
| `tests/workflow_steps/test_commit_push_rejected.py` | Detection, including real-git bare-repo tests |

### Modified: source

- `src/mcp_coder/workflow_steps/commit.py`
- `src/mcp_coder/workflow_steps/ci.py`
- `src/mcp_coder/workflows/implement/core.py`
- `src/mcp_coder/workflows/implement/failure_reporting.py`
- `src/mcp_coder/workflows/fix_ci/core.py`
- `src/mcp_coder/workflows/review/steps.py`
- `src/mcp_coder/workflows/review/handoff.py`
- `src/mcp_coder/workflows/review/config.py`
- `src/mcp_coder/workflows/review/core.py` (comment only)
- `src/mcp_coder/cli/commands/check_branch_status.py`
- `src/mcp_coder/config/labels.json`

### Modified: tests

- `tests/workflows/implement/test_core_failure_categories.py`
- `tests/workflows/implement/test_failure_reporting.py`
- `tests/workflows/fix_ci/test_core.py`
- `tests/workflows/review/test_config.py`
- `tests/workflows/review/test_core_flush_ci.py`
- `tests/cli/commands/test_check_branch_status_auto_fixes.py`

### Modified: docs

- `docs/getting-started/label-setup.md`
- `docs/cli-reference.md`
- `docs/processes-prompts/claude_cheat_sheet.md`
- `docs/processes-prompts/github_Issue_Workflow_Matrix.html`
- `docs/processes-prompts/processes/05-implementation.md`
- `docs/processes-prompts/processes/17-automated-code-review.md`
- `docs/processes-prompts/processes/71-pr-follow-up.md`

## Step order

Handlers land before the loop starts raising, so every commit leaves all workflows correct.

| Step | Commit |
|---|---|
| 1 | `PushRejectedError` and opt-in detection in `push_changes` |
| 2 | `implement` handler |
| 3 | `fix-ci` handler |
| 4 | Automated code review handler |
| 5 | `check_branch_status` handler |
| 6 | Loop stops on a rejected push |
| 7 | Empty analysis on attempt 2 or later counts as a failed attempt |
| 8 | Move `_read_problem_description` into `ci_fix_helpers.py` |
| 9 | No-change fix counts as a failed attempt, with push retry |
| 10 | Label descriptions and docs |

## Checks for every step

Run these before finishing a step, and fix anything they report:

- `mcp__mcp-tools-py__run_format_code`
- `mcp__mcp-tools-py__run_pylint_check`
- `mcp__mcp-tools-py__run_mypy_check`
- `mcp__mcp-tools-py__run_pytest_check` with `extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not copilot_cli_integration and not install_integration and not jenkins_integration and not langchain_integration and not llm_integration and not textual_integration"]`
