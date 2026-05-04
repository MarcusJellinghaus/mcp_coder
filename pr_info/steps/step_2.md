# Step 2 — Adopt shim in langchain session storage

## LLM Prompt
> Read `pr_info/steps/summary.md` for context, then implement
> `pr_info/steps/step_2.md`. The shim from step 1 is already in place;
> this step swaps two `Path.home() / ".mcp_coder" / "sessions" /
> "langchain"` literals to `get_user_app_data_dir("mcp_coder") /
> "sessions" / "langchain"`. Run all four checks before committing.

## Why this is one commit
Both files describe the same concept (langchain session directory) and
land together cleanly.

## WHERE
- **Modify**: `src/mcp_coder/llm/storage/session_storage.py` (line ~165)
- **Modify**: `src/mcp_coder/llm/storage/session_finder.py` (line ~32)

## WHAT

### `session_storage.py`
Replace:
```python
root = (
    Path(base_dir)
    if base_dir
    else Path.home() / ".mcp_coder" / "sessions" / "langchain"
)
```
With:
```python
root = (
    Path(base_dir)
    if base_dir
    else get_user_app_data_dir("mcp_coder") / "sessions" / "langchain"
)
```

### `session_finder.py`
Replace:
```python
session_dir = Path.home() / ".mcp_coder" / "sessions" / "langchain"
```
With:
```python
session_dir = get_user_app_data_dir("mcp_coder") / "sessions" / "langchain"
```
Also update the function docstring (`"Searches ~/.mcp_coder/sessions/langchain/..."`) — leaves the literal as-is since it's still accurate after this change.

## HOW
Both files add:
```python
from mcp_coder.utils.user_app_data import get_user_app_data_dir
```
(Use the project's relative-import convention if the surrounding code
already uses one, e.g. `from ...utils.user_app_data import ...`. Match
existing style.)

## ALGORITHM
N/A — literal substitution.

## DATA
No structural changes. The constructed paths are byte-identical on
every platform (already `~/.mcp_coder/sessions/langchain/` everywhere).

## Test changes
None expected — there are no tests asserting these path literals
(quick grep first to confirm). If a test surfaces, update it to use
`get_user_app_data_dir("mcp_coder")` or delete a platform-branching
fragment if any exists.

## Verification
1. `mcp__tools-py__run_pytest_check` (fast unit tests)
2. `mcp__tools-py__run_pylint_check`
3. `mcp__tools-py__run_mypy_check`
4. `mcp__tools-py__run_lint_imports_check`
5. Commit message: `llm: route langchain session storage through user_app_data shim`
