# Step 2 — Safety net: no "committed successfully: None"

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_2.md` exactly.
> Step 1 is already committed. Write the test first (TDD), then the implementation.
> Run pylint, mypy and the fast pytest suite, all with `-n auto` and the
> non-integration markers from CLAUDE.md, then run the formatter. Make exactly one
> commit for this step. Do not edit `pr_info/TASK_TRACKER.md`.

## Precondition

`_tree_is_clean` must exist in `src/mcp_coder/workflow_steps/commit.py`, and
`tests/workflow_steps/test_commit_clean_tree.py` must exist. This is the output of
Step 1. If either is missing, write one line to `pr_info/.blocked.txt` and stop.

## WHERE

- `src/mcp_coder/workflow_steps/commit.py` (modify `commit_changes` only)
- `tests/workflow_steps/test_commit_clean_tree.py` (add one test)

## WHAT

There are no new functions. In `commit_changes`, replace the success log after the
`if not commit_result["success"]:` block.

## HOW

Make one `if`/`else` around the log call. Both branches fall through to the existing
`return True`. Keep the first-line extraction in the `else` branch only.

## ALGORITHM

```
if commit_result["commit_hash"] is None:
    logger.info("No changes to commit")
else:
    first_line = <existing first-line extraction>
    logger.info(f"Changes committed successfully: {hash} - {first_line}")
return True
```

## DATA

`commit_all_changes` returns `{"success": bool, "commit_hash": str | None, "error": str | None}`.
The return value of `commit_changes` does not change: `True`.

## Test

Add to `tests/workflow_steps/test_commit_clean_tree.py`:

`test_none_commit_hash_logs_no_changes`

- Status: dirty, via `_status()`.
- Generation returns `(True, "feat: m", None)`.
- `commit_all_changes` returns `{"success": True, "commit_hash": None, "error": None}`.
- Use `caplog.set_level(logging.INFO)`.
- Expect:
  - the result is `True`;
  - the text `No changes to commit` is in caplog;
  - the text `committed successfully` is not in caplog.

## Commit message

`fix(commit): log "No changes to commit" when commit returns no hash`
