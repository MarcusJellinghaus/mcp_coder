# Step 3 — Git conflict helpers

Add the deterministic git plumbing for the Python-driven conflict loop. All helpers use
the existing `_run_git`; its signature is untouched. See [summary.md](./summary.md)
("Conflict loop").

## WHERE

- Modify: `src/mcp_coder/workflows/rebase.py` (add a `# --- Conflict handling ---`
  section)
- Modify: `tests/workflows/rebase/test_git_helpers.py` (extend, following its existing
  patterns and markers — real temp-repo tests carry the `git_integration` marker like
  the current ones; pure text helpers get plain unit tests)

## WHAT

```python
def _conflicted_files(project_dir: Path) -> list[str]: ...
def _binary_conflict(project_dir: Path) -> str | None: ...
def _resolve_pr_info_conflict(project_dir: Path, file: str) -> bool: ...
def _has_conflict_markers(project_dir: Path, file: str) -> bool: ...
def _show_stage(project_dir: Path, stage: int, file: str) -> str | None: ...
def _stage_all_and_continue(project_dir: Path) -> _GitResult: ...
```

## HOW / ALGORITHM

```
_conflicted_files:      git diff --name-only --diff-filter=U → non-empty lines
_binary_conflict:       git diff --numstat → first path whose added/deleted columns are "-"
                        (binary marker); None if none
_resolve_pr_info_conflict(file):
                        git checkout --theirs -- <file>; ok → git add -- <file>, True
                        else (delete/modify: feature branch deleted it) →
                        git rm -- <file>; return returncode == 0
_has_conflict_markers:  read file text (utf-8, errors="replace"); True if any line
                        starts with "<<<<<<< " or ">>>>>>> "; missing file → False
                        (legitimately deleted during resolution)
_show_stage(stage, file):
                        git show :<stage>:<file> → stdout, or None on non-zero exit
                        (side absent, e.g. delete/modify) — stages: 1=common ancestor
                        (merge base), 2=ours (base branch, rebased onto), 3=theirs
                        (feature commits)
_stage_all_and_continue:
                        git add -A            # plain, no pathspec — see summary
                        git -c core.editor=true rebase --continue
                        return the _GitResult of the continue
```

Notes:

- `git add -A` is **deliberate** (delete/modify resolutions and adjacent LLM edits both
  break per-file `git add`); do not add exclude pathspecs.
- `-c core.editor=true` is passed as leading args to `_run_git` (`"-c",
  "core.editor=true", "rebase", "--continue"`) so the non-interactive continue never
  blocks on an editor. `_run_git` itself is not modified.
- `=======` alone must NOT count as a conflict marker (it appears in legitimate text,
  e.g. markdown underlines); only the seven-char `<<<<<<< ` / `>>>>>>> ` line prefixes.
- `_binary_conflict` **must be verified against real git behavior** (the two
  integration tests below): at a conflict stop, bare `git diff --numstat` output for
  unmerged paths is not guaranteed to distinguish binary from text. If it proves
  ambiguous (e.g. `-`/`-` for every unmerged path, or unmerged paths omitted), fall
  back to stage-blob comparison: `git ls-files -u` for the stage SHAs, then blob-level
  `git diff --numstat <ours-sha> <theirs-sha>` (where `-` reliably means binary).

## DATA

- `_conflicted_files`: list of repo-relative paths (git's own output order).
- `_binary_conflict`: offending path or `None`.
- `_resolve_pr_info_conflict`: `True` when the file is resolved and staged.
- `_show_stage`: file content string, or `None` when that side does not exist.
- `_stage_all_and_continue`: the `_GitResult` of `rebase --continue` (caller checks
  `.returncode` — non-zero usually means the next commit also conflicts, which is the
  loop's continue condition, not an error).

## TDD

Extend `tests/workflows/rebase/test_git_helpers.py` first:

1. Temp-repo integration tests (`git_integration`): create a real conflict (two branches
   editing one line), assert `_conflicted_files` finds it and `_show_stage` returns all
   three versions; a `pr_info/` conflict resolves via `--theirs`; a delete/modify
   `pr_info/` conflict falls back to `git rm`; `_stage_all_and_continue` finishes a
   single-conflict rebase.
2. `_binary_conflict` integration tests (`git_integration`, both mandatory — a false
   positive here would abort every LLM conflict resolution):
   - text-file conflict → `_binary_conflict(...)` returns `None`;
   - binary-file conflict (conflicting NUL-byte blobs) → returns the path.
3. Plain unit tests: `_has_conflict_markers` on temp files — real markers → True,
   markdown `=======` underline → False, missing file → False.

## Commit

One commit. Suggested message:
`feat: add deterministic git conflict helpers for rebase workflow`

## LLM Prompt

> Read `pr_info/steps/summary.md` for context, then implement `pr_info/steps/step_3.md`
> exactly: add the six conflict helpers to `src/mcp_coder/workflows/rebase.py` using the
> existing `_run_git` (do not change its signature; pass `-c core.editor=true` as git
> args). Write the tests in `tests/workflows/rebase/test_git_helpers.py` first (TDD),
> following that file's existing fixture and marker conventions. Do not modify the
> orchestrator. Run pylint, pytest (include the `git_integration` marker run for the new
> tests), and mypy via the MCP check tools and fix any findings before finishing.
