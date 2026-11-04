# Step 5: `fix-conflict` feedback and docs

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_5.md`. Steps 1 to 4 are already committed. Write the tests first, then implement, run the checks listed in the summary, and produce exactly one commit. Implement only this step.

## WHERE

| File | Change |
|---|---|
| `tests/workflows/fix_conflict/test_core.py` | Both paths |
| `src/mcp_coder/workflows/fix_conflict/core.py` | `Next step` in `_fail`, no-verdict comment |
| `docs/cli-reference.md` | `fix-conflict` section |
| #1376's failure comment text, only if #1376 has merged | See "#1376 failure comment" |

## WHAT

```python
def _post_branch_moved_comment(project_dir: Path, branch: str) -> None:
    """Post the settled-state comment for a rebase stopped by a moved branch."""
```

In `_fail`, add one field:

```python
("Next step", BRANCH_MOVED_NEXT_STEP if outcome.reason == "branch_moved" else None),
```

## HOW

- Import `extract_issue_number_from_branch` from `mcp_coder.mcp_workspace_git`. Do not use `resolve_merge_issue_number`, which logs a misleading auto-merge warning.
- Import `post_issue_comment` from `workflow_utils.failure_handling`, next to `build_failure_comment`.
- Import `BRANCH_MOVED_NEXT_STEP` and `BRANCH_MOVED_REASON` from `workflow_steps.rebase`.
- `_fail` cannot be reused for the no-verdict path, because it sets `pr_merge_conflict`.
- Comments are always on in this workflow, so there is no `post_issue_comments` gate.

## ALGORITHM

Helper:

```text
issue_number = extract_issue_number_from_branch(branch)
if issue_number is None: return
body = build_failure_comment(project_dir, title="Fix Conflict", kind="Failed",
    fields=[("Stage", "Mechanical rebase"), ("Reason", BRANCH_MOVED_REASON),
            ("Next step", BRANCH_MOVED_NEXT_STEP)])
post_issue_comment(project_dir, issue_number, body)
```

In `body()`, between the `if verdict:` block and `if state == "unknown":`:

```text
if outcome.reason == "branch_moved":
    _post_branch_moved_comment(project_dir, branch)
```

Being after the verdict return ensures an issue never gets two comments.

## DATA

Labels and exit codes do not change. With no verdict, the run still goes to `pr_created` (exit 0), or to `run_auto_merge` with `auto_merge`.

## Docs

In `docs/cli-reference.md`, `fix-conflict` section, add after the bullet list:

> If the rebase stops because `origin/<branch>` has commits this checkout does not have, the "Fix Conflict Failed" comment gains a next step. On the settled-state path, where no verdict comment is posted, a separate comment gives the same reason and next step. The label and exit code do not change.

## #1376 failure comment

The issue requires whichever of #1376 and #1382 merges second to update #1376's failure comment. Check #1376's state with `mcp__mcp-workspace__github_issue_view`.

- **#1376 has merged:** find its `Next step` text in `src/` (search for the wording about re-running from a local checkout). Reword the warning that re-running can reach the overwrite, because a re-run now stops with `branch_moved`. Keep the instruction to discard the unpushed commit before re-running. Update any test that pins the text, and include the change in this step's commit.
- **#1376 has not merged:** change nothing, and add one line to this step's commit message saying the update falls to #1376.

## Tests

In `tests/workflows/fix_conflict/test_core.py`, use `_patch_all` with `RebaseOutcome("branch_moved", "main", "abc1234")`, and patch `f"{MODULE}.post_issue_comment"` and `_BRANCH_HEAD`:

| Case | Expected |
|---|---|
| State `dirty` | `mock_fail` comment contains `**Next step:** {BRANCH_MOVED_NEXT_STEP}`; `post_issue_comment` not called; exit 1 |
| State `dirty`, other reason (`conflict`) | `mock_fail` comment has no `**Next step:**` |
| State `clean`, no `auto_merge` | One comment on issue 123 with title, Stage, Reason and Next step; `apply_final_label` to `pr_created`; exit 0 |
| State `clean`, `auto_merge=True` | One comment, posted before `run_auto_merge` (order asserted with `attach_mock`) |
| State `clean`, branch without an issue number (`get_current_branch_name` returns `"no-number"`) | No comment; `pr_created` |
| State `clean`, reason `ok` | No comment |
