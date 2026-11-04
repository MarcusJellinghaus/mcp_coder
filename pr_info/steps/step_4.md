# Step 4: `create-pr` post-creation comment

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_4.md`. Steps 1 to 3 are already committed. Write the tests first, then implement, run the checks listed in the summary, and produce exactly one commit. Implement only this step.

## WHERE

| File | Change |
|---|---|
| `tests/workflows/create_pr/test_post_creation.py` | Comment tests |
| `tests/workflows/create_pr/test_workflow_labels.py` | Pinned call arguments |
| `src/mcp_coder/workflows/create_pr/post_creation.py` | Comment on `branch_moved` |

`create_pr/core.py` is close to the file-size limit and does not change.

## WHAT

```python
def _check_mergeability_and_ci(
    project_dir: Path,
    branch: str,
    head_before: str | None,
    *,
    issue_number: int | None,
    post_issue_comments: bool,
) -> tuple[str, str | None]: ...
```

The 2-tuple return stays. Document both new arguments in the docstring.

Also update the `run_post_creation` docstring, whose `post_issue_comments` entry names only the auto-merge failure comment. It now gates both that comment and the `branch_moved` comment.

## HOW

- `run_post_creation` passes its own `issue_number` and `post_issue_comments`.
- Import `build_failure_comment` and `post_issue_comment` from `workflow_utils.failure_handling`.
- Import `BRANCH_MOVED_NEXT_STEP` and `BRANCH_MOVED_REASON` from `workflow_steps.rebase`.
- `post_issue_comment` logs a warning on failure and never raises, so a failed post cannot change the outcome.

## ALGORITHM

After the existing `push_failed` reset, before the second `_poll_mergeable_state`:

```text
if outcome.reason == "branch_moved" and post_issue_comments and issue_number is not None:
    body = build_failure_comment(
        project_dir, title="PR Creation", kind="Failed",
        fields=[("Stage", "Post-creation rebase"), ("Reason", BRANCH_MOVED_REASON),
                ("Next step", BRANCH_MOVED_NEXT_STEP)])
    post_issue_comment(project_dir, issue_number, body)
```

## DATA

The comment body starts with `## ❌ PR Creation Failed`, and carries `**Stage:**`, `**Reason:**` and `**Next step:**`. Labels and exit codes do not change.

## Tests

### `tests/workflows/create_pr/test_post_creation.py`

Add tests with `mocks.poll.return_value = "dirty"` and `mocks.rebase.return_value = RebaseOutcome("branch_moved", "main", "abc1234")`, patching `f"{_MODULE}.post_issue_comment"`:

| Case | Expected |
|---|---|
| `post_issue_comments=True`, issue set | One comment with the title, Stage, Reason and Next step; label handed on is `pr_merge_conflict` |
| `post_issue_comments=False` | No comment; same label |
| `issue_number=None` | No comment; same label |
| Reason other than `branch_moved` (`push_failed`, `conflict`) | No comment |
| Poll settles after the rebase: `mocks.poll.side_effect = ["dirty", "clean"]` | One comment; label `pr_created` |

Add one test that does not patch `post_issue_comment`, and instead patches `mcp_coder.workflow_utils.failure_handling.IssueManager` with `side_effect=RuntimeError("boom")`. Assert that the label handed on and the return value are unchanged.

### `tests/workflows/create_pr/test_workflow_labels.py`

In `test_final_label_from_post_creation`:

```python
mock_post_creation.assert_called_once_with(
    Path("/test"),
    "feature-branch",
    "abc123",
    issue_number=123,
    post_issue_comments=False,
)
```

`post_issue_comments` defaults to `False` in `run_create_pr_workflow`. Keep the `(label, None)` return shape. Update any other test in this file that pins these call arguments.
