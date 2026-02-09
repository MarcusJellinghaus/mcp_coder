# Step 1: Add `get_folder_git_status()` Function with Tests

## LLM Prompt
```
Read pr_info/steps/summary.md for context on issue #413.
Implement Step 1: Add the `get_folder_git_status()` function following TDD.
First write the tests, then implement the function.
```

## Overview
Add new function to detect git folder status with proper error handling. Follow TDD - write tests first, then implement.

---

## Part A: Write Tests First

### WHERE
`tests/workflows/vscodeclaude/test_status.py`

### WHAT
Add new test class `TestGetFolderGitStatus` with test methods:

```python
class TestGetFolderGitStatus:
    def test_returns_missing_when_folder_not_exists(self, tmp_path: Path) -> None: ...
    def test_returns_no_git_when_not_a_repo(self, tmp_path: Path, monkeypatch) -> None: ...
    def test_returns_clean_when_no_changes(self, tmp_path: Path, monkeypatch) -> None: ...
    def test_returns_dirty_when_has_changes(self, tmp_path: Path, monkeypatch) -> None: ...
    def test_returns_error_when_git_status_fails(self, tmp_path: Path, monkeypatch) -> None: ...
```

### HOW
- Import `get_folder_git_status` from `mcp_coder.workflows.vscodeclaude.status`
- Use `monkeypatch` to mock `execute_subprocess` for controlled testing
- Use `tmp_path` fixture for temporary directories

### TEST PSEUDOCODE
```python
# test_returns_missing_when_folder_not_exists
non_existent = tmp_path / "does_not_exist"
result = get_folder_git_status(non_existent)
assert result == "Missing"

# test_returns_no_git_when_not_a_repo
folder = tmp_path / "not_a_repo"
folder.mkdir()
mock execute_subprocess to raise CalledProcessError for git rev-parse
result = get_folder_git_status(folder)
assert result == "No Git"

# test_returns_clean_when_no_changes
mock execute_subprocess: git rev-parse succeeds, git status returns ""
result = get_folder_git_status(tmp_path)
assert result == "Clean"

# test_returns_dirty_when_has_changes
mock execute_subprocess: git rev-parse succeeds, git status returns "M file.py"
result = get_folder_git_status(tmp_path)
assert result == "Dirty"

# test_returns_error_when_git_status_fails
mock execute_subprocess: git rev-parse succeeds, git status raises exception
result = get_folder_git_status(tmp_path)
assert result == "Error"
```

---

## Part B: Implement Function

### WHERE
`src/mcp_coder/workflows/vscodeclaude/status.py`

### WHAT
```python
def get_folder_git_status(folder_path: Path) -> str:
    """Get git working directory status for display.
    
    Args:
        folder_path: Path to check
        
    Returns:
        One of: "Clean", "Dirty", "Missing", "No Git", "Error"
    """
```

### ALGORITHM
```python
def get_folder_git_status(folder_path: Path) -> str:
    if not folder_path.exists():
        return "Missing"
    
    options = CommandOptions(cwd=str(folder_path))
    
    # Check if git repo
    try:
        execute_subprocess(["git", "rev-parse", "--git-dir"], 
                          CommandOptions(cwd=str(folder_path), check=True))
    except Exception:
        return "No Git"
    
    # Check for changes
    try:
        result = execute_subprocess(["git", "status", "--porcelain"],
                                   CommandOptions(cwd=str(folder_path), check=True))
        return "Dirty" if result.stdout.strip() else "Clean"
    except Exception:
        return "Error"
```

### DATA
- **Input**: `folder_path: Path` - path to folder to check
- **Output**: `str` - one of `"Clean"`, `"Dirty"`, `"Missing"`, `"No Git"`, `"Error"`

---

## Part C: Export Function

### WHERE
`src/mcp_coder/workflows/vscodeclaude/__init__.py`

### WHAT
Add to imports and `__all__`:
```python
from .status import (
    check_folder_dirty,
    get_folder_git_status,  # Add this
    ...
)

__all__ = [
    ...
    "get_folder_git_status",  # Add this
    ...
]
```

---

## Verification
Run tests:
```bash
pytest tests/workflows/vscodeclaude/test_status.py::TestGetFolderGitStatus -v
```
