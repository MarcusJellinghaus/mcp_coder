# Step 1 — Shared failure comment builder

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement **Step 1** exactly as described in
> `pr_info/steps/step_1.md`. Write the tests first, then the implementation. Do not
> migrate any workflow yet. Run pylint, pytest (fast unit set, `-n auto`) and mypy;
> all must pass. Produce one commit.

## WHERE

- `src/mcp_coder/workflow_utils/failure_handling.py` (add, nothing removed)
- `tests/workflow_utils/test_failure_comment.py` (new)

## WHAT

```python
SHORT_SHA_LENGTH = 7

CommentField = tuple[str, str | None]

FIELD_ORDER: tuple[str, ...] = (
    "Category", "Stage", "Error", "Reason", "Branch", "Base", "PR",
    "Likely conflicting files", "Uncommitted files", "Progress", "Verdict",
    "Next step", "Elapsed", "Build",
)

def _branch_head(project_dir: Path) -> tuple[str | None, str | None]:
    """Return (branch name, 7-char HEAD sha). Never raises.

    (None, None) when the branch lookup fails or yields no branch;
    (branch, None) when only the SHA lookup fails.
    """

def build_failure_comment(
    project_dir: Path,
    *,
    title: str,                        # e.g. "Implementation", "Plan Review"
    kind: str,                         # "Failed" | "Handed Off" | "Crashed"
    fields: Sequence[CommentField] = (),
    elapsed: float | None = None,
    extra_section: str | None = None,
) -> str:
```

## HOW

- `_branch_head` uses the already-imported `get_current_branch_name` and
  `get_latest_commit_sha` (add to the existing `mcp_coder.mcp_workspace_git`
  import), each behind its own `try/except Exception` (pylint
  `broad-exception-caught` disable comment, as elsewhere in the file):
  branch guard fails / no branch → `(None, None)`; SHA guard fails or returns
  nothing → `(branch, None)`; else `(branch, sha[:SHORT_SHA_LENGTH])`.
- `build_failure_comment` reads `os.environ.get("BUILD_URL")` itself
  (`import os`).
- `format_elapsed_time` (existing) formats `elapsed`.

## ALGORITHM

```
branch, sha = _branch_head(project_dir)
branch_value = None if not branch else (f"{branch} @ {sha}" if sha else branch)
all_fields = [*fields, ("Branch", branch_value),
              ("Elapsed", format_elapsed_time(elapsed) if elapsed is not None else None),
              ("Build", os.environ.get("BUILD_URL") or None)]
kept = sorted((f for f in all_fields if f[1] is not None), key=_order_key)  # stable
lines = [f"## ❌ {title} {kind}", *(f"**{label}:** {value}" for label, value in kept)]
if extra_section: lines += ["", extra_section]; return "\n".join(lines)
```

`_order_key(field)`: `FIELD_ORDER.index(label)` when known, else
`FIELD_ORDER.index("Next step") - 0.5` (unknown labels land just before
Next step; stable sort keeps caller order among them).

## DATA

- Returns the comment string. First line always contains `❌`.
- `_branch_head` → `("feat-x", "abc1234")`; `("feat-x", None)` when only the
  SHA lookup fails; `(None, None)` when the branch lookup fails.

## Tests (`tests/workflow_utils/test_failure_comment.py`)

Patch `mcp_coder.workflow_utils.failure_handling._branch_head`; for `_branch_head`
itself patch `get_current_branch_name` / `get_latest_commit_sha` in that module.

1. Heading: `build_failure_comment(..., title="CI Fix", kind="Crashed")` first line is `## ❌ CI Fix Crashed`.
2. **Parametrised order test**: pass every `FIELD_ORDER` label (except Branch / Elapsed / Build) in reversed order plus `elapsed` and `BUILD_URL`; assert rendered labels appear exactly in `FIELD_ORDER` order. One parametrisation per label asserting its index relative to its neighbours is fine too — keep it a single `@pytest.mark.parametrize` test.
3. `None` values are skipped.
4. Unknown label (`"Foo"`) renders after `Verdict`, before `Next step`.
5. Branch line: `("feat", "abc1234")` → `**Branch:** feat @ abc1234`; `("feat", None)` → `**Branch:** feat`; `(None, None)` → no Branch line.
6. `BUILD_URL` set → `**Build:** <url>` last field; cleared (`patch.dict(os.environ, {}, clear=True)`) → no Build line.
7. `extra_section` is appended after one blank line.
8. `_branch_head` returns `(None, None)` when `get_current_branch_name` raises; `("feat", None)` when `get_latest_commit_sha` raises; truncates sha to 7 chars.
