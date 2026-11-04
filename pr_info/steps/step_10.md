# Step 10: Label descriptions and docs

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_10.md`. Run the checks listed in the summary. Make exactly one commit's worth of change. Do not run `define-labels`, which is a manual step after merge.

## WHERE

`src/mcp_coder/config/labels.json` and the seven docs listed below.

## WHAT

**`labels.json` descriptions, each within the 100-character limit:**

| Label | New description |
|---|---|
| `status-84:pr-ci-failed` | `CI auto-fix loop exhausted, hit an LLM failure, or branch moved - needs manual fix` |
| `status-06f-ci:ci-fix-needed` | `CI exhausted fix attempts or branch moved during CI fix, needs manual intervention` |
| `status-17f-ci:code-review-ci-fix-needed` | `CI still failing after automated code review fix attempts, or branch moved during CI fix` |

**Docs, adding the moved-branch cause and its recovery:**

| File | Where |
|---|---|
| `docs/getting-started/label-setup.md` | The `status-84` row |
| `docs/processes-prompts/claude_cheat_sheet.md` | The `status-06f-ci` row (remove "3"), the `status-17f-ci` row, the `status-84` row |
| `docs/processes-prompts/processes/71-pr-follow-up.md` | The flow diagram's `status-84` line and the `status-84` failure-exit row |
| `docs/cli-reference.md` | The `status-17f-ci` sentence in the code review section, and the `fix-ci` section's `status-84` sentence |
| `docs/processes-prompts/github_Issue_Workflow_Matrix.html` | The three label-description cards (same text as `labels.json`) and the `82 → 84` transition line |
| `docs/processes-prompts/processes/05-implementation.md` | The `status-06f-ci` row (remove "3") |
| `docs/processes-prompts/processes/17-automated-code-review.md` | The `status-17f-ci` failure-exit row |

## HOW

- Write "fix attempts" with no number, so the text cannot go stale against `CI_MAX_FIX_ATTEMPTS`.
- Recovery text for a moved branch: check the new commit on the branch, then `fix-ci` sets `status-10:pr-created`, `implement` sets `status-05:plan-ready`, and review sets `status-17:code-review-bot`.
- Say that the issue comment's Category line names the cause, matching the existing wording.

## ALGORITHM

None.

## DATA

Only the `description` values change in `labels.json`.

## TESTS

No new tests. These existing tests must pass:

- `tests/config/test_label_config.py` (the 100-character limit)
- `tests/cli/commands/test_define_labels.py`
- `tests/docs/test_workflow_matrix.py`

Finally, run the full set once:

- `mcp__mcp-tools-py__run_pytest_check` with `extra_args=["-n", "auto"]` and `markers=["git_integration"]`
- `mcp__mcp-workspace__check_file_size` with `max_lines=750`

If the `git_integration` tests in `tests/workflow_steps/test_commit_push_rejected.py` fail, write one line to `pr_info/.blocked.txt` and stop.
