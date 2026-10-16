# Step 2 — `EventData` shim export + pure watermark helper

See `pr_info/steps/summary.md` for full context. This step adds the one
missing shim re-export needed for typing, then the pure, GitHub-free watermark
algorithm as its own unit-tested function.

## LLM prompt

> Read `pr_info/steps/summary.md` for context, then implement
> `pr_info/steps/step_2.md` exactly as written. Follow TDD: write the unit
> tests for `_review_comments_watermark()` first (they must fail against a
> stub or missing function), then implement. Produce exactly one commit for
> this step.

## WHERE

- `src/mcp_coder/mcp_workspace_github.py` — add `EventData` to the existing
  `from mcp_workspace.github_operations.issues import (...)` block and to
  `__all__`.
- `src/mcp_coder/workflows/vscodeclaude/session_launch.py` — add
  `_review_comments_watermark()`.
- `tests/workflows/vscodeclaude/test_session_launch_review_comments.py` — new
  file, unit tests for the helper only (step 3 extends this same file).

## Precondition check

Before writing any code, confirm `EventData` is importable:
`mcp_workspace.github_operations.issues.EventData` must exist in the installed
`mcp_workspace` package (it backs `IssueManager.get_issue_events()`, already
re-exported via `IssueEventType` in the same shim file). If the import fails,
write one line to `pr_info/.blocked.txt` and stop.

## WHAT

```python
def _review_comments_watermark(
    events: list[EventData],
    review_label_name: str,
    created_label_name: str,
) -> str | None:
    """Derive the comment-watermark timestamp from an issue's label history."""
```

## HOW

- Shim: add `EventData` next to `IssueEventType` in the existing
  `from mcp_workspace.github_operations.issues import (...)` import and in
  `__all__` (alphabetical, same style as the surrounding entries).
- `session_launch.py`: import `EventData` from `...mcp_workspace_github`
  alongside the existing imports from that module. `_review_comments_watermark`
  is a private module-level function, no decorators, no I/O — pure list
  processing only. Add it near the top of the "check" functions, before
  `_check_merge_conflict`.

## ALGORITHM

```
last_review_idx = last i where events[i].event == "labeled"
                          and events[i].label == review_label_name
if last_review_idx is None: return None          # first-ever arrival
for event in events[last_review_idx + 1:]:
    if event.event == "labeled" and event.label == created_label_name:
        return event.created_at
return None                                       # no status-10 relabel followed
```

## DATA

- Input: `events` — the full list returned by
  `issue_manager.get_issue_events(issue_number, IssueEventType.LABELED)`
  (already filtered to `LABELED` events by that call, so every item's
  `event` field reads `"labeled"` — no further filtering needed by this
  function beyond matching on `label`).
- `review_label_name` / `created_label_name` — the actual GitHub label text
  for `status-91:pr-review-comments` / `status-10:pr-created` (not the
  internal_ids), resolved by the caller added in step 3.
- Returns: an ISO-8601 timestamp string (the watermark), or `None` meaning "no
  filter — every existing comment counts." Both the first-arrival case and the
  degenerate "no status-10 relabel found" case return `None`; the caller
  (step 3) does not need to distinguish them.

## Tests (write first)

In the new test file, cover with synthetic `EventData` lists (plain dicts
matching the `TypedDict` shape — no mocking of `IssueManager` or GitHub):

- No `status-91` event anywhere → `None`.
- One `status-91` event, followed later by one `status-10` event → that
  event's `created_at`.
- Two `status-91`/`status-10` relabel cycles → uses the **last** `status-91`
  event, not the first.
- `status-91` event with no subsequent `status-10` event in the list → `None`.
- Empty `events` list → `None`.

## Quality checks

Run `mcp__mcp-tools-py__run_pytest_check` (fast unit markers, scoped to the new
test file while iterating), `mcp__mcp-tools-py__run_pylint_check`,
`mcp__mcp-tools-py__run_mypy_check`. All must pass before committing.
