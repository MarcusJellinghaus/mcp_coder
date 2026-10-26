# Step 9 — `vscodeclaude/status.get_folder_git_status` (dirty gate)

## LLM prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_9.md`. Implement step 9 only,
> tests first. Run pylint, pytest (fast unit set, `-n auto`) and mypy until all pass,
> run the formatter, and make one commit: `refactor(vscodeclaude): folder git status via mcp_workspace_git`.

## WHERE

- `src/mcp_coder/mcp_workspace_git.py` — export `get_working_tree_status` (from `mcp_workspace.git_operations.repository_status`)
- `src/mcp_coder/workflows/vscodeclaude/status.py` — `get_folder_git_status` (~164); drop the `subprocess_runner` import
- `tests/workflows/vscodeclaude/test_folder_git_status.py`, `tests/workflows/vscodeclaude/test_status_display.py` (~306–343)

## WHAT

```python
def get_folder_git_status(folder_path: Path) -> str:
    if not folder_path.exists():
        return "Missing"
    if not is_git_repository(folder_path):
        return "No Git"
    status = get_working_tree_status(folder_path)
    if not status["success"]:
        return "Error"          # never read a git failure as clean
    return "Clean" if status["clean"] else "Dirty"
```

**Not** `get_full_status` / `is_working_directory_clean` (both read errors as clean).
`is_git_repository` first keeps "No Git" distinct from "Error". Upstream does not search parent
dirs: a non-repo folder inside a repo is now "No Git" (accepted). `clean` counts untracked
files, matching today's `status --porcelain`. `check_folder_dirty` is unchanged.

## Tests (write first) — dirty-gate parity

Patch `mcp_coder.workflows.vscodeclaude.status.{is_git_repository, get_working_tree_status}`.

- missing folder → `"Missing"`, nothing called.
- `is_git_repository` `False` → `"No Git"`; status not called.
- `success=True, clean=True` → `"Clean"`; `clean=False` → `"Dirty"`.
- `success=False, clean=False` → `"Error"` (and `check_folder_dirty` → `True`, i.e. cleanup never deletes on a git failure).
- Rewrite the `"rev-parse" in cmd` fakes in both test files.

## DATA

- One of `"Clean" | "Dirty" | "Missing" | "No Git" | "Error"` (unchanged).
