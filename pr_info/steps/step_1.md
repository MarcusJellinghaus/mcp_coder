# Step 1 — Neutral names for the implement check loop (Scope 6)

## LLM prompt

> Read `pr_info/steps/summary.md` and this file (`pr_info/steps/step_1.md`).
> Implement Step 1 only: rename the mypy-specific names of the implement check
> loop. Pure rename, no behaviour change. Update tests first, then the code.
> Run format, pylint, mypy and the fast pytest set; all must pass. One commit.

## WHERE

- `src/mcp_coder/workflows/implement/check_loop.py`
- `src/mcp_coder/workflows/implement/core.py`
- `src/mcp_coder/workflows/implement/task_processing.py`
- `src/mcp_coder/workflows/implement/__init__.py`
- `pyproject.toml` (`real_check_loop` marker description)
- `vulture_whitelist.py` (`_stub_final_mypy_pass` entry)
- Tests: `tests/workflows/implement/**` (string patch targets, `_STAGE` in
  `test_core_final_check.py`, `"step_2_mypy_3"` in `test_check_loop_fix_turns.py`,
  the helper `_stub_final_mypy_pass` wherever defined/used)

## WHAT

| Today | New |
|---|---|
| `check_and_fix_mypy(...)` | `check_and_fix(...)` (same signature) |
| `__all__` entry `"check_and_fix_mypy"` | `"check_and_fix"` |
| stage `"Final mypy check"` (`core.py`, 2 places incl. docstring) | `"Final checks"` |
| `"LLM failure during final mypy check"` | `"LLM failure during final checks"` |
| `"Running final mypy check after all tasks..."` | `"Running final checks after all tasks..."` |
| `"Formatting failed after final mypy check"` | `"Formatting failed after final checks"` |
| `"Committing final mypy fixes..."` / `"Failed to commit final mypy fixes"` / `"Failed to push final mypy fixes"` | `... final check fixes ...` |
| `"No changes from final mypy check - skipping commit"` | `"No changes from final checks - skipping commit"` |
| `"Running mypy type checking..."` | `"Running checks..."` |
| `"Mypy check passed after %d fix turns"` | `"Checks passed after %d fix turns"` |
| session `f"step_{step_num}_mypy_{turn}"` | `f"step_{step_num}_check_{turn}"` |
| comments `# Use step number 0 for final mypy check conversation`, `# Format code after mypy fixes`, `# Commit mypy fixes ...` | "final checks" / "check fixes" |
| `task_processing.py` module docstring "mypy fixes" | "check fixes" |
| `_stub_final_mypy_pass` (test helper) | `_stub_final_check_pass` |

Keep comments about mypy as mcp-coder's own type checker ("Type narrowing for
mypy", "Fallback keeps mypy happy", `constants.py` "for mypy").

## HOW

- Use `mcp__mcp-tools-py__rename_symbol` for `check_and_fix_mypy`, then fix
  string patch targets (`"mcp_coder.workflows.implement.core.check_and_fix_mypy"`,
  `"...task_processing.check_and_fix_mypy"`) with `search_files` + `edit_file`.
- Marker text in `pyproject.toml`:
  `"real_check_loop: opt out of the autouse task_processing.check_and_fix patch in implement tests"`.

## DATA

No data changes.

## Done when

`search_files(pattern="(?i)mypy", glob="src/mcp_coder/workflows/implement/*.py")`
shows only comments about mcp-coder's own type checking; no test references
`check_and_fix_mypy`, `step_*_mypy_*` or `_stub_final_mypy_pass`.
