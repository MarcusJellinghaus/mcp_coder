# Step 2: Integration tests + `-M`/`-C90%` flags

## LLM Prompt

> Read `pr_info/steps/summary.md` for context. Implement Step 2: add git_integration tests in a new file `test_compact_diffs_integration.py` that exercise the full pipeline with real git repos, then add `-M` and `-C90%` flags to `get_branch_diff()` in `diffs.py`. Follow TDD — write tests first (they will fail without the flags for rename/copy detection), then add the flags, then verify all checks pass. Tests use the `git_repo_with_commit` fixture and capture the base branch name via `get_current_branch_name()` (never hard-code `"main"`).

## WHERE

- **Create**: `tests/utils/git_operations/test_compact_diffs_integration.py`
- **Modify**: `src/mcp_coder/utils/git_operations/diffs.py`

## WHAT

### Integration tests in `test_compact_diffs_integration.py`

All tests marked `@pytest.mark.git_integration`, using the existing `git_repo_with_commit` fixture from `conftest.py` (which provides a repo with one initial README commit on the default branch). Each test calls `get_current_branch_name(project_dir)` to capture the base branch name *before* creating a feature branch, then passes that captured name to `get_compact_diff(project_dir, base_branch)`. Never hard-code `"main"` — the default branch depends on the user's `init.defaultBranch` git config. This matches the existing pattern in `tests/utils/git_operations/test_diffs.py`.

**Class `TestCompactDiffRenames`:**

1. `test_pure_rename_appears_in_compact_diff` — capture base branch name, create feature branch, rename a file with no content change, commit, run `get_compact_diff(project_dir, base_branch)`, assert output contains `rename from` and `rename to`.
2. `test_partial_rename_shows_headers_and_hunks` — capture base branch name, create feature branch, rename a file AND change some content, commit, run `get_compact_diff(project_dir, base_branch)`, assert output contains `rename from`/`rename to` AND the content diff.

**Class `TestCompactDiffCopies`:**

3. `test_pure_copy_appears_in_compact_diff` — capture base branch name, create feature branch, modify the source file's content slightly AND create a near-identical copy under a new name in the same commit, so git considers the source as a copy candidate (plain `-C` only considers files modified in the commit as copy sources). Run `get_compact_diff(project_dir, base_branch)`, assert output contains `copy from`/`copy to`.

**Class `TestCompactDiffModeChanges`:**

4. `test_mode_change_appears_in_compact_diff` — capture base branch name, create feature branch, change file mode via `git update-index --chmod=+x` (with `core.fileMode=true` in the test repo), commit, run `get_compact_diff(project_dir, base_branch)`, assert output contains `old mode`/`new mode`.

**Class `TestCompactDiffBinaryAndEmpty`:**

5. `test_binary_change_appears_in_compact_diff` — capture base branch name, create feature branch, add a binary file, commit, run `get_compact_diff(project_dir, base_branch)`, assert output contains `Binary files` or `Binary`.
6. `test_empty_file_creation_appears_in_compact_diff` — capture base branch name, create feature branch, create an empty file, commit, run `get_compact_diff(project_dir, base_branch)`, assert output contains `new file mode`.
7. `test_empty_file_deletion_appears_in_compact_diff` — on the base branch add a file and commit, capture base branch name, create feature branch, delete that file, commit, run `get_compact_diff(project_dir, base_branch)`, assert output contains `deleted file mode`.

### Production change in `diffs.py`

Add `-M` and `-C90%` to the shared `diff_args` list in `get_branch_diff()`, before the `if ansi:` branch, so both passes pick them up symmetrically.

## HOW

- Tests import `get_compact_diff` from `mcp_coder.utils.git_operations.compact_diffs` and `get_current_branch_name` from `mcp_coder.utils.git_operations.branches` (matching the import pattern used in `tests/utils/git_operations/test_diffs.py`).
- Tests use the `git_repo_with_commit` fixture from `tests/utils/git_operations/conftest.py`, which provides a non-bare repo with one initial README commit on the default branch and configured user — no manual initial-commit setup needed in each test.
- Each test calls `base_branch = get_current_branch_name(project_dir)` *before* creating the feature branch, creates the feature branch, makes the specific change type, commits, then calls `get_compact_diff(project_dir, base_branch)`. The base branch is never hard-coded to `"main"` because the default branch depends on the user's `init.defaultBranch` git config.
- The mode-change test sets `core.fileMode=true` and uses `git update-index --chmod=+x` for cross-platform support.
- The copy test modifies the source file slightly AND creates a near-identical copy under a new name in the same commit, so git's `-C90%` detects it (plain `-C` only considers files modified in that commit as copy sources).
- **Ripple-effect check**: before committing, verify the existing tests in `tests/utils/git_operations/test_diffs.py`, `tests/utils/test_git_encoding_stress.py`, and `tests/workflows/create_pr/test_generation.py` do not assert on delete+add shapes that will now collapse into renames after adding `-M`; update any assertions that break.

## ALGORITHM (flag addition in `get_branch_diff`)

`diff_args` is passed positionally via GitPython's `repo.git.diff(*diff_args)`, which shells out to git — so flags must use git's CLI syntax. Git accepts `-M` and `-C90%` (no equals sign); `-C=90%` is NOT valid.

```python
# In get_branch_diff(), both exclude_paths and non-exclude code paths:
# Add after "--no-prefix":
diff_args = [
    f"{base_branch}...HEAD",
    "--unified=5",
    "--no-prefix",
    "-M",          # ← NEW: force rename detection
    "-C90%",       # ← NEW: force copy detection (90% threshold)
    ...
]
```

Both the `if exclude_paths:` and `else:` branches build `diff_args` — add `-M` and `-C90%` to both.

## DATA

Integration test inputs come from the `git_repo_with_commit` fixture (one initial README commit on the default branch). Each test captures the base branch name with `get_current_branch_name(project_dir)` before branching and passes that captured value to `get_compact_diff`. Integration test outputs are strings from `get_compact_diff()`. Assertions check for presence of specific header keywords:

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
feat: add -M/-C90% flags to get_branch_diff for rename/copy detection (#709)

Forces rename detection (-M) and conservative copy detection (-C90%)
in both ANSI and plain diff passes, regardless of user's diff.renames
git config. Integration tests verify the full pipeline for all
header-only change types.
```
