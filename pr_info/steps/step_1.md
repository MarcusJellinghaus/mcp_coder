# Step 1 — Smoke-test fix + `session_launch` branch name

## LLM prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_1.md`. Implement step 1 only,
> tests first. Run pylint, pytest (fast unit set, `-n auto`) and mypy until all pass,
> run the formatter, and make one commit: `refactor(vscodeclaude): read session branch via mcp_workspace_git`.

## WHERE

- `tests/test_mcp_workspace_git_smoke.py`
- `src/mcp_coder/workflows/vscodeclaude/session_launch.py` (`regenerate_session_files`, ~line 507)
- `tests/workflows/vscodeclaude/test_session_launch_regenerate.py`
- `tests/workflows/vscodeclaude/test_session_restart_closed_sessions.py` (~403–410, ~575–631: fakes that answer `rev-parse --abbrev-ref`)

No shim change: `get_current_branch_name` is already exported.

## WHAT

1. `test_all_exports_defined` — replace `assert len(__all__) == 30` with:
   ```python
   import mcp_coder.mcp_workspace_git as shim
   assert len(set(shim.__all__)) == len(shim.__all__)
   for name in shim.__all__:
       assert hasattr(shim, name), name
   ```
   (`tests/test_mcp_workspace_github_smoke.py` is untouched — no step adds GitHub exports.)

2. `regenerate_session_files` — replace the `try: execute_subprocess(["git", "rev-parse", ...]) except CalledProcessError` block with:
   ```python
   # Detached HEAD or any failure yields None -> explicit "main" fallback.
   branch_name = get_current_branch_name(folder_path) or "main"
   ```
   `get_current_branch_name` never raises (returns `None` on non-repo, detached HEAD, error).
   Remove `execute_subprocess` / `CommandOptions` / `CalledProcessError` imports if now unused.

## HOW

- Import: `from mcp_coder.mcp_workspace_git import get_current_branch_name` (or add to the existing shim import).

## Tests (write first)

- In `test_session_launch_regenerate.py` (or the closed-sessions file where the branch is asserted):
  - `get_current_branch_name` patched to return `"feature-x"` → status file / script receive `"feature-x"`.
  - patched to return `None` → `"main"` (covers detached HEAD; previously `"HEAD"`).
- Rewrite the closed-sessions fakes that answer `"rev-parse" in cmd` to patch
  `mcp_coder.workflows.vscodeclaude.session_launch.get_current_branch_name` instead; the
  assertion "git rev-parse --abbrev-ref HEAD should be called" becomes
  "`get_current_branch_name` called with the session folder".

## DATA

- `branch_name: str` — never `"HEAD"`, never empty.
