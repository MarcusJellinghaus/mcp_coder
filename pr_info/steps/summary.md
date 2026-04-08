# Issue #709: compact-diff silently omits pure renames (and other header-only changes)

## Problem

`render_file_diff()` in `compact_diffs.py` returns `""` whenever `rendered_hunks` is empty. Files whose only change is captured in git headers (pure renames, mode changes, binary changes, empty file create/delete) produce a `FileDiff` with populated `headers` but **zero hunks at parse time**, so the entire file is silently dropped from output.

## Architecture / Design Changes

### Rendering fix (`compact_diffs.py`)

The change is a **single conditional branch** in `render_file_diff()`. Today:

```python
if not rendered_hunks:
    return ""
```

After fix — distinguish two empty-hunk cases:

```python
if not rendered_hunks:
    if not file_diff.hunks:
        # No hunks at parse time (rename/copy/mode/binary/empty-file)
        # → emit git's native header lines verbatim
        return "\n".join(file_diff.headers)
    # Had hunks but all collapsed via moved-block suppression → stay hidden
    return ""
```

No new classes, no new functions, no parser changes. The `FileDiff.headers` list already contains everything needed (`similarity index`, `rename from/to`, `copy from/to`, `old mode`/`new mode`, `Binary files ... differ`).

### Rename/copy detection flags (`diffs.py`)

Add `-M` and `-C=90%` to the shared `diff_args` list in `get_branch_diff()` so both ANSI and non-ANSI passes use identical rename/copy detection regardless of user's git config.

### No other production code changes

The parser, hunk renderer, moved-block suppression, and public API signatures are all unchanged.

## Files Modified

| File | Change |
|------|--------|
| `src/mcp_coder/utils/git_operations/compact_diffs.py` | Fix `render_file_diff()` — ~4 lines |
| `src/mcp_coder/utils/git_operations/diffs.py` | Add `-M`, `-C=90%` to `diff_args` — ~2 lines |
| `tests/utils/git_operations/test_compact_diffs.py` | Update 1 existing test, add unit tests for each header-only change type + partial-rename regression guard |
| `tests/utils/git_operations/test_compact_diffs_integration.py` | **New file** — integration tests with real git repos |

## Implementation Steps

| Step | Commit | Description |
|------|--------|-------------|
| 1 | Unit tests + `render_file_diff` fix | TDD: add unit tests for all header-only change types, update existing test, then fix `render_file_diff()` |
| 2 | Integration tests + `-M`/`-C=90%` flags | TDD: add git_integration tests for real renames/copies/mode/binary/empty-file, then add flags to `get_branch_diff()` |
