# Step 1 — Shared ❌ helper `is_marked()`

## LLM prompt

Read `pr_info/steps/summary.md`, then implement this step (`pr_info/steps/step_1.md`) only.
Write the tests first, then the implementation. Run format, pylint, mypy and the fast unit
tests (see CLAUDE.md); all must pass. Produce exactly one commit.

## WHERE

- `src/mcp_coder/workflows/vscodeclaude/helpers.py` — add `is_marked`, add to `__all__`.
- `src/mcp_coder/workflows/vscodeclaude/workspace.py` — `_find_marked_comment` (~line 634).
- `tests/workflows/vscodeclaude/test_helpers.py` — new test class.

## WHAT

```python
def is_marked(body: str, marker: str = "❌") -> bool:
    """Return True if the first line of ``body`` contains ``marker``.

    mcp-coder's automated notes carry the marker on their first line.
    """
```

## HOW

- `workspace.py` already does `from .helpers import load_to_be_deleted`; extend that import
  with `is_marked`.
- `_find_marked_comment` keeps its signature and return value; its loop body becomes
  `if is_marked(comment["body"], marker): return comment["body"]`.

## ALGORITHM

```
if not body: return False
return marker in body.splitlines()[0]
```

## DATA

`bool`. A body starting with a newline has an empty first line → `False` (same as today's
`_find_marked_comment`).

## Tests (`test_helpers.py`, new `TestIsMarked`)

One `pytest.mark.parametrize` test, `(body, expected)`:

- `""` → `False`
- `"## ❌ Implementation Failed\ndetails"` → `True` (marker inside a heading)
- `"❌ handoff"` → `True`
- `"Implementation Failed\n❌ details"` → `False` (marker only on a later line)
- `"\n## ❌ Implementation Failed"` → `False` (blank first line)
- `"plain comment"` → `False`

Existing `TestFindMarkedComment` in `tests/workflows/vscodeclaude/test_status_note.py` must
pass unchanged — it shows `_find_marked_comment` behaves as before. Do not edit it.
