# Step 5 — Extract shared `check_git_clean` prerequisite step

**Goal:** Consolidate the duplicated git-cleanliness sub-check (`implement/prerequisites.py`
and `create_pr/core.py`) into one shared step. Independent of Step 6.

## WHERE

Create:
- `src/mcp_coder/workflow_steps/prerequisites.py`
- `tests/workflow_steps/test_prerequisites.py`

Modify:
- `src/mcp_coder/workflows/implement/prerequisites.py` (delegate to shared step)
- `src/mcp_coder/workflows/create_pr/core.py` (delegate the git-clean check in `check_prerequisites`)

## WHAT (signature)

In `workflow_steps/prerequisites.py`:
```python
def check_git_clean(project_dir: Path) -> bool
```

Body = `implement`'s current `check_git_clean` (the richer version: `is_working_directory_clean(
project_dir, ignore_files=DEFAULT_IGNORED_BUILD_ARTIFACTS)`, on dirty log detailed
`get_full_status`, handle `ValueError` → False).

## HOW (integration points)

- `prerequisites.py` imports `DEFAULT_IGNORED_BUILD_ARTIFACTS` (constants),
  `get_full_status` / `is_working_directory_clean` (mcp_workspace_git).
- `implement/prerequisites.py`: replace its local `check_git_clean` body with a call to
  `mcp_coder.workflow_steps.prerequisites.check_git_clean`. Keep the name importable
  from `implement/prerequisites` (thin wrapper or re-export) so `core.py` and existing
  patch targets keep working.
- `create_pr/core.py`: in `check_prerequisites`, replace the inline
  `is_working_directory_clean(...)` try/except block with
  `if not check_git_clean(project_dir): return False`.
- **Exception-scope delta (conscious, accepted):** create_pr's current block catches
  **all** exceptions → False; the shared `check_git_clean` catches only `ValueError` →
  False (letting other exceptions from the inner `get_full_status` be swallowed by its
  nested try). Since `is_working_directory_clean` is documented to raise `ValueError`,
  this is practically equivalent — accept the narrowing rather than widening the shared
  step's catch.

## ALGORITHM

```
try:
    clean = is_working_directory_clean(project_dir, ignore_files=DEFAULT_IGNORED_BUILD_ARTIFACTS)
except ValueError as e:
    log error(e); return False
if not clean:
    log error + per-category get_full_status detail; return False
return True
```

## DATA

`bool` — True when the working directory is clean (ignoring build artifacts).

## TDD

Write `tests/workflow_steps/test_prerequisites.py::test_check_git_clean_*` first
(clean → True; dirty → False with detail logging; `ValueError` → False), reusing the
existing `implement` git-clean test cases. Then extract. Adjust the `create_pr`
prerequisite tests for the shared step — note create_pr now gains the detailed
`get_full_status` log lines on the dirty path (log-only delta, no functional change).

## Checks / commit

All enforcers + pylint / pytest / mypy green. One commit:
`refactor(workflow_steps): extract shared check_git_clean prerequisite`.

## LLM prompt

> Read `pr_info/steps/summary.md` (section "Prerequisite extraction") and
> `pr_info/steps/step_5.md`. Create `workflow_steps/prerequisites.py` with a
> `check_git_clean(project_dir) -> bool` step using implement's current (detailed)
> git-clean logic. Repoint `implement/prerequisites.py` to delegate to it (keeping the
> name importable), and replace the inline git-clean check in
> `create_pr/core.py::check_prerequisites` with a call to the shared step. Write the
> shared step's tests in `tests/workflow_steps/test_prerequisites.py` first, then adjust
> the create_pr prerequisite tests for the shared step's logging. Do not change the
> cleanliness determination. Verify all enforcers and the pylint/pytest/mypy trio are
> green, then produce one commit.
