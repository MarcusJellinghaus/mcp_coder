# Step 2: Pure building blocks — scan-rule helper + status-file note template

See [summary.md](./summary.md) for full context. This step adds two
pure, independently-testable pieces used by Step 3. Neither is wired into
`create_status_file` yet, and neither performs any I/O — no `IssueManager`
is touched in this step.

## WHERE

- `src/mcp_coder/workflows/vscodeclaude/templates.py` — new module-level
  constant `STATUS_NOTE_TEMPLATE`.
- `src/mcp_coder/workflows/vscodeclaude/workspace.py` — new private
  function `_find_marked_comment`.
- `tests/workflows/vscodeclaude/test_templates.py` — test for the new
  constant's formatting.
- `tests/workflows/vscodeclaude/test_workspace.py` — new test class for
  `_find_marked_comment`.

## WHAT

```python
# templates.py
STATUS_NOTE_TEMPLATE = (
    "❌ Last automated note:\n"
    "--------------------------------------------------------------------------\n"
    "{comment_body}\n"
    "--------------------------------------------------------------------------\n"
)
```

Dash-line length matches the `=`-line length already used by
`STATUS_FILE_TEMPLATE` in the same file (copy that line's length, don't
guess it).

```python
# workspace.py
from ...mcp_workspace_github import CommentData  # add to existing import block

def _find_marked_comment(
    comments: list[CommentData],
    *,
    marker: str = "❌",
    window: int = 3,
) -> str | None:
    """Return the body of the most recent ❌-marked comment, or None."""
```

## HOW

- `_find_marked_comment` is a plain function, no decorators, no I/O. It is
  not exported in any `__all__` — it stays private to `workspace.py`
  (Step 3 calls it from the same module).
- `STATUS_NOTE_TEMPLATE` follows the exact pattern already used for
  `STATUS_FILE_TEMPLATE` / `INTERVENTION_LINE` in the same file: a plain
  `.format()`-style string constant, no f-string, no new templating
  mechanism.

## ALGORITHM

```
take the last `window` comments (oldest-first list, so this is comments[-window:])
walk that slice from most recent to oldest (reversed)
for each comment: take its body's first line (empty string if body has no lines)
if marker is found anywhere in that first line: return the comment's full body
if nothing in the window matches: return None
```

## DATA

- Input: `list[CommentData]` (the `TypedDict` already defined in
  `mcp_workspace_github` / re-exported from `mcp_coder.mcp_workspace_github`;
  has a `"body": str` key, among others — only `"body"` is read).
- Output: `str | None` — the full, untruncated comment body, or `None`.

## Tests (write first, then implement)

`tests/workflows/vscodeclaude/test_workspace.py`, new class
`TestFindMarkedComment`, built from plain `CommentData`-shaped dicts (no
mocking):

- Most recent of the last 3 is marked → its body is returned.
- Most recent is unmarked (e.g. a later human reply) but an older one within
  the window is marked → the marked one's body is returned (confirms
  "scan backwards past unmarked comments").
- None of the last 3 are marked → `None`.
- Fewer than 3 comments exist (e.g. only 1) → still scans correctly, no
  index error.
- Marker appears only on the comment's *second* line, not its first → not
  matched (confirms "first line", not "anywhere in body").
- A comment with an empty `"body"` string in the window → no crash,
  treated as unmarked.

`tests/workflows/vscodeclaude/test_templates.py`, one test asserting
`STATUS_NOTE_TEMPLATE.format(comment_body="## ❌ Implementation Failed\n...")`
contains both the literal header `"❌ Last automated note:"` and the
substituted body text.

## Commit

One commit: both test files + both production additions, `run_pytest_check`
/ `run_pylint_check` / `run_mypy_check` all passing.

## LLM prompt for this step

> Implement Step 2 of `pr_info/steps/summary.md` (see that file for full
> context) exactly as specified in `pr_info/steps/step_2.md`: add the pure
> `_find_marked_comment` helper to
> `src/mcp_coder/workflows/vscodeclaude/workspace.py` and the
> `STATUS_NOTE_TEMPLATE` constant to
> `src/mcp_coder/workflows/vscodeclaude/templates.py`. Write the listed
> tests first in `tests/workflows/vscodeclaude/test_workspace.py` and
> `tests/workflows/vscodeclaude/test_templates.py`, confirm they fail, then
> implement until green. Do not call `_find_marked_comment` from
> `create_status_file` yet — that is Step 3. Do not touch `IssueManager` or
> any network code in this step. Run pytest, pylint and mypy; all must
> pass. Produce exactly one commit for this step.
