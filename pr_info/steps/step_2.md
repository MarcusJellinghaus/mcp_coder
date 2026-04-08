# Step 2: Integration tests + `-M`/`-C=90%` flags

## LLM Prompt

> Read `pr_info/steps/summary.md` for context. Implement Step 2: add git_integration tests in a new file `test_compact_diffs_integration.py` that exercise the full pipeline with real git repos, then add `-M` and `-C=90%` flags to `get_branch_diff()` in `diffs.py`. Follow TDD — write tests first (they will fail without the flags for rename/copy detection), then add the flags, then verify all checks pass.

## WHERE

- **Create**: `tests/utils/git_operations/test_compact_diffs_integration.py`
- **Modify**: `src/mcp_coder/utils/git_operations/diffs.py`

## WHAT

### Integration tests in `test_compact_diffs_integration.py`

All tests marked `@pytest.mark.git_integration`, using the existing `git_repo` fixture from `conftest.py`.

**Class `TestCompactDiffRenames`:**

1. `test_pure_rename_appears_in_compact_diff` — rename a file with no content change on a feature branch, run `get_compact_diff`, assert output contains `rename from` and `rename to`.
2. `test_partial_rename_shows_headers_and_hunks` — rename a file AND change some content, run `get_compact_diff`, assert output contains `rename from`/`rename to` AND the content diff.

**Class `TestCompactDiffCopies`:**

3. `test_pure_copy_appears_in_compact_diff` — copy a file (use `git diff -C=90%` detection by creating a near-identical file), run `get_compact_diff`, assert output contains `copy from`/`copy to`.

**Class `TestCompactDiffModeChanges`:**

4. `test_mode_change_appears_in_compact_diff` — change file mode via `git update-index --chmod=+x` (with `core.fileMode=true` in the test repo), run `get_compact_diff`, assert output contains `old mode`/`new mode`.

**Class `TestCompactDiffBinaryAndEmpty`:**

5. `test_binary_change_appears_in_compact_diff` — add a binary file on a feature branch, run `get_compact_diff`, assert output contains `Binary files` or `Binary`.
6. `test_empty_file_creation_appears_in_compact_diff` — create an empty file on a feature branch, run `get_compact_diff`, assert output contains `new file mode`.
7. `test_empty_file_deletion_appears_in_compact_diff` — delete a file that was added on main, run `get_compact_diff`, assert output contains `deleted file mode`.

### Production change in `diffs.py`

Add `-M` and `-C=90%` to the shared `diff_args` list in `get_branch_diff()`, before the `if ansi:` branch, so both passes pick them up symmetrically.

## HOW

- Tests import `get_compact_diff` from `mcp_coder.utils.git_operations.compact_diffs`.
- Tests use the `git_repo` fixture (bare repo + configured user) from `tests/utils/git_operations/conftest.py`.
- Each test creates a main branch with initial content, creates a feature branch, makes the specific change type, commits, then calls `get_compact_diff(project_dir, "main")`.
- The mode-change test sets `core.fileMode=true` and uses `git update-index --chmod=+x` for cross-platform support.
- The copy test creates a file on main, then on the feature branch creates a near-identical copy under a new name so `-C=90%` detects it.

## ALGORITHM (flag addition in `get_branch_diff`)

```python
# In get_branch_diff(), both exclude_paths and non-exclude code paths:
# Add after "--no-prefix":
diff_args = [
    f"{base_branch}...HEAD",
    "--unified=5",
    "--no-prefix",
    "-M",          # ← NEW: force rename detection
    "-C=90%",      # ← NEW: force copy detection (90% threshold)
    ...
]
```

Both the `if exclude_paths:` and `else:` branches build `diff_args` — add `-M` and `-C=90%` to both.

## DATA

Integration test outputs are strings from `get_compact_diff()`. Assertions check for presence of specific header keywords:

| Change type | Assert contains |
|------------|----------------|
| Pure rename | `"rename from"`, `"rename to"` |
| Partial rename | `"rename from"`, `"rename to"`, `"@@"` |
| Copy | `"copy from"`, `"copy to"` |
| Mode change | `"old mode"`, `"new mode"` |
| Binary | `"Binary"` or `"binary"` |
| Empty create | `"new file mode"` |
| Empty delete | `"deleted file mode"` |

## Commit

```
feat: add -M/-C=90% flags to get_branch_diff for rename/copy detection (#709)

Forces rename detection (-M) and conservative copy detection (-C=90%)
in both ANSI and plain diff passes, regardless of user's diff.renames
git config. Integration tests verify the full pipeline for all
header-only change types.
```
