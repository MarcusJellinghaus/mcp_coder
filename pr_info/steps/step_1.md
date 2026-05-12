# Step 1 — Bind window-title match to owning VSCode process (Item #1)

## LLM Prompt

> Read `pr_info/steps/summary.md` and this file (`pr_info/steps/step_1.md`) in
> full. Implement only what this step describes. Follow TDD: write failing
> tests first, then implementation, then run the three MCP quality checks
> (pylint, pytest with `-n auto` and the recommended `not <integration>`
> markers, mypy). One commit at the end.

## Goal

Eliminate the cross-process title-leak that produced the `#946`/`#950` style
false positives where some unrelated VSCode owns a window whose title
accidentally contains the issue number and repo name.

## WHERE

- `src/mcp_coder/workflows/vscodeclaude/sessions.py`
- `tests/workflows/vscodeclaude/test_sessions.py`

## WHAT — function signatures

```python
# sessions.py — module-level cache type changes
_vscode_window_cache: list[tuple[int, str]] | None = None

def _get_vscode_window_titles(refresh: bool = False) -> list[tuple[int, str]]:
    """Return list of (pid, title) pairs for visible VSCode windows."""

def is_vscode_window_open_for_folder(
    folder_path: str,
    issue_number: int | None = None,
    repo: str | None = None,
) -> bool:
    """Now requires title's owning PID to also have folder_path in its cmdline."""
```

`clear_vscode_window_cache` signature unchanged. Public `__init__.py`
re-exports unchanged.

## HOW — integration points

- `_get_vscode_window_titles` already extracts `pid` via
  `win32process.GetWindowThreadProcessId(hwnd)` — just stop discarding it.
- `is_vscode_window_open_for_folder` reuses `_get_vscode_processes()` (already
  caches results) and the same substring check `is_vscode_open_for_folder`
  uses today (lowercase `folder_str` or `folder_name`).
- No changes to callers; behavior change only.
- **Cache semantics preserved**: the change to `_get_vscode_window_titles`
  (returning `(pid, title)` tuples) must preserve the existing
  `_vscode_pids_cache` / `_vscode_window_cache` refresh semantics. Only the
  cached payload type changes — do not modify cache lifetime, refresh
  triggers, or `clear_vscode_window_cache` behavior.

## ALGORITHM

```
matching_pids = {p["pid"] for p in _get_vscode_processes()
                 if folder_str in p["cmdline_lower"]
                 or folder_name in p["cmdline_lower"]}
for pid, title in titles:
    if pid not in matching_pids:
        continue
    if issue_pattern in title and repo_name in title.lower():
        return True
return False
```

## DATA

- Cache: `list[tuple[int, str]]` — VSCode-owned visible windows.
- `matching_pids: set[int]` — PIDs whose cmdline references the target folder.
- Return: `bool` (unchanged).

## Tests (write first)

In `tests/workflows/vscodeclaude/test_sessions.py`:

1. **Cross-process false-positive guard**: mock `_get_vscode_processes` to
   return two processes (A: pid=100, cmdline contains `mcp_coder_950`;
   B: pid=200, cmdline contains `mcp_coder_946`). Mock
   `_get_vscode_window_titles` to return `[(100, "[#946 stuff] - mcp_coder")]`.
   Call `is_vscode_window_open_for_folder("/tmp/mcp_coder_946", 946,
   "owner/mcp_coder")` → expect `False` (title pid=100 doesn't match cmdline
   for folder `mcp_coder_946`).
2. **Positive match preserved**: same setup but window pid=200 → expect `True`.
3. **Return-shape test**: assert `_get_vscode_window_titles()` returns a list
   of `(int, str)` tuples; first element of each tuple is the PID.
4. Update any existing tests that depended on `list[str]` return shape.

## Done when

- New + updated tests pass.
- `mcp__tools-py__run_pylint_check`, `mcp__tools-py__run_pytest_check`
  (`extra_args=["-n", "auto", "-m", "not git_integration and not
  claude_cli_integration and not claude_api_integration and not
  formatter_integration and not github_integration and not
  langchain_integration"]`), `mcp__tools-py__run_mypy_check` all pass.
- One commit: tests + implementation.
