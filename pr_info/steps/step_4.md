# Step 4 — `finish_auto_merge` + best-effort `post_issue_comment`

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement **only** `pr_info/steps/step_4.md`.
> Follow TDD: write the tests first, then the code. Not called by any command yet.
> Run format, pylint, mypy, lint-imports, pytest (fast unit set, `-n auto`) and make them
> pass. Produce exactly one commit.

## WHERE

- `src/mcp_coder/workflow_utils/failure_handling.py` — add `post_issue_comment`
- `src/mcp_coder/workflow_steps/merge.py` — add `finish_auto_merge`
- Tests: the existing failure-handling test module under `tests/workflow_utils/`
  (find it by searching for `handle_workflow_failure`), new
  `tests/workflow_steps/test_merge_finish.py`

## WHAT

```python
# failure_handling.py
def post_issue_comment(project_dir: Path, issue_number: int, body: str) -> None:
    """Post a comment on the issue. Best-effort: logs a warning on failure, never raises."""

# merge.py
_EXIT_1_LABELS = frozenset({"pr_merge_conflict", "merge_failed"})

def finish_auto_merge(
    project_dir: Path,
    outcome: MergeOutcome,
    *,
    from_label_id: str,
    issue_number: int | None,
    update_issue_labels: bool,
    post_issue_comments: bool,
) -> int: ...
```

`handle_workflow_failure` is left unchanged.

## ALGORITHM — `finish_auto_merge`

```
rc = 0
if update_issue_labels:
    if issue_number is None: logger.warning("Skipping label update: branch not linked to an issue")
    else: rc = apply_final_label(project_dir, from_label_id, outcome.label_id, issue_number)
if outcome.comment_fields and post_issue_comments and issue_number is not None:
    body = build_failure_comment(project_dir, title="Auto-merge", kind="Failed", fields=outcome.comment_fields)
    post_issue_comment(project_dir, issue_number, body)
logger.log(OUTPUT, "Auto-merge outcome: %s", outcome.label_id)
return rc or (1 if outcome.label_id in _EXIT_1_LABELS else 0)
```

`post_issue_comment`: `try: IssueManager(project_dir).add_comment(issue_number, body)`
`except Exception as exc: logger.warning("Failed to post comment: %s", exc)` (broad catch with
pylint disable comment, matching the module).

## HOW

- `merge.py` imports `apply_final_label` from `workflow_utils.label_transitions`,
  `build_failure_comment`, `post_issue_comment` from `workflow_utils.failure_handling`,
  `OUTPUT` from `mcp_coder.utils.log_utils`.
- The label is applied **before** the comment is posted.

## DATA

Exit code: `merged` / `pr_created` / `failing_ci` → 0; `pr_merge_conflict` / `merge_failed` → 1;
label write failed → 1.

## Tests

- `post_issue_comment`: success calls `add_comment`; `IssueManager` or `add_comment` raising →
  no exception, warning logged.
- `finish_auto_merge` (patch `apply_final_label`, `post_issue_comment`, `build_failure_comment`
  at `mcp_coder.workflow_steps.merge.*`), parametrized over label ids → exit codes;
  `apply_final_label` called with `issue_number=` keyword/positional as passed; label write
  returning 1 → exit 1 even for `merged`; `update_issue_labels=False` → no label call, exit
  code by outcome; `issue_number=None` → no label, no comment, exit code by outcome;
  comment posted only when fields non-empty and `post_issue_comments=True`; label called
  before comment (call order).

## Done when

Both functions tested; nothing calls them yet.
