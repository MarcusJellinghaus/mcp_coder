# Step 8 — Refactor create-pr: extract `_cleanup_commit_push` and `_resolve_issue_from_pr`

Pure refactor, no behaviour change. Prepares the resume path (step 11) and phase B wiring (step 10).

## LLM prompt
> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_8.md` exactly.
> Add the helper unit tests first, then extract the code. Existing `tests/workflows/create_pr/` tests must pass unchanged.
> Run pylint, pytest (fast unit set, `-n auto`) and mypy; all must pass. Format the code and make exactly one commit.

## WHERE
- `src/mcp_coder/workflows/create_pr/core.py`
- `tests/workflows/create_pr/test_workflow_helpers.py`

## WHAT
```python
def _cleanup_commit_push(project_dir: Path) -> tuple[str, str] | None:
    """Clean up pr_info/ and profiler output, commit, push.

    Returns:
        None on success, else (stage, message) for _handle_create_pr_failure.
    """

def _resolve_issue_from_pr(project_dir: Path, pr_number: int) -> int | None:
    """Closing-references fallback: first issue the PR closes, or None. Never raises."""
```

## ALGORITHM
`_cleanup_commit_push` — the current body steps 3–4, moved verbatim:
```
if not cleanup_repository(pd): return ("cleanup", "Repository cleanup failed")
if not is_working_directory_clean(pd, ignore_files=DEFAULT_IGNORED_BUILD_ARTIFACTS):
    r = commit_all_changes("chore: clean up build artifacts", pd)
    if not r["success"] and "No staged files" not in (r.get("error") or ""): return ("cleanup", f"Failed to commit cleanup: {r['error']}")
push = git_push(pd); if not push["success"]: return ("push", push.get("error", "Unknown push error"))
return None
```
`_resolve_issue_from_pr` — the current fallback block (`get_closing_issue_numbers`, first entry, warning on >1, warning on exception).

## HOW
- In `body()`: replace the inline block with
  ```python
  failure = _cleanup_commit_push(project_dir)
  if failure:
      stage, message = failure
      _handle_create_pr_failure(stage=stage, message=message, ...); return 1
  ```
  and the fallback with
  `if update_issue_labels and cached_issue_number is None: cached_issue_number = _resolve_issue_from_pr(project_dir, pr_number)`.
- Keep the "Step 3/5", "Step 4/5" OUTPUT log lines inside `_cleanup_commit_push`.
- Keep all patched names (`cleanup_repository`, `git_push`, `commit_all_changes`, `is_working_directory_clean`) imported
  in `core.py` so existing test patches still apply.
- Check `core.py` stays under the file-size limit (`check_file_size`); phase B goes to a new module in step 9.

## Tests (write first)
- `_cleanup_commit_push`: success → `None`; cleanup False → `("cleanup", ...)`; commit error → `("cleanup", ...)`;
  commit "No staged files" → continues; push failure → `("push", <error>)`; clean tree → no commit call.
- `_resolve_issue_from_pr`: `[7]` → 7; `[7, 8]` → 7 + warning; `[]` → None; exception → None + warning.

## DATA
See signatures.
