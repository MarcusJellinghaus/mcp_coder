# Step 1: Refactor `failure_handling.py` — replace GitPython with subprocess

## Context
See [summary.md](summary.md) for full issue context.

`get_diff_stat()` in `failure_handling.py` is the sole consumer of `_safe_repo_context` (raw GitPython). It must be replaced with a subprocess call before the shim flip, otherwise GitPython isolation is violated.

## WHERE

| File | Action |
|------|--------|
| `src/mcp_coder/workflow_utils/failure_handling.py` | Modify |
| `tests/workflow_utils/test_failure_handling.py` | Modify |

## WHAT

### `get_diff_stat(project_dir: Path) -> str`
- **Current**: Uses `_safe_repo_context` to get a GitPython `Repo`, then calls `repo.git.diff("HEAD", "--stat")`
- **New**: Uses `execute_command(["git", "diff", "HEAD", "--stat"], cwd=str(project_dir))` from `subprocess_runner`
- **Signature unchanged**: `get_diff_stat(project_dir: Path) -> str`
- **Return value unchanged**: diff stat string, or empty string on error

## HOW

### Import changes in `failure_handling.py`
```python
# REMOVE:
from mcp_coder.mcp_workspace_git import _safe_repo_context

# ADD:
from mcp_coder.utils.subprocess_runner import execute_command
```

Note: `extract_issue_number_from_branch` and `get_current_branch_name` imports from the shim stay — they are used by `handle_workflow_failure`.

## ALGORITHM

```
def get_diff_stat(project_dir):
    result = execute_command(["git", "diff", "HEAD", "--stat"], cwd=str(project_dir))
    if result.return_code == 0:
        return result.stdout
    return ""
```

Wrap in try/except for safety (same broad exception pattern as current code).

## DATA

- `execute_command` returns `CommandResult` with `.return_code: int`, `.stdout: str`, `.stderr: str`
- Function returns `str` (diff stat output or empty string)

## Test changes in `test_failure_handling.py`

### `TestGetDiffStat.test_returns_diff_stat`
```python
# BEFORE: patches _safe_repo_context, asserts repo.git.diff called
# AFTER:  patches execute_command, asserts called with ["git", "diff", "HEAD", "--stat"]

@patch("mcp_coder.workflow_utils.failure_handling.execute_command")
def test_returns_diff_stat(self, mock_exec: MagicMock) -> None:
    mock_exec.return_value = MagicMock(return_code=0, stdout=" file.py | 2 +-\n 1 file changed")
    result = get_diff_stat(Path("/fake/project"))
    assert result == " file.py | 2 +-\n 1 file changed"
    mock_exec.assert_called_once_with(["git", "diff", "HEAD", "--stat"], cwd="/fake/project")
```

### `TestGetDiffStat.test_returns_empty_on_error`
```python
# BEFORE: patches _safe_repo_context to raise
# AFTER:  patches execute_command to return non-zero

@patch("mcp_coder.workflow_utils.failure_handling.execute_command")
def test_returns_empty_on_error(self, mock_exec: MagicMock) -> None:
    mock_exec.return_value = MagicMock(return_code=1, stdout="", stderr="error")
    result = get_diff_stat(Path("/fake/project"))
    assert result == ""
```

## LLM Prompt

```
Read pr_info/steps/summary.md for full context, then implement pr_info/steps/step_1.md.

Refactor `get_diff_stat()` in `src/mcp_coder/workflow_utils/failure_handling.py`:
1. Replace `_safe_repo_context` + GitPython with `execute_command` from `subprocess_runner`
2. Remove the `_safe_repo_context` import (keep other shim imports)
3. Update both tests in `TestGetDiffStat` class in `tests/workflow_utils/test_failure_handling.py`
4. Run all checks (pylint, mypy, pytest)
```

## Commit message
```
refactor: replace GitPython with subprocess in get_diff_stat (#886)

Replace _safe_repo_context + raw GitPython call with execute_command
subprocess wrapper. This removes the last consumer of _safe_repo_context,
enabling the shim flip in the next step.
```
