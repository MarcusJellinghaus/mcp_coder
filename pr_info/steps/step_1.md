# Step 1 — Shim re-exports + status-note trust filter

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_1.md`
> only. TDD: update/add the tests first, then the code. Run pylint, mypy and
> the fast unit tests (see CLAUDE.md) until they pass, run
> `run_format_code`, and make exactly one commit.

## Precondition

`mcp_workspace.github_operations` must export `is_trusted_author` and
`get_trusted_commenters`, and `mcp_workspace.github_operations.pr_types` must
define `ReviewThreadData` (check with `get_library_source`). If not, write
one line to `pr_info/.blocked.txt` and stop.

## WHERE

- `src/mcp_coder/mcp_workspace_github.py`
- `src/mcp_coder/workflows/vscodeclaude/workspace.py` (`_find_marked_comment`,
  `_fetch_marked_comment`, ~lines 626-654)
- `tests/workflows/vscodeclaude/test_status_note.py`

## WHAT

Shim:
- Add `get_trusted_commenters`, `is_trusted_author` to the existing
  `from mcp_workspace.github_operations import (...)` block.
- Add `ReviewThreadData` to the existing `pr_types` import.
- Add all three to `__all__` (trust helpers under a `# Trust` comment,
  `ReviewThreadData` under `# PR`).

workspace.py:

```python
def _find_marked_comment(
    comments: list[CommentData],
    trusted: frozenset[str],
    *,
    marker: str = "❌",
    window: int = 3,
) -> str | None:
    """Return the body of the most recent trusted ❌-marked comment, or None."""

def _fetch_marked_comment(project_dir: Path, issue_number: int) -> str | None:
    # unchanged signature; inside try:
    #   comments = IssueManager(project_dir=project_dir).get_comments(issue_number)
    #   return _find_marked_comment(comments, get_trusted_commenters())
```

## HOW

- Import `get_trusted_commenters`, `is_trusted_author` from
  `...mcp_workspace_github` in `workspace.py` (extend the existing import).
- `get_trusted_commenters` is called inside the existing `try`, so failures
  stay best-effort.

## ALGORITHM

```
trusted_comments = [c for c in comments
                    if is_trusted_author(c["user"], c["author_association"], trusted)]
for c in reversed(trusted_comments[-window:]):
    if is_marked(c["body"], marker): return c["body"]
return None
```

## DATA

Return value unchanged: comment body `str` or `None`.

## Tests (`test_status_note.py`)

- `_comment(body, user="owner", author_association="OWNER")` — trusted by
  default (was `None`/`None`, which would now be untrusted).
- Autouse fixture: `monkeypatch.setattr(
  "mcp_coder.workflows.vscodeclaude.workspace.get_trusted_commenters",
  lambda: frozenset())` — tests never read the developer's config.
- Existing `_find_marked_comment(comments)` calls → `_find_marked_comment(comments, frozenset())`.
- New in `TestFindMarkedComment`:
  - untrusted ❌ comment (`user="stranger", author_association="NONE"`) → `None`;
  - OWNER ❌ comment → its body;
  - OWNER ❌ comment followed by 3 untrusted comments → OWNER body still found.
- Existing `TestCreateStatusFileNote` tests keep passing unchanged (they
  exercise `_fetch_marked_comment` via `create_status_file`).
