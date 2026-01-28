# Step 1: Dependencies and Filesystem Wrapper

## LLM Prompt
```
Read pr_info/steps/summary.md and pr_info/steps/step_1.md.
Implement Step 1: Update pyproject.toml dependencies and create mcp_server_filesystem.py wrapper.
Follow TDD - write tests first, then implementation.
```

## Objective
Set up the foundation: update dependencies and create a thin wrapper for file listing.

---

## Task 1.1: Update pyproject.toml

### WHERE
`pyproject.toml`

### WHAT
Move `mcp-server-filesystem` from optional to main dependencies.

### HOW
```toml
# In [project.dependencies], add:
"mcp-server-filesystem @ git+https://github.com/MarcusJellinghaus/mcp_server_filesystem.git",

# In [project.optional-dependencies].mcp, remove the same line
```

---

## Task 1.2: Create mcp_server_filesystem.py Wrapper

### WHERE
`src/mcp_coder/mcp_server_filesystem.py`

### WHAT
```python
def list_files(directory: str, project_dir: Path, use_gitignore: bool = True) -> list[str]
```

### HOW
- Import from `mcp_server_filesystem.file_tools.directory_utils`
- Thin wrapper that delegates to the library function
- No additional logic needed

### ALGORITHM
```
1. Import list_files from mcp_server_filesystem.file_tools.directory_utils
2. Create wrapper function with same signature
3. Delegate call to imported function
4. Return result unchanged
```

### DATA
- **Input**: directory path (str), project_dir (Path), use_gitignore flag
- **Output**: List of relative file paths (strings)

### IMPLEMENTATION
```python
"""Wrapper for mcp-server-filesystem file listing functionality."""

from pathlib import Path

from mcp_server_filesystem.file_tools.directory_utils import (
    list_files as _list_files,
)


def list_files(
    directory: str, project_dir: Path, use_gitignore: bool = True
) -> list[str]:
    """List all files in directory with optional gitignore filtering.

    Args:
        directory: Directory to list files from
        project_dir: Project root directory
        use_gitignore: Whether to apply .gitignore filtering (default: True)

    Returns:
        List of relative file paths
    """
    return _list_files(directory, project_dir, use_gitignore)
```

---

## Task 1.3: Create Test Package Structure

### WHERE
- `tests/checks/__init__.py`

### WHAT
Empty init file to make tests/checks a package.

### IMPLEMENTATION
```python
"""Tests for mcp_coder.checks package."""
```

---

## Verification Checklist
- [ ] `pyproject.toml` has mcp-server-filesystem in main dependencies
- [ ] `pyproject.toml` no longer has mcp-server-filesystem in optional mcp dependencies
- [ ] `src/mcp_coder/mcp_server_filesystem.py` exists and imports work
- [ ] `tests/checks/__init__.py` exists
- [ ] Run `pip install -e .` to verify dependency resolution
