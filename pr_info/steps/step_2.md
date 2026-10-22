# Step 2 — Count only outstanding feedback in `_check_review_comments()`

## LLM prompt

Read `pr_info/steps/summary.md`, then implement this step (`pr_info/steps/step_2.md`) only.
Step 1 (`is_marked` in `workflows/vscodeclaude/helpers.py`) is already done. Write the tests
first, then the implementation. Run format, pylint, mypy, lint-imports and the fast unit tests
(see CLAUDE.md); all must pass. Produce exactly one commit.

Precondition: `ChangesRequestedData` must have a `submitted_at` key and
`ConversationCommentData` must have `id` and `author_association` keys in the installed
`mcp_workspace.github_operations.pr_types` (check with `get_library_source`). If not, write one
line to `pr_info/.blocked.txt` and stop.

## WHERE

- `src/mcp_coder/mcp_workspace_github.py` — re-export two TypedDicts.
- `src/mcp_coder/workflows/vscodeclaude/checks.py` — `_check_review_comments()`.
- `tests/workflows/vscodeclaude/test_checks_review_comments.py`.

## WHAT

No new functions in `checks.py`. `_check_review_comments()` keeps its signature, return value
and never-raises contract; update its docstring to say "outstanding" feedback.

## HOW

- Shim: add
  `from mcp_workspace.github_operations.pr_types import ChangesRequestedData, ConversationCommentData`
  and both names to `__all__` (under `# PR`).
- `checks.py`: `from .helpers import get_issue_status, is_marked`.

## ALGORITHM (body of the `try` before `if triggered:`)

```
feedback = pr_manager.get_pr_feedback(pr["number"])
if feedback["unresolved_threads"]: triggered = True
else:
    comments = [c for c in feedback["conversation_comments"] if not is_marked(c["body"])]
    timestamps = [r["submitted_at"] for r in feedback["changes_requested"]] + [c["created_at"] for c in comments]
    if not timestamps: triggered = False          # get_issue_events not called
    else: watermark = _review_comments_watermark(get_issue_events(issue, LABELED), ...)
          triggered = watermark is None or any(ts is None or ts > watermark for ts in timestamps)
```

Keep the ❌ comprehension as the single "does this item count?" place — #1257 adds its trust
condition there.

## DATA

Timestamps are ISO strings with `+00:00` (or `None`); string comparison as today.

## Tests

Add typed builders (complete dicts so mypy enforces every key; a missing key would raise
`KeyError`, be swallowed, and make a "no escalation" test pass for the wrong reason):

```python
def _review(submitted_at: str | None, body: str = "please fix") -> ChangesRequestedData
def _comment(created_at: str | None, body: str = "y", comment_id: int = 1) -> ConversationCommentData
```

Use `author="reviewer"`, `author_association="MEMBER"`. Use `+00:00` timestamps in all new and
converted tests. Add a module constant for the watermark events, e.g.
`WATERMARK_EVENTS` = created 2024-01-01, review 2024-03-01, created `2024-06-01T00:00:00+00:00`.

Convert existing tests in `TestCheckReviewComments` that build partial comment/review dicts to
the builders. Leave `TestReviewCommentsWatermark` unchanged.

New / changed cases (`get_issue_events` assertions go inside these tests, not separate ones):

- Reviews, one parametrized test `(submitted_at, events, expected)`:
  before watermark → `False`; after → `True`; no watermark (`events=[]`) → `True`;
  `submitted_at=None` with watermark → `True`. Assert `get_issue_events` called once.
- Unresolved thread with a watermark present → `True`; `get_issue_events` not called.
- No items at all → `False`; `get_issue_events` not called.
- ❌-only comment `"## ❌ Implementation Failed\ndetails"` (after watermark) → `False`;
  `get_issue_events` not called.
- Comment with ❌ only on a later line (after watermark) → `True`.
- ❌ comment + new human comment (after watermark) → `True`.
- Existing comment watermark tests (before → `False`, after → `True`, `created_at=None` →
  `True`, first-ever → `True`) and exception-swallowing tests still pass after conversion.
