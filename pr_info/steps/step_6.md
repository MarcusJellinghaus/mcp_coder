# Step 6: task tracker preparation formats and commits the formatter's changes

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_6.md`.
> Write the tests first, then the code. Run pylint, mypy and the fast pytest
> set (`-n auto`). Format, then make exactly one commit.

## WHERE

- `src/mcp_coder/workflows/implement/task_tracker_prep.py`: `prepare_task_tracker`
- `tests/workflows/implement/test_task_tracker_format.py` (new)
- `tests/workflows/implement/test_task_tracker_prep.py`: `test_success`
- `tests/workflows/implement/test_task_tracker_repair.py`:
  `test_populates_and_commits_only_tracker` (must still pass; adapt only if needed)

## WHAT

No new public functions. `prepare_task_tracker` gains, between
`_populate`/`_repair` and `commit_paths`:

```python
format_best_effort(project_dir, "task tracker commit")
formatted = [
    f for f in _other_changed_files(project_dir) if not f.startswith(".mcp-coder/")
]
commit_result = commit_paths(
    "TASK_TRACKER.md with implementation steps and PR tasks updated",
    [tracker, *(project_dir / f for f in formatted)],
    project_dir,
)
```

## HOW

- Import `format_best_effort` from `mcp_coder.workflow_steps.commit` and
  `reset_hard` from `mcp_coder.mcp_workspace_git`.
- Why it is correct: after each LLM call, `_llm_rounds` already refuses any
  change other than the tracker and `DEFAULT_IGNORED_BUILD_ARTIFACTS`. So
  every other path `_other_changed_files` reports after the formatter came from
  the formatter. `.mcp-coder/` paths are dropped explicitly. Put this in a
  short code comment.
- Initialise `formatted: list[str] = []` before the `try`.
- `finally`: keep `tracker.write_bytes(original)` when `not done`. When
  `not done and formatted`, also call `reset_hard(project_dir, "HEAD")`. The
  tree was clean before the step, so this restores the formatter's files and
  clears a half-staged failed commit. A failed reset logs an ERROR with
  `result["error"]`, and the step then fails dirty.

## ALGORITHM

```
formatted = []
try:
    _repair(...) or _populate(...)
    format_best_effort(project_dir, "task tracker commit")
    formatted = [non-.mcp-coder paths from _other_changed_files(project_dir)]
    commit_paths(msg, [tracker, *formatted paths], project_dir) -> raise TrackerPrepError on failure
    done = True
finally:
    if not done: tracker.write_bytes(original); if formatted: reset_hard(project_dir, "HEAD") (log error if it fails)
```

## DATA

Unchanged: returns `None`, raises `TrackerPrepError` on failure.

## Tests first

`test_task_tracker_format.py`: reuse the mocking style of
`test_task_tracker_prep.py`. Patch `prompt_llm`, `store_session`,
`get_full_status`, `commit_paths` and `reset_hard` in
`mcp_coder.workflows.implement.task_tracker_prep`, and give `get_full_status`
a `side_effect` list:

- **Format before commit:** `formatter_mocks.format_best_effort` is called with
  `tmp_path` before `commit_paths` (recorded order).
- **The formatter's file is committed, `.mcp-coder/` is not.** The guard status
  is the tracker only. The post-format status is tracker modified, `src/a.py`
  modified, and `.mcp-coder/implement_sessions/s.json` untracked. Then
  `commit_paths` paths == `[tracker, tmp_path / "src/a.py"]`.
- **Formatter raises or returns False (real helper):** put back the real
  `format_best_effort` (`monkeypatch.setattr(prep, "format_best_effort",
  commit.format_best_effort)`), make `commit.run_formatters` raise
  `FormatterConfigError` (second case: return False). Expect a WARNING,
  `commit_paths` called, no raise.
- **Commit fails after the formatter changed a file:** `commit_paths` returns
  `{"success": False, "error": "x"}`, so `TrackerPrepError` is raised,
  `reset_hard` is called once with `(tmp_path, "HEAD")`, and the tracker bytes
  equal the original.
- **Commit fails, formatter changed nothing:** `reset_hard` is not called; the
  tracker is restored.

Adapt `test_task_tracker_prep.py::test_success`:
`mocks.get_full_status.call_count == 2` (guard + post-format), both calls with
`tmp_path`.

## Commit

`feat(implement): format the task tracker commit and include the formatter's changes`
