# Step 1: Move symbols to branch_naming.py and update imports

> **Context:** See [summary.md](summary.md) for overall goal. This step extracts the two standalone
> symbols from `branch_manager.py` into a new `branch_naming.py` and updates package re-exports.

## LLM Prompt

```
Implement Step 1 of issue #538 (see pr_info/steps/summary.md and pr_info/steps/step_1.md).

Move `BranchCreationResult` and `generate_branch_name_from_issue` from `branch_manager.py`
to a new `branch_naming.py` in the same directory. Update `__init__.py` re-exports.
Use the `move_symbol` MCP tool. Move only — do not change any logic.
Run all quality checks (pylint, pytest, mypy) after changes.
Commit with message: "refactor: extract branch naming symbols to branch_naming.py (#538)"
```

## WHERE

- **Source:** `src/mcp_coder/utils/github_operations/issues/branch_manager.py`
- **Destination:** `src/mcp_coder/utils/github_operations/issues/branch_naming.py` (new)
- **Update:** `src/mcp_coder/utils/github_operations/issues/__init__.py`

## WHAT

Move these two symbols (no signature changes):

```python
# branch_naming.py will contain:

class BranchCreationResult(TypedDict):
    success: bool
    branch_name: str
    error: Optional[str]
    existing_branches: List[str]

def generate_branch_name_from_issue(
    issue_number: int, issue_title: str, max_length: int = 200
) -> str: ...
```

## HOW

1. Use `mcp__tools-py__move_symbol` to move `BranchCreationResult` and `generate_branch_name_from_issue`
   from `branch_manager.py` to `branch_naming.py` — this auto-creates the file and adds an import
   in `branch_manager.py`.
2. Update `__init__.py`: change the import source for these two symbols from `.branch_manager` to `.branch_naming`.
3. Verify `branch_manager.py` now imports `BranchCreationResult` and `generate_branch_name_from_issue`
   from `.branch_naming` (the `move_symbol` tool should handle this).
4. Run format, then all 5 quality checks (pylint, pytest, mypy, lint_imports, vulture) and `mcp-coder check file-size --max-lines 750`.

## DATA

- `branch_naming.py` imports: `re`, `typing` (List, Optional, TypedDict)
- `branch_manager.py` gains: `from .branch_naming import BranchCreationResult, generate_branch_name_from_issue`
- `__init__.py` changes: import source from `.branch_naming` instead of `.branch_manager`

## Verification

- All existing tests pass unchanged (they import from the package `__init__.py`)
- `branch_manager.py` line count drops to ~700
- No logic changes visible in compact diff — only import lines
