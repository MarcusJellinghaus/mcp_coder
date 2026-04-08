# Step 1: Unit tests + `render_file_diff` fix

## LLM Prompt

> Read `pr_info/steps/summary.md` for context. Implement Step 1: add unit tests for all header-only change types in `test_compact_diffs.py`, then fix `render_file_diff()` in `compact_diffs.py` to emit headers for files with zero parsed hunks. Follow TDD — write tests first (they will fail), then apply the fix, then verify all checks pass.

## WHERE

- **Modify**: `tests/utils/git_operations/test_compact_diffs.py`
- **Modify**: `src/mcp_coder/utils/git_operations/compact_diffs.py`

## WHAT

### Tests to add/update in `test_compact_diffs.py`

**Update existing test:**

- `test_file_entirely_skipped_when_no_hunks` → rename to `test_file_headers_emitted_when_no_parsed_hunks` and assert that `render_file_diff` returns `"\n".join(file_diff.headers)` instead of `""`.

**New tests in `TestRenderFileDiff`:**

1. `test_pure_rename_headers_emitted` — `FileDiff` with `similarity index 100%`, `rename from`, `rename to` headers, empty hunks → output contains all header lines.
2. `test_partial_rename_emits_headers_and_hunks` — `FileDiff` with rename headers AND hunks → output contains both rename headers and hunk content. (Regression guard — this already works today.)
3. `test_pure_copy_headers_emitted` — `FileDiff` with `similarity index 100%`, `copy from`, `copy to` headers, empty hunks → output contains all header lines.
4. `test_partial_copy_emits_headers_and_hunks` — `FileDiff` with copy headers AND hunks → output contains both.
5. `test_mode_change_headers_emitted` — `FileDiff` with `old mode`/`new mode` headers, empty hunks → output contains mode lines.
6. `test_binary_change_headers_emitted` — `FileDiff` with `Binary files ... differ` header, empty hunks → output contains binary header.
7. `test_empty_file_creation_headers_emitted` — `FileDiff` with `new file mode 100644` header, empty hunks → output contains header.
8. `test_empty_file_deletion_headers_emitted` — `FileDiff` with `deleted file mode 100644` header, empty hunks → output contains header.
9. `test_moved_suppression_still_hides_collapsed_hunks` — `FileDiff` with hunks that ALL collapse to `""` via moved-block suppression → `render_file_diff` returns `""`. (Regression guard for existing behaviour.)

**New test in `TestRenderCompactDiff`:**

10. `test_pure_rename_in_compact_diff` — full `render_compact_diff` with a pure-rename diff string → output is non-empty and contains `rename from`/`rename to`.

### Production fix in `compact_diffs.py`

Single change in `render_file_diff()`:

```python
# BEFORE:
if not rendered_hunks:
    return ""

# AFTER:
if not rendered_hunks:
    if not file_diff.hunks:
        return "\n".join(file_diff.headers)
    return ""
```

## HOW

- Tests use hand-crafted `FileDiff` / `Hunk` objects and raw diff strings — no git repos, no I/O.
- Import `FileDiff`, `Hunk`, `render_file_diff`, `render_compact_diff` from `mcp_coder.utils.git_operations.compact_diffs`.

## ALGORITHM (fix)

```
function render_file_diff(file_diff, moved_lines, ...):
    rendered_hunks = [render_hunk(h, ...) for h in file_diff.hunks if render_hunk(h, ...) != ""]
    if rendered_hunks is empty:
        if file_diff.hunks is empty:        # ← NEW: no hunks at parse time
            return "\n".join(file_diff.headers)  # emit git's native headers
        return ""                            # existing: all hunks collapsed → suppress
    return "\n".join(file_diff.headers + rendered_hunks)
```

## DATA

All test inputs are `FileDiff` objects with various `.headers` lists and empty `.hunks` lists. Expected outputs are the joined header strings. Example:

```python
# Pure rename input
FileDiff(
    headers=[
        "diff --git a/old.py b/new.py",
        "similarity index 100%",
        "rename from old.py",
        "rename to new.py",
    ],
    hunks=[],
)
# Expected output: "diff --git a/old.py b/new.py\nsimilarity index 100%\nrename from old.py\nrename to new.py"
```

## Commit

```
fix: emit git headers for pure renames and other header-only changes (#709)

render_file_diff() now distinguishes "no hunks at parse time" (emit
headers verbatim) from "all hunks collapsed via moved-block suppression"
(stay hidden). Fixes compact-diff silently dropping pure renames, mode
changes, binary changes, and empty file create/delete.
```
