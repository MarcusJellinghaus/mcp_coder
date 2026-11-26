# Step 8: the review's whole-tree round-log flush formats first

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_8.md`.
> Write the tests first, then the code. Run pylint, mypy and the fast pytest
> set (`-n auto`). Format, then make exactly one commit.

## WHERE

- `src/mcp_coder/workflows/review/handoff.py`: `_flush_round_log`
- `tests/workflows/review/test_handoff.py`
- `tests/workflows/review/test_core_formatter_preflight.py`
- `tests/workflows/review/test_core_flush_format.py` (new; core-level checks)

## WHAT

In `_flush_round_log`, the whole-tree branch becomes:

```python
else:
    format_best_effort(project_dir, "round-log commit")
    result = commit_all_changes(message, project_dir)
```

The scoped branch (`only is not None`) is unchanged: it never formats.

## HOW

- Import `format_best_effort` from `mcp_coder.workflow_steps.commit` (next to
  `push_changes`).
- `format_best_effort` never raises, so the broad `except` cannot skip the
  commit after a formatter failure.
- Docstring: the whole-tree flush formats the tree first (best-effort). The
  scoped flush does not, because the formatter cannot be limited to one path,
  and the unresolved-rebase handoff reaches it with a dirty tree.
- This one change covers the dismiss flush and every `_fail` flush in
  `core.py`. The top-of-loop flush, `_route_to_human` and the rounds-cap paths
  (including its CI path) pass `only=` and stay unformatted.
- `test_core_formatter_preflight.py::test_format_code_false_skips_formatter_in_tasks_round`:
  also `monkeypatch.setattr(handoff, "format_best_effort",
  commit.format_best_effort)`, so `format_code = false` is shown to skip
  `run_binding` in the flush too. Update the module docstring.

## ALGORITHM

```
if only is not None: stage_specific_files + commit_paths   # unformatted
else: format_best_effort(project_dir, "round-log commit"); commit_all_changes(message, project_dir)
... unchanged result handling and push
```

## DATA

Unchanged: returns `None`.

## Tests first

`test_handoff.py`:

- Whole-tree flush: `formatter_mocks.format_best_effort` is called with
  `tmp_path` before `commit_all_changes` (recorded order).
- `only=` flush: `formatter_mocks.format_best_effort` is not called.
- Real helper restored (`monkeypatch.setattr(handoff, "format_best_effort",
  commit.format_best_effort)`), `commit.run_formatters` raising
  `FormatterConfigError` (second case: returning False): WARNING logged,
  `commit_all_changes` called, push called.

`test_core_flush_format.py` (uses the review `env` fixture and `_run` from
`tests/workflows/review/conftest.py`; LLM responses as in `test_core.py`):

- Dismiss round 1 (the final flush): `formatter_mocks.format_best_effort` is
  called at least once and `env.commit_all_changes` is called.
- Escalate verdict (`_route_to_human`, scoped): `env.commit_paths` is called,
  `env.commit_all_changes` is not, and the helper is not called.
- A `_fail` path that flushes the whole tree (e.g. `env.commit_changes`
  returning False → `commit-failed`): the helper is called before
  `env.commit_all_changes`.

## Commit

`feat(review): format before the whole-tree round-log flush`
