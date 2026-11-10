# Step 1: Move `read_and_clear_blocked` into `blocked.py`

Pure refactor, no behaviour change. Step 3's `check_loop.py` needs `read_and_clear_blocked`, and `task_processing.py` will import `check_loop.py`; keeping the helper in `task_processing.py` would create a circular import.

## LLM prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_1.md`. Implement step 1 only: move `read_and_clear_blocked`, `BLOCKED_REASON_MAX_CHARS` and `BLOCKED_REASON_FALLBACK` from `task_processing.py` into a new `blocked.py` with `mcp__mcp-tools-py__move_symbol`, then fix any imports the tool missed. Run pylint, mypy and the fast pytest suite; all must pass. Format, then make one commit.

## WHERE
- Create `src/mcp_coder/workflows/implement/blocked.py`.
- Modify `src/mcp_coder/workflows/implement/task_processing.py`, `core.py`, `finalisation.py`.
- Modify `tests/workflows/implement/test_task_processing_blocked.py` (imports only).

## WHAT
```python
# blocked.py
BLOCKED_REASON_MAX_CHARS = 500
BLOCKED_REASON_FALLBACK = "Agent reported being blocked but gave no reason"

def read_and_clear_blocked(project_dir: Path) -> str | None: ...  # body unchanged
```

## HOW
- Use `mcp__mcp-tools-py__move_symbol(source_file="src/mcp_coder/workflows/implement/task_processing.py", symbol_names=["read_and_clear_blocked", "BLOCKED_REASON_MAX_CHARS", "BLOCKED_REASON_FALLBACK"], dest_file="src/mcp_coder/workflows/implement/blocked.py")`.
- `blocked.py` imports `BLOCKED_FILE` from `.constants` and has its own `logger = logging.getLogger(__name__)`.
- `task_processing.py` keeps using the helper via `from .blocked import read_and_clear_blocked`, so `@patch("...task_processing.read_and_clear_blocked")` targets keep working.
- `core.py` and `finalisation.py` import from `.blocked`. Update `@patch("mcp_coder.workflows.implement.core.read_and_clear_blocked")` targets only if the name in `core` changes (it doesn't).
- Tests importing the constants import them from `mcp_coder.workflows.implement.blocked`.
- Check the `.importlinter` / `tach` config: if a contract lists `task_processing` explicitly for this helper, add `blocked`. If a contract prevents the new module and you cannot fix it, write one line to `pr_info/.blocked.txt` saying which contract, and stop.

## ALGORITHM
None (move only).

## DATA
Unchanged.

## Tests
No new tests. The existing `test_task_processing_blocked.py` tests (including `test_blocked_wins_over_changed_files`) must pass unchanged apart from imports.
