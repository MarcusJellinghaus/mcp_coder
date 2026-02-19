# Step 1: Extend `get_branch_diff()` with `ansi` parameter

## Goal

Add an optional `ansi: bool = False` parameter to `get_branch_diff()`. When
`True`, inject `--color=always` into the git diff args so that ANSI color codes
(used in Pass 1 of the compact diff pipeline) are preserved in the output.
Backward-compatible: all existing callers are unaffected.

---

## WHERE

**Modify:** `src/mcp_coder/utils/git_operations/diffs.py`

**Test:** `tests/utils/git_operations/test_diffs.py`  
(add to existing `TestDiffOperations` class — do **not** create a new file)

---

## WHAT

```python
def get_branch_diff(
    project_dir: Path,
    base_branch: Optional[str] = None,
    exclude_paths: Optional[list[str]] = None,
    ansi: bool = False,          # NEW parameter
) -> str:
```

When `ansi=True`:
- Insert `"--color=always"` as the first element of `diff_args`
- **Windows note:** follow the existing pattern in this file — no `LC_ALL` on
  Windows (`os.name != "nt"` guard already present)

No other changes to the function.

---

## HOW

Integration points:
- Called by `compact_diffs.get_compact_diff()` (Step 2) with `ansi=True`
- All existing callers pass no `ansi` argument → default `False` → unchanged

---

## ALGORITHM

```
if ansi:
    prepend "--color=always" to diff_args list
else:
    diff_args unchanged (existing behaviour)
run repo.git.diff(*diff_args) as before
return str(diff_output)
```

---

## DATA

Return type unchanged: `str`.  
When `ansi=True` the returned string contains ANSI escape sequences (e.g.
`\x1b[2;37m`). Callers that need plain text should use `ansi=False` (default).

---

## TESTS TO ADD (in existing `test_diffs.py`)

Add to `TestDiffOperations`:

```python
def test_get_branch_diff_ansi_false_returns_plain_text(
    self, git_repo_with_commit: tuple[Repo, Path]
) -> None:
    """Default ansi=False returns a string without ANSI escape codes."""
    ...
    diff = get_branch_diff(project_dir, base_branch)
    assert "\x1b[" not in diff   # no ANSI codes

def test_get_branch_diff_ansi_parameter_accepted(
    self, git_repo_with_commit: tuple[Repo, Path]
) -> None:
    """ansi=True is accepted without error (smoke test — ANSI may or may not
    appear depending on git/terminal, but the call must not raise)."""
    ...
    diff = get_branch_diff(project_dir, base_branch, ansi=True)
    assert isinstance(diff, str)
```

---

## LLM PROMPT

```
Read pr_info/steps/summary.md and pr_info/steps/step_1.md.

Implement Step 1 exactly as specified.

Files to modify:
  src/mcp_coder/utils/git_operations/diffs.py
  tests/utils/git_operations/test_diffs.py

Changes required:
1. Add `ansi: bool = False` parameter to `get_branch_diff()` in diffs.py.
   When True, prepend "--color=always" to diff_args before calling repo.git.diff().
   Follow the existing Windows guard pattern (no LC_ALL on Windows).
   Do not change any other behaviour.

2. Add the two new test methods described in step_1.md to the existing
   TestDiffOperations class in test_diffs.py.
   Mark them @pytest.mark.git_integration (same as existing tests in that class).

Do not modify any other files.
Run the new tests to verify they pass before finishing.
```
