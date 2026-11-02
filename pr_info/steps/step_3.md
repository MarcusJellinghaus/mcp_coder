# Step 3 — Marker retry once per conflict stop

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_3.md` only.
> Write the tests first, then the implementation. Run pylint, pytest (fast unit
> set, `-n auto`), mypy and lint-imports until they pass, run `run_format_code`,
> and make exactly one commit.

## WHERE

- `src/mcp_coder/workflows/rebase.py` (conflict loop in `run_rebase_workflow`)
- New test file: `tests/workflows/rebase/test_marker_retry.py` (reuse the fixtures
  in `tests/workflows/rebase/conftest.py`)

## WHAT

```python
_MARKER_RETRY_PROMPT = (
    "Conflict markers remain in: {files}. Edit these files so they contain the "
    "final merged content with no conflict markers. Same tools and rules as before."
)
```

No new function; the retry is a few lines inside the loop.

## HOW

After the conflict prompt, when `unresolved` is non-empty, resume the same session
once with `_MARKER_RETRY_PROMPT` (`step_name=f"conflict_{stop}_retry"`), then
re-check. Still unresolved → the existing abort (exit 1, "conflict markers remain in …").

## ALGORITHM

```
unresolved = [f for f in others if _has_conflict_markers(project_dir, f)]
if unresolved:
    _, session_id = _prompt_in_session(_MARKER_RETRY_PROMPT.format(files=", ".join(unresolved)),
                                       session_id, ..., step_name=f"conflict_{stop}_retry")
    unresolved = [f for f in unresolved if _has_conflict_markers(project_dir, f)]
if unresolved:
    return _end(1, f"conflict markers remain in {', '.join(unresolved)}")
```

## DATA

Unchanged.

## Tests

- Markers fixed by the retry → loop continues, rebase completes (exit 0).
- Markers survive the retry → exit 1, reason names the file.
- The retry prompt is sent at most once per stop (two stops with markers → two
  retries; one stop → one retry), and resumes the existing session id.
- No markers after the first edit → no retry prompt sent.
