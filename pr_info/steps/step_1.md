# Step 1: Re-export Exceptions and Migrate Production Code

## LLM Prompt

```
Read pr_info/steps/summary.md for context, then implement Step 1.

This step adds exception re-exports to subprocess_runner.py and migrates all 
production code to use the subprocess wrapper exclusively.
```

## Overview

Add re-exports for subprocess exception types and migrate production files that either:
1. Use `subprocess.run()` directly
2. Import subprocess only for exception types

---

## Task 1.1: Re-export Exception Classes

### WHERE
`src/mcp_coder/utils/subprocess_runner.py`

### WHAT
Add re-exports at module level:
```python
# Re-export for external use (allows catching without direct subprocess import)
from subprocess import CalledProcessError, SubprocessError, TimeoutExpired

__all__ = [
    "CommandResult",
    "CommandOptions",
    "execute_command",
    "execute_subprocess",
    # Re-exported exceptions
    "CalledProcessError",
    "SubprocessError",
    "TimeoutExpired",
]
```

### HOW
Add imports and `__all__` near top of file, after existing imports.

### DATA
No new data structures. These are standard library exceptions being re-exported.

---

## Task 1.2: Migrate `commits.py`

### WHERE
`src/mcp_coder/utils/git_operations/commits.py`

### WHAT
Replace `get_latest_commit_sha()` implementation:

**Before:**
```python
import subprocess

def get_latest_commit_sha(project_dir: Path) -> Optional[str]:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=project_dir,
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return None
```

**After:**
```python
from mcp_coder.utils.subprocess_runner import execute_command

def get_latest_commit_sha(project_dir: Path) -> Optional[str]:
    result = execute_command(
        ["git", "rev-parse", "HEAD"],
        cwd=str(project_dir),
    )
    if result.return_code == 0:
        return result.stdout.strip()
    return None
```

### HOW
1. Remove `import subprocess`
2. Add import for `execute_command`
3. Replace function body

### ALGORITHM
```
1. Call execute_command with git rev-parse HEAD
2. If return_code == 0, return stripped stdout
3. Otherwise return None
```

### DATA
- Input: `project_dir: Path`
- Output: `Optional[str]` (commit SHA or None)

---

## Task 1.3: Migrate `claude_executable_finder.py`

### WHERE
`src/mcp_coder/llm/providers/claude/claude_executable_finder.py`

### WHAT
Remove fallback `subprocess.run()` calls in `verify_claude_installation()`.

**Current pattern (remove):**
```python
# First try with our complex runner
version_result = execute_command(...)
if version_result.return_code == 0 and version_result.stdout.strip():
    ...
else:
    # If complex runner fails, try simple subprocess as fallback
    try:
        simple_result = subprocess.run(...)  # ← REMOVE THIS
```

**After:**
```python
version_result = execute_command(...)
if version_result.return_code == 0 and version_result.stdout.strip():
    result["version"] = version_result.stdout.strip()
    result["works"] = True
else:
    result["error"] = f"Version check failed: {version_result.stderr or 'No output'}"
```

### HOW
1. Remove `import subprocess` 
2. Remove all `subprocess.run()` fallback blocks
3. Keep only `execute_command()` calls
4. Simplify error handling

### ALGORITHM
```
1. Try execute_command for --version
2. If success (return_code=0 and stdout), set version and works=True
3. If failure, set error message from stderr
4. No fallback attempts
```

---

## Task 1.4: Change Exception Imports (5 files)

### WHERE
- `src/mcp_coder/workflows/implement/task_processing.py`
- `src/mcp_coder/llm/providers/claude/claude_code_api.py`
- `src/mcp_coder/llm/providers/claude/claude_code_cli.py`
- `src/mcp_coder/formatters/black_formatter.py`
- `src/mcp_coder/formatters/isort_formatter.py`

### WHAT
Change import statements:

**Before:**
```python
import subprocess
# ... later in code ...
except subprocess.CalledProcessError:
except subprocess.TimeoutExpired:
```

**After:**
```python
from mcp_coder.utils.subprocess_runner import CalledProcessError, TimeoutExpired
# ... later in code ...
except CalledProcessError:
except TimeoutExpired:
```

### HOW
For each file:
1. Remove `import subprocess`
2. Add import from `subprocess_runner` for needed exceptions
3. Update exception references (remove `subprocess.` prefix)

### Specific imports needed per file:

| File | Exceptions Used |
|------|-----------------|
| `task_processing.py` | `TimeoutExpired` |
| `claude_code_api.py` | `TimeoutExpired`, `CalledProcessError` |
| `claude_code_cli.py` | `TimeoutExpired`, `CalledProcessError` |
| `black_formatter.py` | `CalledProcessError` |
| `isort_formatter.py` | `CalledProcessError` |

---

## Verification

After completing this step:
```bash
# Should find NO subprocess imports in modified files
grep -r "import subprocess" src/mcp_coder/utils/git_operations/commits.py
grep -r "import subprocess" src/mcp_coder/llm/providers/claude/claude_executable_finder.py
grep -r "import subprocess" src/mcp_coder/workflows/implement/task_processing.py
grep -r "import subprocess" src/mcp_coder/formatters/

# Run tests for affected modules
pytest tests/utils/git_operations/test_commits.py -v
pytest tests/llm/providers/claude/ -v
pytest tests/formatters/ -v
```
