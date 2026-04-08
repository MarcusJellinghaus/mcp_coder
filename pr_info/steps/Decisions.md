# Decisions — Issue #709

Decisions recorded from the plan review discussion that produced the current
plan revision.

## 1. Git CLI flag syntax: `-C90%`, not `-C=90%`

Git's CLI accepts `-C90%` (and `-M`) without an equals sign. Since
`diff_args` is passed positionally to `repo.git.diff(*diff_args)` in
`src/mcp_coder/utils/git_operations/diffs.py` — which shells out directly to
git — we must use git's CLI form. Step 2 and the summary were corrected to
`-C90%` throughout.

## 2. `parse_diff` coverage added to Step 1

The original Step 1 unit tests only hand-crafted `FileDiff` objects, bypassing
`parse_diff()`. We added a parameterised test that feeds raw diff strings for
each header-only change type (pure rename, pure copy, mode change, binary,
empty create, empty delete) directly to `parse_diff()` and asserts on the
resulting `FileDiff.headers`. This closes the gap where rendering could pass
but parsing silently differs.

## 3. Parameterised `render_compact_diff` test for all header-only types

Step 1 originally had only one `TestRenderCompactDiff` test (pure rename). We
added a parameterised test covering all six header-only types at the
`render_compact_diff` level, using raw diff strings as input, to exercise the
full parse→render pipeline for each type.

## 4. `git_repo` fixture description corrected

The plan previously called the `git_repo` fixture a "bare repo + configured
user." It is actually a **non-bare, empty** repo (no initial commit) with a
configured user. Step 2's HOW section now states this correctly and notes
that each integration test must create an initial commit on `main` before
branching.

## 5. Explicit ripple-effect check in Step 2

Adding `-M` changes how git renders delete+add file pairs that become
renames. Step 2's HOW section now instructs the implementer to verify that
existing tests in `tests/utils/git_operations/test_diffs.py`,
`tests/utils/test_git_encoding_stress.py`, and
`tests/workflows/create_pr/test_generation.py` do not assert on delete+add
shapes that will now collapse into renames.

## 6. Copy-test setup detailed

Plain `-C` only considers files modified in the same commit as copy
candidates. Rather than switch to `--find-copies-harder`, we keep the plan
aligned with the issue's `-C90%` decision by modifying the source file's
content slightly AND creating a near-identical copy in the same commit. Step
2 test #3 description was updated accordingly.

## 7. Loosen `test_file_headers_emitted_when_no_parsed_hunks` assertion

The updated test (replacement for `test_file_entirely_skipped_when_no_hunks`)
now checks that each header line is present as a substring in the returned
string (contains-based), rather than strict equality to
`"\n".join(headers)`. This survives future join-style refactors while still
guarding the behavioural fix.

## Additional decisions from Round 2

### 8. Integration tests capture base branch via `get_current_branch_name`

Step 2 integration tests must not hard-code `"main"` as the base branch — the
default branch depends on the user's `init.defaultBranch` git config. Each
test now calls `get_current_branch_name(project_dir)` *before* creating the
feature branch and passes that captured name to `get_compact_diff`. This
matches the existing pattern in `tests/utils/git_operations/test_diffs.py`.

### 9. Integration tests use `git_repo_with_commit` fixture

Step 2 integration tests now use the existing `git_repo_with_commit` fixture
from `tests/utils/git_operations/conftest.py` instead of `git_repo`. The
fixture already provides an initial README commit on the default branch, so
each test no longer needs manual initial-commit setup. This simplifies the
tests and matches house style used by existing integration tests.

### 10. `parse_diff` header-only assertion tightened

Step 1's `test_parse_diff_header_only_change_types` now asserts
`file_diff.hunks == []` for all six header-only cases, rather than "where
applicable." Every header-only diff block should parse to an empty hunks
list.
